import requests
import sys
import io
from datetime import datetime
import json

class FinancialReconciliationTester:
    def __init__(self, base_url="https://finrecon-engine.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, headers=headers)
                elif data:
                    headers['Content-Type'] = 'application/json'
                    response = requests.post(url, json=data, headers=headers)
                else:
                    response = requests.post(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and 'message' in response_data:
                        print(f"   Message: {response_data['message']}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response: {response.text[:200]}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def create_sample_transactions_csv(self):
        """Create sample transactions CSV content"""
        csv_content = """txn_id,date,amount,account_id,counterparty
TXN001,2024-01-15,1500.00,ACC123,Customer A
TXN002,2024-01-15,2300.00,ACC124,Customer B
TXN003,2024-01-16,50000.00,ACC123,Large Corp
TXN004,2024-01-16,750.00,ACC125,Customer C
TXN005,2024-01-17,1200.00,ACC123,Customer D"""
        return csv_content

    def create_sample_gl_csv(self):
        """Create sample general ledger CSV content"""
        csv_content = """gl_id,date,debit_amount,credit_amount,account_id
GL001,2024-01-15,1500.00,0.00,ACC123
GL002,2024-01-15,2300.00,0.00,ACC124
GL003,2024-01-16,800.00,0.00,ACC125
GL004,2024-01-17,1200.00,0.00,ACC123"""
        return csv_content

    def test_file_upload(self, csv_content, endpoint, file_name, description):
        """Test file upload endpoints"""
        files = {
            'file': (file_name, io.StringIO(csv_content), 'text/csv')
        }
        success, response = self.run_test(
            f"Upload {description}",
            "POST",
            f"upload/{endpoint}",
            200,
            files=files
        )
        return success, response

    def test_dashboard_stats(self):
        """Test dashboard statistics endpoint"""
        success, response = self.run_test(
            "Dashboard Statistics",
            "GET",
            "dashboard/stats",
            200
        )
        if success and response:
            print(f"   📊 Total Transactions: {response.get('total_transactions', 0)}")
            print(f"   📊 Total GL Entries: {response.get('total_gl_entries', 0)}")
            print(f"   📊 Matched Count: {response.get('matched_count', 0)}")
            print(f"   📊 Data Quality Score: {response.get('data_quality_score', 0)}%")
        return success, response

    def test_reconciliation_process(self):
        """Test reconciliation process"""
        success, response = self.run_test(
            "Run Reconciliation",
            "POST",
            "reconcile",
            200
        )
        return success, response

    def test_anomaly_detection(self):
        """Test anomaly detection process"""
        success, response = self.run_test(
            "Run Anomaly Detection",
            "POST",
            "detect-anomalies",
            200
        )
        if success and response:
            print(f"   🚨 Statistical Anomalies: {response.get('statistical_anomalies', 0)}")
            print(f"   🚨 ML Anomalies: {response.get('ml_anomalies', 0)}")
        return success, response

    def test_reconciliation_results(self):
        """Test reconciliation results endpoint"""
        success, response = self.run_test(
            "Get Reconciliation Results",
            "GET",
            "reconciliation/results",
            200
        )
        if success and response:
            print(f"   📋 Total Results: {len(response)}")
            if response:
                statuses = {}
                for result in response:
                    status = result.get('status', 'unknown')
                    statuses[status] = statuses.get(status, 0) + 1
                for status, count in statuses.items():
                    print(f"   📋 {status}: {count}")
        return success, response

    def test_anomalies_results(self):
        """Test anomalies results endpoint"""
        success, response = self.run_test(
            "Get Anomalies Results",
            "GET",
            "anomalies",
            200
        )
        if success and response:
            print(f"   🚨 Total Anomalies: {len(response)}")
            if response:
                methods = {}
                for anomaly in response:
                    method = anomaly.get('detection_method', 'unknown')
                    methods[method] = methods.get(method, 0) + 1
                for method, count in methods.items():
                    print(f"   🚨 {method}: {count}")
        return success, response

    def test_data_quality(self):
        """Test data quality endpoint"""
        success, response = self.run_test(
            "Get Data Quality Reports",
            "GET",
            "data-quality",
            200
        )
        if success and response:
            print(f"   📊 Quality Reports: {len(response)}")
            for report in response:
                dataset = report.get('dataset_name', 'unknown')
                score = report.get('quality_score', 0)
                records = report.get('total_records', 0)
                print(f"   📊 {dataset}: {score}% quality, {records} records")
        return success, response

    def test_export_functionality(self):
        """Test CSV export functionality"""
        success, response = self.run_test(
            "Export Reconciliation Report",
            "GET",
            "export/reconciliation",
            200
        )
        return success, response

def main():
    print("🏦 Financial Reconciliation Engine - Backend API Testing")
    print("=" * 60)
    
    tester = FinancialReconciliationTester()
    
    # Test 1: Upload sample transactions
    print("\n📤 PHASE 1: FILE UPLOAD TESTING")
    transactions_csv = tester.create_sample_transactions_csv()
    success1, _ = tester.test_file_upload(
        transactions_csv, 
        "transactions", 
        "sample_transactions.csv", 
        "Transactions CSV"
    )
    
    # Test 2: Upload sample general ledger
    gl_csv = tester.create_sample_gl_csv()
    success2, _ = tester.test_file_upload(
        gl_csv, 
        "general-ledger", 
        "sample_gl.csv", 
        "General Ledger CSV"
    )
    
    if not (success1 and success2):
        print("\n❌ File upload failed. Cannot proceed with further testing.")
        return 1
    
    # Test 3: Dashboard stats (should show uploaded data)
    print("\n📊 PHASE 2: DASHBOARD TESTING")
    tester.test_dashboard_stats()
    
    # Test 4: Run reconciliation
    print("\n🔄 PHASE 3: RECONCILIATION TESTING")
    success3, _ = tester.test_reconciliation_process()
    
    # Test 5: Run anomaly detection
    print("\n🚨 PHASE 4: ANOMALY DETECTION TESTING")
    success4, _ = tester.test_anomaly_detection()
    
    # Test 6: Get reconciliation results
    print("\n📋 PHASE 5: RESULTS RETRIEVAL TESTING")
    tester.test_reconciliation_results()
    
    # Test 7: Get anomaly results
    tester.test_anomalies_results()
    
    # Test 8: Get data quality reports
    tester.test_data_quality()
    
    # Test 9: Export functionality
    print("\n📥 PHASE 6: EXPORT TESTING")
    tester.test_export_functionality()
    
    # Test 10: Updated dashboard stats
    print("\n📊 PHASE 7: FINAL DASHBOARD CHECK")
    tester.test_dashboard_stats()
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 FINAL RESULTS: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All backend API tests passed successfully!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())