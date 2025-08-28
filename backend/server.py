from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import pandas as pd
import numpy as np
import aiofiles
import json
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler
from scipy import stats
import io

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Pydantic Models
class Transaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    txn_id: str
    date: str
    amount: float
    account_id: str
    counterparty: str

class GeneralLedgerEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    gl_id: str
    date: str
    debit_amount: float
    credit_amount: float
    account_id: str

class ReconciliationResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: str  # "matched", "missing_transaction", "missing_gl", "amount_mismatch"
    transaction_id: Optional[str] = None
    gl_id: Optional[str] = None
    account_id: str
    date: str
    amount_difference: Optional[float] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AnomalyResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transaction_id: str
    anomaly_type: str  # "statistical", "ml_isolation_forest", "ml_one_class_svm"
    anomaly_score: float
    is_anomaly: bool
    detection_method: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DataQualityReport(BaseModel):
    dataset_name: str
    total_records: int
    completeness_score: float
    consistency_score: float
    duplicate_count: int
    quality_score: float
    issues: List[str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DashboardStats(BaseModel):
    total_transactions: int
    total_gl_entries: int
    matched_count: int
    unmatched_count: int
    anomalies_detected: int
    data_quality_score: float
    reconciliation_accuracy: float

# Helper functions for data processing
def prepare_for_mongo(data):
    """Convert datetime objects to ISO strings for MongoDB storage"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
    return data

def parse_from_mongo(item):
    """Parse datetime strings back from MongoDB"""
    if isinstance(item.get('created_at'), str):
        try:
            item['created_at'] = datetime.fromisoformat(item['created_at'])
        except:
            pass
    return item

# Data Quality Functions
def calculate_data_quality(df: pd.DataFrame, dataset_name: str) -> DataQualityReport:
    """Calculate comprehensive data quality metrics"""
    total_records = len(df)
    
    # Completeness: percentage of non-null values
    completeness_score = (df.count().sum() / (df.shape[0] * df.shape[1])) * 100
    
    # Consistency: check for data type consistency
    consistency_issues = []
    consistency_score = 100.0
    
    # Check for duplicates
    duplicate_count = df.duplicated().sum()
    
    # Check for negative amounts in financial data
    if 'amount' in df.columns:
        negative_amounts = (df['amount'] < 0).sum()
        if negative_amounts > 0:
            consistency_issues.append(f"{negative_amounts} negative amounts found")
            consistency_score -= 10
    
    # Check date format consistency
    if 'date' in df.columns:
        try:
            pd.to_datetime(df['date'])
        except:
            consistency_issues.append("Inconsistent date formats")
            consistency_score -= 15
    
    # Overall quality score
    quality_score = (completeness_score + consistency_score) / 2
    
    return DataQualityReport(
        dataset_name=dataset_name,
        total_records=total_records,
        completeness_score=round(completeness_score, 2),
        consistency_score=round(consistency_score, 2),
        duplicate_count=duplicate_count,
        quality_score=round(quality_score, 2),
        issues=consistency_issues
    )

# Reconciliation Engine
async def reconcile_transactions():
    """Core reconciliation logic - match transactions with GL entries"""
    transactions = await db.transactions.find().to_list(length=None)
    gl_entries = await db.general_ledger.find().to_list(length=None)
    
    # Clear previous reconciliation results
    await db.reconciliation_results.delete_many({})
    
    results = []
    matched_gl_ids = set()
    
    for txn in transactions:
        matched = False
        
        for gl in gl_entries:
            if (gl['account_id'] == txn['account_id'] and 
                gl['date'] == txn['date'] and
                gl['_id'] not in matched_gl_ids):
                
                # Check if amounts match (considering debit/credit)
                gl_amount = gl['debit_amount'] - gl['credit_amount']
                if abs(gl_amount - txn['amount']) < 0.01:  # Allow for small rounding differences
                    # Perfect match
                    result = ReconciliationResult(
                        status="matched",
                        transaction_id=txn['txn_id'],
                        gl_id=gl['gl_id'],
                        account_id=txn['account_id'],
                        date=txn['date'],
                        amount_difference=0.0
                    )
                    matched_gl_ids.add(gl['_id'])
                    matched = True
                    break
                elif abs(gl_amount - txn['amount']) < 100:  # Amount mismatch but close
                    result = ReconciliationResult(
                        status="amount_mismatch",
                        transaction_id=txn['txn_id'],
                        gl_id=gl['gl_id'],
                        account_id=txn['account_id'],
                        date=txn['date'],
                        amount_difference=gl_amount - txn['amount']
                    )
                    matched_gl_ids.add(gl['_id'])
                    matched = True
                    break
        
        if not matched:
            # Transaction without matching GL entry
            result = ReconciliationResult(
                status="missing_gl",
                transaction_id=txn['txn_id'],
                account_id=txn['account_id'],
                date=txn['date']
            )
        
        results.append(result)
    
    # Check for GL entries without matching transactions
    for gl in gl_entries:
        if gl['_id'] not in matched_gl_ids:
            result = ReconciliationResult(
                status="missing_transaction",
                gl_id=gl['gl_id'],
                account_id=gl['account_id'],
                date=gl['date']
            )
            results.append(result)
    
    # Store results in database
    for result in results:
        result_dict = prepare_for_mongo(result.dict())
        await db.reconciliation_results.insert_one(result_dict)
    
    return len(results)

# Anomaly Detection Functions
async def detect_anomalies_statistical():
    """Statistical anomaly detection using Z-score and IQR"""
    transactions = await db.transactions.find().to_list(length=None)
    df = pd.DataFrame(transactions)
    
    if len(df) < 5:
        return []
    
    anomalies = []
    
    # Z-score method
    z_scores = np.abs(stats.zscore(df['amount']))
    z_anomalies = df[z_scores > 3]
    
    for _, txn in z_anomalies.iterrows():
        anomaly = AnomalyResult(
            transaction_id=txn['txn_id'],
            anomaly_type="statistical",
            anomaly_score=float(z_scores[txn.name]),
            is_anomaly=True,
            detection_method="z_score"
        )
        anomalies.append(anomaly)
    
    # IQR method
    Q1 = df['amount'].quantile(0.25)
    Q3 = df['amount'].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    iqr_anomalies = df[(df['amount'] < lower_bound) | (df['amount'] > upper_bound)]
    
    for _, txn in iqr_anomalies.iterrows():
        # Avoid duplicates
        if txn['txn_id'] not in [a.transaction_id for a in anomalies]:
            anomaly = AnomalyResult(
                transaction_id=txn['txn_id'],
                anomaly_type="statistical",
                anomaly_score=float(abs(txn['amount'] - df['amount'].median())),
                is_anomaly=True,
                detection_method="iqr"
            )
            anomalies.append(anomaly)
    
    return anomalies

async def detect_anomalies_ml():
    """ML-based anomaly detection using Isolation Forest and One-Class SVM"""
    transactions = await db.transactions.find().to_list(length=None)
    df = pd.DataFrame(transactions)
    
    if len(df) < 10:
        return []
    
    anomalies = []
    
    # Prepare features for ML models
    features = df[['amount']].copy()
    
    # Add day of week and hour features if we have datetime
    try:
        df['datetime'] = pd.to_datetime(df['date'])
        features['day_of_week'] = df['datetime'].dt.dayofweek
        features['hour'] = df['datetime'].dt.hour
    except:
        features['day_of_week'] = 0
        features['hour'] = 12
    
    # Standardize features
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    # Isolation Forest
    iso_forest = IsolationForest(contamination=0.1, random_state=42)
    iso_predictions = iso_forest.fit_predict(features_scaled)
    iso_scores = iso_forest.decision_function(features_scaled)
    
    for idx, (prediction, score) in enumerate(zip(iso_predictions, iso_scores)):
        if prediction == -1:  # Anomaly
            txn = df.iloc[idx]
            anomaly = AnomalyResult(
                transaction_id=txn['txn_id'],
                anomaly_type="ml_isolation_forest",
                anomaly_score=float(abs(score)),
                is_anomaly=True,
                detection_method="isolation_forest"
            )
            anomalies.append(anomaly)
    
    # One-Class SVM
    svm_model = OneClassSVM(gamma='scale', nu=0.1)
    svm_predictions = svm_model.fit_predict(features_scaled)
    svm_scores = svm_model.decision_function(features_scaled)
    
    for idx, (prediction, score) in enumerate(zip(svm_predictions, svm_scores)):
        if prediction == -1:  # Anomaly
            txn = df.iloc[idx]
            # Avoid duplicates
            if txn['txn_id'] not in [a.transaction_id for a in anomalies]:
                anomaly = AnomalyResult(
                    transaction_id=txn['txn_id'],
                    anomaly_type="ml_one_class_svm",
                    anomaly_score=float(abs(score)),
                    is_anomaly=True,
                    detection_method="one_class_svm"
                )
                anomalies.append(anomaly)
    
    return anomalies

# API Routes
@api_router.post("/upload/transactions")
async def upload_transactions(file: UploadFile = File(...)):
    """Upload transactions CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Validate required columns
        required_columns = ['txn_id', 'date', 'amount', 'account_id', 'counterparty']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(status_code=400, detail=f"CSV must contain columns: {required_columns}")
        
        # Clear existing transactions
        await db.transactions.delete_many({})
        
        # Process and insert transactions
        transactions = []
        for _, row in df.iterrows():
            transaction = Transaction(
                txn_id=str(row['txn_id']),
                date=str(row['date']),
                amount=float(row['amount']),
                account_id=str(row['account_id']),
                counterparty=str(row['counterparty'])
            )
            transactions.append(transaction.dict())
        
        await db.transactions.insert_many(transactions)
        
        # Calculate data quality
        quality_report = calculate_data_quality(df, "transactions")
        quality_dict = prepare_for_mongo(quality_report.dict())
        await db.data_quality.replace_one(
            {"dataset_name": "transactions"}, 
            quality_dict, 
            upsert=True
        )
        
        return {
            "message": f"Successfully uploaded {len(transactions)} transactions",
            "data_quality": quality_report
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

@api_router.post("/upload/general-ledger")
async def upload_general_ledger(file: UploadFile = File(...)):
    """Upload general ledger CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Validate required columns
        required_columns = ['gl_id', 'date', 'debit_amount', 'credit_amount', 'account_id']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(status_code=400, detail=f"CSV must contain columns: {required_columns}")
        
        # Clear existing GL entries
        await db.general_ledger.delete_many({})
        
        # Process and insert GL entries
        gl_entries = []
        for _, row in df.iterrows():
            gl_entry = GeneralLedgerEntry(
                gl_id=str(row['gl_id']),
                date=str(row['date']),
                debit_amount=float(row['debit_amount']),
                credit_amount=float(row['credit_amount']),
                account_id=str(row['account_id'])
            )
            gl_entries.append(gl_entry.dict())
        
        await db.general_ledger.insert_many(gl_entries)
        
        # Calculate data quality
        quality_report = calculate_data_quality(df, "general_ledger")
        quality_dict = prepare_for_mongo(quality_report.dict())
        await db.data_quality.replace_one(
            {"dataset_name": "general_ledger"}, 
            quality_dict, 
            upsert=True
        )
        
        return {
            "message": f"Successfully uploaded {len(gl_entries)} general ledger entries",
            "data_quality": quality_report
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

@api_router.post("/reconcile")
async def run_reconciliation():
    """Run the reconciliation process"""
    try:
        result_count = await reconcile_transactions()
        return {
            "message": f"Reconciliation completed. Generated {result_count} results.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reconciliation failed: {str(e)}")

@api_router.post("/detect-anomalies")
async def run_anomaly_detection():
    """Run both statistical and ML-based anomaly detection"""
    try:
        # Clear existing anomalies
        await db.anomalies.delete_many({})
        
        # Run statistical detection
        statistical_anomalies = await detect_anomalies_statistical()
        
        # Run ML detection
        ml_anomalies = await detect_anomalies_ml()
        
        # Combine and store all anomalies
        all_anomalies = statistical_anomalies + ml_anomalies
        if all_anomalies:
            anomaly_dicts = [prepare_for_mongo(anomaly.dict()) for anomaly in all_anomalies]
            await db.anomalies.insert_many(anomaly_dicts)
        
        return {
            "message": f"Anomaly detection completed. Found {len(all_anomalies)} anomalies.",
            "statistical_anomalies": len(statistical_anomalies),
            "ml_anomalies": len(ml_anomalies),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anomaly detection failed: {str(e)}")

@api_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Get comprehensive dashboard statistics"""
    try:
        # Count totals
        total_transactions = await db.transactions.count_documents({})
        total_gl_entries = await db.general_ledger.count_documents({})
        
        # Reconciliation stats
        matched_count = await db.reconciliation_results.count_documents({"status": "matched"})
        unmatched_count = await db.reconciliation_results.count_documents({
            "status": {"$in": ["missing_gl", "missing_transaction", "amount_mismatch"]}
        })
        
        # Anomaly count
        anomalies_detected = await db.anomalies.count_documents({})
        
        # Data quality score (average of both datasets)
        quality_docs = await db.data_quality.find().to_list(length=None)
        data_quality_score = sum(doc.get('quality_score', 0) for doc in quality_docs) / max(len(quality_docs), 1)
        
        # Reconciliation accuracy
        total_reconciled = matched_count + unmatched_count
        reconciliation_accuracy = (matched_count / max(total_reconciled, 1)) * 100
        
        return DashboardStats(
            total_transactions=total_transactions,
            total_gl_entries=total_gl_entries,
            matched_count=matched_count,
            unmatched_count=unmatched_count,
            anomalies_detected=anomalies_detected,
            data_quality_score=round(data_quality_score, 2),
            reconciliation_accuracy=round(reconciliation_accuracy, 2)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")

@api_router.get("/reconciliation/results")
async def get_reconciliation_results(status: Optional[str] = None, account_id: Optional[str] = None):
    """Get reconciliation results with optional filtering"""
    try:
        filter_dict = {}
        if status:
            filter_dict["status"] = status
        if account_id:
            filter_dict["account_id"] = account_id
        
        results = await db.reconciliation_results.find(filter_dict).to_list(length=None)
        return [parse_from_mongo(result) for result in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get reconciliation results: {str(e)}")

@api_router.get("/anomalies")
async def get_anomalies(detection_method: Optional[str] = None):
    """Get detected anomalies with optional filtering"""
    try:
        filter_dict = {}
        if detection_method:
            filter_dict["detection_method"] = detection_method
        
        anomalies = await db.anomalies.find(filter_dict).to_list(length=None)
        return [parse_from_mongo(anomaly) for anomaly in anomalies]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get anomalies: {str(e)}")

@api_router.get("/data-quality")
async def get_data_quality():
    """Get data quality reports for both datasets"""
    try:
        quality_reports = await db.data_quality.find().to_list(length=None)
        return [parse_from_mongo(report) for report in quality_reports]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get data quality reports: {str(e)}")

@api_router.get("/export/reconciliation")
async def export_reconciliation_report():
    """Export reconciliation results as CSV"""
    try:
        results = await db.reconciliation_results.find().to_list(length=None)
        df = pd.DataFrame(results)
        
        # Create CSV in memory
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()
        
        # Save to temporary file
        temp_file = f"/tmp/reconciliation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(temp_file, 'w') as f:
            f.write(csv_content)
        
        return FileResponse(
            temp_file,
            media_type='text/csv',
            filename=f"reconciliation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export reconciliation report: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()