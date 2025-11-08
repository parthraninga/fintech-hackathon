import { useState, useEffect, useRef } from 'react'
import { io, Socket } from 'socket.io-client'
import ProcessingLogs from './components/ProcessingLogs'
import './App.css'

interface OCRResults {
  filename: string;
  uploadedFile: string;
  textract: string | null;
  tesseract: string | null;
  errors: string[];
}

interface ProcessingStep {
  step: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  details?: string;
  timestamp?: string;
}

interface DualAIResults {
  success: boolean;
  extracted_data?: any;
  database_ids?: any;
  database_report?: any;
  validation_result?: any;
  duplication_analysis?: any;
  document_classification?: any;
  ai_reasoning?: any;
  errors?: string[];
  processing_log?: string;
  raw_output?: string;
  textract_input?: string;
  tesseract_input?: string;
}

function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResults] = useState<OCRResults | null>(null);
  const [error, setError] = useState<string>('');
  const [processingSteps, setProcessingSteps] = useState<ProcessingStep[]>([]);
  const [dualAIResults, setDualAIResults] = useState<DualAIResults | null>(null);
  const [currentStep, setCurrentStep] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'extraction' | 'logs'>('extraction');
  const [realTimeLogs, setRealTimeLogs] = useState<Array<{
    type: string;
    message: string;
    timestamp: string;
    script?: string;
  }>>([]);
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    // Initialize Socket.IO connection for real-time processing updates only
    socketRef.current = io('http://localhost:3001', {
      transports: ['websocket', 'polling'],
      upgrade: true,
      timeout: 20000,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5
    });

    // Processing event listeners
    socketRef.current.on('processing_step', (data: ProcessingStep) => {
      setCurrentStep(data.step);
      setProcessingSteps(prev => {
        const newSteps = [...prev];
        const existingIndex = newSteps.findIndex(step => step.step === data.step);
        if (existingIndex >= 0) {
          newSteps[existingIndex] = data;
        } else {
          newSteps.push(data);
        }
        return newSteps;
      });
    });

    socketRef.current.on('dual_ai_complete', (data: DualAIResults) => {
      console.log('Dual AI Results received:', data);
      setDualAIResults(data);
      setIsProcessing(false);
      setCurrentStep('Processing Complete');
    });

    socketRef.current.on('processing_error', (data: { error: string }) => {
      setError(data.error);
      setIsProcessing(false);
    });

    socketRef.current.on('processing_log', (logData: {
      type: string;
      message: string;
      timestamp: string;
      script?: string;
    }) => {
      setRealTimeLogs(prev => [...prev, logData]);
    });

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, []);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
      setError('');
      setResults(null);
      setProcessingSteps([]);
      setDualAIResults(null);
      setCurrentStep('');
    } else {
      setError('Please select a valid PDF file');
      setSelectedFile(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || !socketRef.current) return;

    setIsProcessing(true);
    setError('');
    setProcessingSteps([]);
    setRealTimeLogs([]);
    setCurrentStep('Initializing...');

    try {
      const formData = new FormData();
      formData.append('pdf', selectedFile);

      // Join a room for this processing session
      const sessionId = Date.now().toString();
      socketRef.current.emit('join_session', sessionId);

      const response = await fetch(`http://localhost:3001/api/process-pdf?sessionId=${sessionId}`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Processing failed: ${response.statusText}`);
      }

      const data = await response.json();
      setResults(data);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Processing failed');
      setIsProcessing(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="app-container">
      {/* Navigation Header */}
      <header className="app-header">
        <div className="header-content">
          <h1>📄 PDF OCR & AI Analytics</h1>
          <p className="header-subtitle">Extract and analyze text from PDF documents with AI-powered insights</p>
        </div>
        <nav className="nav-tabs">
          <button
            className={`nav-tab ${activeTab === 'extraction' ? 'active' : ''}`}
            onClick={() => setActiveTab('extraction')}
          >
            📄 OCR Extraction
          </button>
          <button 
            className={`nav-tab ${activeTab === 'logs' ? 'active' : ''}`}
            onClick={() => setActiveTab('logs')}
          >
            📊 Processing Logs & Reports
          </button>
        </nav>
      </header>

      <main className="main-content">
        {/* OCR Extraction Tab */}
        {activeTab === 'extraction' && (
          <div className="container">
            <div className="upload-section">
              <div className="upload-card">
                <div className="upload-icon">📎</div>
                <h2>Upload PDF Document</h2>
                <p>Select a PDF file to extract text using AWS Textract and Tesseract OCR</p>
                
                <div className="file-input-wrapper">
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={handleFileSelect}
                    className="file-input"
                    id="pdf-upload"
                  />
                  <label htmlFor="pdf-upload" className="file-input-label">
                    {selectedFile ? (
                      <div className="selected-file">
                        <span className="file-name">{selectedFile.name}</span>
                        <span className="file-size">
                          {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                        </span>
                      </div>
                    ) : (
                      <div className="upload-prompt">
                        <span>Choose PDF File</span>
                        <small>or drag and drop</small>
                      </div>
                    )}
                  </label>
                </div>

                {selectedFile && (
                  <button
                    onClick={handleUpload}
                    disabled={isProcessing}
                    className="process-button"
                  >
                    {isProcessing ? (
                      <>
                        <div className="spinner"></div>
                        Processing...
                      </>
                    ) : (
                      <>
                        <span>🚀</span>
                        Process PDF
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>

            {error && (
              <div className="error-card">
                <div className="error-icon">❌</div>
                <div className="error-content">
                  <h3>Processing Error</h3>
                  <p>{error}</p>
                </div>
              </div>
            )}

            {isProcessing && (
              <div className="processing-card">
                <div className="processing-header">
                  <h3>🔄 Processing: {currentStep}</h3>
                  <div className="progress-bar">
                    <div className="progress-fill"></div>
                  </div>
                </div>
                
                <div className="processing-steps">
                  {processingSteps.map((step, index) => (
                    <div key={index} className={`step-item ${step.status}`}>
                      <div className="step-icon">
                        {step.status === 'completed' && '✅'}
                        {step.status === 'processing' && '⏳'}
                        {step.status === 'error' && '❌'}
                        {step.status === 'pending' && '⏸️'}
                      </div>
                      <div className="step-content">
                        <h4>{step.step}</h4>
                        {step.details && <p>{step.details}</p>}
                        {step.timestamp && <small>{new Date(step.timestamp).toLocaleTimeString()}</small>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {!isProcessing && currentStep === 'Processing Complete' && (
              <div className="completion-card">
                <div className="completion-icon">✅</div>
                <div className="completion-content">
                  <h3>Processing Complete!</h3>
                  <p>Your PDF has been successfully processed. Switch to the "Processing Logs & Reports" tab to view detailed results.</p>
                  <button
                    onClick={() => setActiveTab('logs')}
                    className="view-results-button"
                  >
                    📊 View Results
                  </button>
                </div>
              </div>
            )}

            {results && (
              <div className="results-section">
                <h2>✅ Processing Results</h2>
                
                <div className="results-grid">
                  <div className="result-card">
                    <div className="result-header">
                      <h3>📁 Original File</h3>
                    </div>
                    <div className="result-content">
                      <p><strong>{results.filename}</strong></p>
                    </div>
                  </div>

                  {results.textract && (
                    <div className="result-card success">
                      <div className="result-header">
                        <h3>🔍 AWS Textract Results</h3>
                      </div>
                      <div className="result-content">
                        <div className="file-path">
                          <code>{results.textract}</code>
                          <button 
                            onClick={() => copyToClipboard(results.textract!)}
                            className="copy-button"
                            title="Copy path"
                          >
                            📋
                          </button>
                        </div>
                      </div>
                    </div>
                  )}

                  {results.tesseract && (
                    <div className="result-card success">
                      <div className="result-header">
                        <h3>🔤 Tesseract OCR Results</h3>
                      </div>
                      <div className="result-content">
                        <div className="file-path">
                          <code>{results.tesseract}</code>
                          <button 
                            onClick={() => copyToClipboard(results.tesseract!)}
                            className="copy-button"
                            title="Copy path"
                          >
                            📋
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {results.errors.length > 0 && (
                  <div className="result-card error">
                    <div className="result-header">
                      <h3>⚠️ Warnings</h3>
                    </div>
                    <div className="result-content">
                      <ul>
                        {results.errors.map((error, index) => (
                          <li key={index}>{error}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            )}

            {dualAIResults && (
              <div className="ai-results-section">
                <h2>🤖 AI Analysis Results</h2>
                
                <div className="ai-results-grid">
                  {dualAIResults.extracted_data && (
                    <div className="ai-result-card">
                      <div className="ai-result-header">
                        <h3>📊 Extracted Invoice Data</h3>
                      </div>
                      <div className="ai-result-content">
                        <div className="data-grid">
                          <div className="data-item">
                            <strong>Document Type:</strong> {dualAIResults.extracted_data.document_type}
                          </div>
                          <div className="data-item">
                            <strong>Invoice Number:</strong> {dualAIResults.extracted_data.invoice_number || 'N/A'}
                          </div>
                          <div className="data-item">
                            <strong>Total Amount:</strong> ₹{dualAIResults.extracted_data.total_amount || 'N/A'}
                          </div>
                          <div className="data-item">
                            <strong>Date:</strong> {dualAIResults.extracted_data.invoice_date || 'N/A'}
                          </div>
                          <div className="data-item">
                            <strong>Vendor:</strong> {dualAIResults.extracted_data.vendor_name || 'N/A'}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {dualAIResults.validation_result && (
                    <div className="ai-result-card">
                      <div className="ai-result-header">
                        <h3>🔍 Arithmetic Validation</h3>
                      </div>
                      <div className="ai-result-content">
                        <p><strong>Status:</strong> {dualAIResults.validation_result.is_valid ? '✅ Valid' : '❌ Invalid'}</p>
                        {dualAIResults.validation_result.discrepancies && dualAIResults.validation_result.discrepancies.length > 0 && (
                          <div>
                            <strong>Discrepancies:</strong>
                            <ul>
                              {dualAIResults.validation_result.discrepancies.map((disc: string, index: number) => (
                                <li key={index}>{disc}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {dualAIResults.database_ids && (
                    <div className="ai-result-card">
                      <div className="ai-result-header">
                        <h3>💾 Database Storage</h3>
                      </div>
                      <div className="ai-result-content">
                        <p>Invoice stored successfully with ID: <code>{dualAIResults.database_ids.invoice_id}</code></p>
                      </div>
                    </div>
                  )}
                </div>
                
                {/* Detailed Database Information Section */}
                {dualAIResults.database_report && (
                  <div className="database-info-section">
                    <h2>🗃️ Database Insertion Details</h2>
                    <div className="database-summary-card">
                      <div className="summary-stats">
                        <div className="stat-item">
                          <span className="stat-number">{dualAIResults.database_report.summary.total_tables_affected}</span>
                          <span className="stat-label">Tables Updated</span>
                        </div>
                        <div className="stat-item">
                          <span className="stat-number">{dualAIResults.database_report.summary.total_records_inserted}</span>
                          <span className="stat-label">Records Inserted</span>
                        </div>
                        <div className="stat-item">
                          <span className="stat-time">{new Date(dualAIResults.database_report.summary.processing_timestamp).toLocaleTimeString()}</span>
                          <span className="stat-label">Processing Time</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="database-tables-grid">
                      {Object.entries(dualAIResults.database_report.tables).map(([tableName, tableData]: [string, any]) => (
                        <div key={tableName} className="database-table-card">
                          <div className="table-header">
                            <h3>📋 {tableData.table_info.name}</h3>
                            <p className="table-description">{tableData.table_info.description}</p>
                            <div className="table-stats">
                              <span className="record-count">{tableData.records.length} record(s) inserted</span>
                              <span className="field-count">{tableData.table_info.total_fields} fields available</span>
                            </div>
                          </div>
                          
                          {tableData.records.map((record: any, recordIndex: number) => (
                            <div key={recordIndex} className="record-details">
                              <h4>Record ID: {record.record_id}</h4>
                              <div className="fields-grid">
                                {Object.entries(record.fields).map(([fieldName, fieldInfo]: [string, any]) => (
                                  <div key={fieldName} className="field-item">
                                    <div className="field-header">
                                      <strong>{fieldName}</strong>
                                      <span className="field-type">({fieldInfo.type})</span>
                                    </div>
                                    <div className="field-value">
                                      {fieldInfo.formatted_value}
                                    </div>
                                    <div className="field-description">
                                      {fieldInfo.description}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      ))}
                    </div>
                    
                    {/* Relationships Section */}
                    {dualAIResults.database_report.relationships && Object.keys(dualAIResults.database_report.relationships).length > 0 && (
                      <div className="relationships-section">
                        <h3>🔗 Table Relationships</h3>
                        <div className="relationships-grid">
                          {Object.entries(dualAIResults.database_report.relationships).map(([relName, relInfo]: [string, any]) => (
                            <div key={relName} className="relationship-card">
                              <div className="relationship-type">{relInfo.type}</div>
                              <div className="relationship-description">{relInfo.description}</div>
                              <div className="relationship-rule">{relInfo.business_rule}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* Business Impact Section */}
                    {dualAIResults.database_report.business_impact && (
                      <div className="business-impact-section">
                        <h3>📈 Business Impact Analysis</h3>
                        <div className="impact-categories">
                          {dualAIResults.database_report.business_impact.data_quality && (
                            <div className="impact-category">
                              <h4>Data Quality</h4>
                              {Object.entries(dualAIResults.database_report.business_impact.data_quality).map(([key, value]: [string, any]) => (
                                <div key={key} className="impact-item">
                                  <span className={`status-badge ${value.status?.toLowerCase().replace(' ', '-')}`}>
                                    {value.status}
                                  </span>
                                  <span className="impact-description">{value.description}</span>
                                </div>
                              ))}
                            </div>
                          )}
                          
                          {dualAIResults.database_report.business_impact.compliance && (
                            <div className="impact-category">
                              <h4>Compliance</h4>
                              {Object.entries(dualAIResults.database_report.business_impact.compliance).map(([key, value]: [string, any]) => (
                                <div key={key} className="impact-item">
                                  <span className={`status-badge ${value.status?.toLowerCase().replace(' ', '-')}`}>
                                    {value.status}
                                  </span>
                                  <span className="impact-description">{value.description}</span>
                                </div>
                              ))}
                            </div>
                          )}
                          
                          {dualAIResults.database_report.business_impact.operational && (
                            <div className="impact-category">
                              <h4>Operational Metrics</h4>
                              <div className="operational-stats">
                                <div className="op-stat">
                                  <span className="op-number">{dualAIResults.database_report.business_impact.operational.database_growth?.total_invoices}</span>
                                  <span className="op-label">Total Invoices</span>
                                </div>
                                <div className="op-stat">
                                  <span className="op-number">{dualAIResults.database_report.business_impact.operational.database_growth?.total_companies}</span>
                                  <span className="op-label">Total Companies</span>
                                </div>
                                <div className="op-stat">
                                  <span className="op-number">{dualAIResults.database_report.business_impact.operational.database_growth?.total_products}</span>
                                  <span className="op-label">Total Products</span>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Processing Logs & Reports Tab */}
        {activeTab === 'logs' && (
          <ProcessingLogs
            results={results}
            dualAIResults={dualAIResults}
            processingSteps={processingSteps}
            realTimeLogs={realTimeLogs}
            onBack={() => setActiveTab('extraction')}
          />
        )}
      </main>
    </div>
  )
}

export default App