import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Badge } from "./components/ui/badge";
import { Progress } from "./components/ui/progress";
import { Alert, AlertDescription } from "./components/ui/alert";
import { Separator } from "./components/ui/separator";
import { 
  Upload, 
  BarChart3, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle, 
  Activity, 
  FileText,
  Download,
  RefreshCw,
  TrendingUp,
  Database,
  Shield
} from "lucide-react";
import { Toaster } from "./components/ui/sonner";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [dashboardStats, setDashboardStats] = useState({
    total_transactions: 0,
    total_gl_entries: 0,
    matched_count: 0,
    unmatched_count: 0,
    anomalies_detected: 0,
    data_quality_score: 0,
    reconciliation_accuracy: 0
  });
  const [reconciliationResults, setReconciliationResults] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [dataQuality, setDataQuality] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("dashboard");

  // Fetch dashboard data
  const fetchDashboardData = async () => {
    try {
      const [statsRes, reconciliationRes, anomaliesRes, qualityRes] = await Promise.all([
        axios.get(`${API}/dashboard/stats`),
        axios.get(`${API}/reconciliation/results`),
        axios.get(`${API}/anomalies`),
        axios.get(`${API}/data-quality`)
      ]);
      
      setDashboardStats(statsRes.data);
      setReconciliationResults(reconciliationRes.data);
      setAnomalies(anomaliesRes.data);
      setDataQuality(qualityRes.data);
    } catch (error) {
      console.error("Error fetching dashboard data:", error);
      toast.error("Failed to fetch dashboard data");
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // File upload handlers
  const handleFileUpload = async (file, endpoint, type) => {
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API}/upload/${endpoint}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast.success(`${type} uploaded successfully!`);
      fetchDashboardData();
    } catch (error) {
      console.error(`Error uploading ${type}:`, error);
      toast.error(`Failed to upload ${type}: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Run reconciliation
  const runReconciliation = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/reconcile`);
      toast.success("Reconciliation completed successfully!");
      fetchDashboardData();
    } catch (error) {
      console.error("Error running reconciliation:", error);
      toast.error("Failed to run reconciliation");
    } finally {
      setLoading(false);
    }
  };

  // Run anomaly detection
  const runAnomalyDetection = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/detect-anomalies`);
      toast.success("Anomaly detection completed!");
      fetchDashboardData();
    } catch (error) {
      console.error("Error running anomaly detection:", error);
      toast.error("Failed to run anomaly detection");
    } finally {
      setLoading(false);
    }
  };

  // Export reconciliation report
  const exportReport = async () => {
    try {
      const response = await axios.get(`${API}/export/reconciliation`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `reconciliation_report_${new Date().getTime()}.csv`);
      document.body.appendChild(link);
      link.click();
      toast.success("Report exported successfully!");
    } catch (error) {
      console.error("Error exporting report:", error);
      toast.error("Failed to export report");
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'matched': return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'missing_gl': return 'bg-red-100 text-red-800 border-red-200';
      case 'missing_transaction': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'amount_mismatch': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default: return 'bg-slate-100 text-slate-800 border-slate-200';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/40">
      <div className="container mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-700 mb-4 shadow-lg">
            <BarChart3 className="h-8 w-8 text-white" />
          </div>
          <div className="space-y-2">
            <h1 className="text-4xl font-bold bg-gradient-to-r from-slate-800 via-blue-700 to-indigo-700 bg-clip-text text-transparent">
              Financial Reconciliation Engine
            </h1>
            <p className="text-slate-600 text-lg max-w-2xl mx-auto">
              Intelligent data quality monitoring, transaction reconciliation, and AI-driven anomaly detection for financial operations
            </p>
          </div>
        </div>

        {/* Main Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4 mb-8 bg-white/70 backdrop-blur-sm border shadow-sm">
            <TabsTrigger value="dashboard" className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Dashboard
            </TabsTrigger>
            <TabsTrigger value="upload" className="flex items-center gap-2">
              <Upload className="h-4 w-4" />
              Upload Data
            </TabsTrigger>
            <TabsTrigger value="reconciliation" className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" />
              Reconciliation
            </TabsTrigger>
            <TabsTrigger value="anomalies" className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              Anomalies
            </TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            {/* Key Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-slate-600">Total Transactions</CardTitle>
                  <Database className="h-5 w-5 text-blue-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-slate-900">{dashboardStats.total_transactions.toLocaleString()}</div>
                </CardContent>
              </Card>

              <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-slate-600">GL Entries</CardTitle>
                  <FileText className="h-5 w-5 text-indigo-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-slate-900">{dashboardStats.total_gl_entries.toLocaleString()}</div>
                </CardContent>
              </Card>

              <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-slate-600">Reconciliation Accuracy</CardTitle>
                  <TrendingUp className="h-5 w-5 text-emerald-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-slate-900">{dashboardStats.reconciliation_accuracy}%</div>
                  <Progress value={dashboardStats.reconciliation_accuracy} className="mt-2" />
                </CardContent>
              </Card>

              <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-slate-600">Data Quality Score</CardTitle>
                  <Shield className="h-5 w-5 text-purple-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-slate-900">{dashboardStats.data_quality_score}%</div>
                  <Progress value={dashboardStats.data_quality_score} className="mt-2" />
                </CardContent>
              </Card>
            </div>

            {/* Main Dashboard Content */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Reconciliation Summary */}
              <Card className="lg:col-span-2 bg-white/80 backdrop-blur-sm border-0 shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                    Reconciliation Overview
                  </CardTitle>
                  <CardDescription>Transaction matching and discrepancy analysis</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-slate-600">Matched</span>
                        <span className="font-semibold text-emerald-700">{dashboardStats.matched_count}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-slate-600">Unmatched</span>
                        <span className="font-semibold text-red-700">{dashboardStats.unmatched_count}</span>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-slate-600">Anomalies</span>
                        <span className="font-semibold text-orange-700">{dashboardStats.anomalies_detected}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="pt-4">
                    <img 
                      src="https://images.unsplash.com/photo-1551288049-bebda4e38f71" 
                      alt="Financial Analytics Dashboard" 
                      className="w-full h-48 object-cover rounded-lg shadow-sm"
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Data Quality Summary */}
              <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="h-5 w-5 text-purple-600" />
                    Data Quality
                  </CardTitle>
                  <CardDescription>Dataset health and integrity metrics</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {dataQuality.map((quality, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium capitalize">{quality.dataset_name}</span>
                        <Badge variant="outline" className="text-xs">
                          {quality.quality_score}%
                        </Badge>
                      </div>
                      <Progress value={quality.quality_score} className="h-2" />
                      <div className="text-xs text-slate-500">
                        {quality.total_records} records, {quality.duplicate_count} duplicates
                      </div>
                    </div>
                  ))}
                  
                  <div className="pt-2">
                    <img 
                      src="https://images.unsplash.com/photo-1526628953301-3e589a6a8b74" 
                      alt="Data Quality Monitoring" 
                      className="w-full h-32 object-cover rounded-lg shadow-sm"
                    />
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Upload Tab */}
          <TabsContent value="upload" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Transactions Upload */}
              <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Database className="h-5 w-5 text-blue-600" />
                    Upload Transactions
                  </CardTitle>
                  <CardDescription>
                    CSV file with columns: txn_id, date, amount, account_id, counterparty
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="border-2 border-dashed border-slate-200 rounded-lg p-8 text-center space-y-4">
                    <Upload className="h-12 w-12 text-slate-400 mx-auto" />
                    <div className="space-y-2">
                      <p className="text-sm text-slate-600">Drop your transactions CSV file here or click to browse</p>
                      <input
                        type="file"
                        accept=".csv"
                        className="hidden"
                        id="transactions-upload"
                        onChange={(e) => {
                          const file = e.target.files[0];
                          if (file) handleFileUpload(file, 'transactions', 'Transactions');
                        }}
                      />
                      <label htmlFor="transactions-upload">
                        <Button variant="outline" className="cursor-pointer">
                          Choose File
                        </Button>
                      </label>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* General Ledger Upload */}
              <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="h-5 w-5 text-indigo-600" />
                    Upload General Ledger
                  </CardTitle>
                  <CardDescription>
                    CSV file with columns: gl_id, date, debit_amount, credit_amount, account_id
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="border-2 border-dashed border-slate-200 rounded-lg p-8 text-center space-y-4">
                    <Upload className="h-12 w-12 text-slate-400 mx-auto" />
                    <div className="space-y-2">
                      <p className="text-sm text-slate-600">Drop your general ledger CSV file here or click to browse</p>
                      <input
                        type="file"
                        accept=".csv"
                        className="hidden"
                        id="gl-upload"
                        onChange={(e) => {
                          const file = e.target.files[0];
                          if (file) handleFileUpload(file, 'general-ledger', 'General Ledger');
                        }}
                      />
                      <label htmlFor="gl-upload">
                        <Button variant="outline" className="cursor-pointer">
                          Choose File
                        </Button>
                      </label>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-4 justify-center">
              <Button 
                onClick={runReconciliation} 
                disabled={loading}
                className="bg-gradient-to-r from-emerald-600 to-green-600 hover:from-emerald-700 hover:to-green-700 text-white shadow-lg"
              >
                {loading ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <CheckCircle2 className="h-4 w-4 mr-2" />}
                Run Reconciliation
              </Button>
              <Button 
                onClick={runAnomalyDetection} 
                disabled={loading}
                className="bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700 text-white shadow-lg"
              >
                {loading ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <AlertTriangle className="h-4 w-4 mr-2" />}
                Detect Anomalies
              </Button>
              <Button 
                onClick={exportReport} 
                variant="outline"
                className="border-slate-300 hover:bg-slate-50 shadow-lg"
              >
                <Download className="h-4 w-4 mr-2" />
                Export Report
              </Button>
            </div>

            <div className="text-center">
              <img 
                src="https://images.unsplash.com/photo-1718778449026-fc05939d7650" 
                alt="Financial Data Processing" 
                className="w-full max-w-2xl mx-auto h-64 object-cover rounded-lg shadow-lg"
              />
            </div>
          </TabsContent>

          {/* Reconciliation Results Tab */}
          <TabsContent value="reconciliation" className="space-y-6">
            <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                  Reconciliation Results
                </CardTitle>
                <CardDescription>
                  Detailed transaction matching results and discrepancies
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {reconciliationResults.length > 0 ? (
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                      {reconciliationResults.slice(0, 50).map((result, index) => (
                        <div key={index} className="flex items-center justify-between p-3 rounded-lg border bg-slate-50/50">
                          <div className="flex items-center gap-3">
                            <Badge className={getStatusColor(result.status)}>
                              {result.status.replace('_', ' ')}
                            </Badge>
                            <div className="text-sm">
                              <div className="font-medium">Account: {result.account_id}</div>
                              <div className="text-slate-500">Date: {result.date}</div>
                            </div>
                          </div>
                          <div className="text-sm text-right">
                            {result.transaction_id && (
                              <div className="text-slate-600">TXN: {result.transaction_id}</div>
                            )}
                            {result.gl_id && (
                              <div className="text-slate-600">GL: {result.gl_id}</div>
                            )}
                            {result.amount_difference && (
                              <div className="text-red-600 font-medium">
                                Diff: ${Math.abs(result.amount_difference).toFixed(2)}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <CheckCircle2 className="h-12 w-12 text-slate-300 mx-auto mb-4" />
                      <p className="text-slate-500">No reconciliation results yet. Upload data and run reconciliation.</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Anomalies Tab */}
          <TabsContent value="anomalies" className="space-y-6">
            <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-orange-600" />
                  Detected Anomalies
                </CardTitle>
                <CardDescription>
                  Statistical and ML-based anomaly detection results
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {anomalies.length > 0 ? (
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                      {anomalies.map((anomaly, index) => (
                        <div key={index} className="flex items-center justify-between p-3 rounded-lg border bg-red-50/50 border-red-100">
                          <div className="flex items-center gap-3">
                            <AlertTriangle className="h-5 w-5 text-red-600" />
                            <div className="text-sm">
                              <div className="font-medium">Transaction: {anomaly.transaction_id}</div>
                              <div className="text-slate-500">Method: {anomaly.detection_method}</div>
                            </div>
                          </div>
                          <div className="text-sm text-right">
                            <Badge variant="destructive" className="mb-1">
                              {anomaly.anomaly_type}
                            </Badge>
                            <div className="text-red-700 font-medium">
                              Score: {anomaly.anomaly_score.toFixed(2)}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <AlertTriangle className="h-12 w-12 text-slate-300 mx-auto mb-4" />
                      <p className="text-slate-500">No anomalies detected yet. Upload data and run anomaly detection.</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
      <Toaster />
    </div>
  );
}

export default App;