# Financial Reconciliation Engine - Sample Datasets

This directory contains sample financial data for testing the Financial Reconciliation Engine's capabilities.

## 📊 Dataset Overview

### Transactions Dataset (`transactions.csv`)
- **30 transaction records** spanning January-February 2024
- **5 account IDs** (ACC1001 through ACC1005) 
- **Realistic amounts** ranging from $45.90 to $1,500,000
- **Diverse counterparties** representing various business entities

### General Ledger Dataset (`general_ledger.csv`)
- **30 general ledger entries** with corresponding timeframe
- **8 account IDs** (ACC1001 through ACC1008)
- **Debit/Credit structure** following standard accounting practices
- **Strategic mismatches** for reconciliation testing

## 🎯 Testing Scenarios Included

### 1. **Perfect Matches** ✅
- TXN001 ↔ GL001: $1,500.00 on 2024-01-15 (ACC1001)
- TXN002 ↔ GL002: $2,350.75 on 2024-01-15 (ACC1002)
- TXN007 ↔ GL007: $4,500.00 on 2024-01-18 (ACC1001)

### 2. **Amount Mismatches** ⚠️
- TXN004 ($750.50) vs GL004 ($800.50): $50 difference
- These will be flagged as "amount_mismatch" with discrepancy details

### 3. **Missing Records** ❌
- **Missing GL Entries**: TXN011, TXN019, TXN029 (no corresponding GL)
- **Missing Transactions**: GL028, GL029, GL030 (no corresponding transactions)

### 4. **Anomaly Detection Targets** 🚨
- **TXN003**: $950,000 (statistical outlier)
- **TXN011**: $500,000 (suspicious large transfer)
- **TXN019**: $750,000 (unusual wire transfer)
- **TXN029**: $1,500,000 (highly suspicious transfer)

### 5. **Data Quality Issues** 📋
- **Duplicate potential**: Similar amounts and dates for testing
- **Completeness**: All required fields populated
- **Consistency**: Proper date formats and positive amounts

## 🔄 Expected Reconciliation Results

When you run the reconciliation engine with this data:

- **Matched Transactions**: ~20-22 records
- **Amount Mismatches**: 2-3 records  
- **Missing GL Entries**: 3-4 records
- **Missing Transactions**: 3 records
- **Reconciliation Accuracy**: ~75-80%

## 🚨 Expected Anomaly Detection

The ML and statistical models should detect:

- **Statistical Anomalies**: 4 high-value transactions (Z-score > 3)
- **IQR Outliers**: Large transactions outside normal range
- **ML Anomalies**: Isolation Forest and One-Class SVM detections

## 💡 Usage Instructions

1. **Upload Transactions**: Use `transactions.csv` in the Upload Data tab
2. **Upload General Ledger**: Use `general_ledger.csv` in the Upload Data tab
3. **Run Reconciliation**: Click "Run Reconciliation" to match records
4. **Detect Anomalies**: Click "Detect Anomalies" to find outliers
5. **Review Results**: Check Dashboard, Reconciliation, and Anomalies tabs
6. **Export Report**: Generate CSV report of reconciliation results

## 🎨 Account Mapping

- **ACC1001**: Primary business account (high volume)
- **ACC1002**: Secondary operations account  
- **ACC1003**: Project-specific account
- **ACC1004**: Utilities and services account
- **ACC1005**: Software and subscriptions account
- **ACC1006-1008**: Additional GL-only accounts (for missing transaction testing)

This dataset provides comprehensive testing scenarios for all reconciliation engine features while maintaining realistic financial data patterns.