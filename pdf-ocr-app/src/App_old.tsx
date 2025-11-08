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
    // 🔥 EXTREME WEBSOCKET CLIENT DEBUGGING 🔥
    console.log('� CLIENT DEBUG: Initializing Socket.IO connection with extreme debugging');
    
    const connectionStartTime = Date.now();
    const debugOptions = {
      transports: ['websocket', 'polling'],
      upgrade: true,
      timeout: 20000,
      forceNew: true,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 10,
      withCredentials: true,
      autoConnect: true
    };
    
    console.log('🔧 CLIENT DEBUG: Socket.IO configuration', {
      url: 'http://localhost:3001',
      options: debugOptions,
      timestamp: new Date().toISOString()
    });
    
    socketRef.current = io('http://localhost:3001', debugOptions);

    // 🔥 EXTREME CONNECTION EVENT DEBUGGING 🔥
    socketRef.current.on('connect', () => {
      const connectionTime = Date.now() - connectionStartTime;
      console.log('🎯 CLIENT DEBUG: Socket connection established!', {
        socketId: socketRef.current?.id,
        transport: socketRef.current?.io?.engine?.transport?.name,
        connected: socketRef.current?.connected,
        connectionTime: connectionTime,
        timestamp: new Date().toISOString(),
        engine: {
          readyState: (socketRef.current?.io?.engine as any)?.readyState,
          transport: socketRef.current?.io?.engine?.transport?.name,
          upgraded: (socketRef.current?.io?.engine as any)?.upgraded,
          ping: (socketRef.current?.io?.engine as any)?.ping,
          pingInterval: (socketRef.current?.io?.engine as any)?.pingInterval,
          pingTimeout: (socketRef.current?.io?.engine as any)?.pingTimeout
        }
      });
      setSocketConnected(true);
    });

    socketRef.current.on('connection_confirmed', (data) => {
      console.log('✅ CLIENT DEBUG: Connection confirmed by server', {
        serverData: data,
        clientSocketId: socketRef.current?.id,
        transport: socketRef.current?.io?.engine?.transport?.name,
        timestamp: new Date().toISOString()
      });
      setSocketConnected(true);
    });

    socketRef.current.on('session_joined', (data) => {
      console.log('📍 CLIENT DEBUG: Session joined confirmation', {
        sessionData: data,
        timestamp: new Date().toISOString()
      });
    });

    socketRef.current.on('disconnect', (reason) => {
      console.log('💔 CLIENT DEBUG: Socket disconnection initiated', {
        reason: reason,
        socketId: socketRef.current?.id,
        wasConnected: socketRef.current?.connected,
        transport: socketRef.current?.io?.engine?.transport?.name,
        timestamp: new Date().toISOString()
      });
      setSocketConnected(false);
    });

    socketRef.current.on('connect_error', (error: any) => {
      console.error('💥 CLIENT DEBUG: Connection error occurred', {
        error: error.message,
        description: error.description,
        context: error.context,
        type: error.type,
        timestamp: new Date().toISOString()
      });
      setSocketConnected(false);
    });

    socketRef.current.on('reconnect', (attemptNumber) => {
      console.log('🔄 CLIENT DEBUG: Reconnection successful', {
        attemptNumber: attemptNumber,
        socketId: socketRef.current?.id,
        transport: socketRef.current?.io?.engine?.transport?.name,
        timestamp: new Date().toISOString()
      });
      setSocketConnected(true);
    });

    socketRef.current.on('reconnect_attempt', (attemptNumber) => {
      console.log('🔄 CLIENT DEBUG: Reconnection attempt', {
        attemptNumber: attemptNumber,
        timestamp: new Date().toISOString()
      });
    });

    socketRef.current.on('reconnect_error', (error) => {
      console.error('❌ CLIENT DEBUG: Reconnection error', {
        error: error.message,
        timestamp: new Date().toISOString()
      });
      setSocketConnected(false);
    });

    socketRef.current.on('reconnect_failed', () => {
      console.error('💀 CLIENT DEBUG: Reconnection failed completely', {
        timestamp: new Date().toISOString()
      });
      setSocketConnected(false);
    });

    // 🔥 EXTREME ENGINE.IO EVENT DEBUGGING 🔥
    socketRef.current.io.on('error', (error) => {
      console.error('🚨 CLIENT DEBUG: Engine.IO error', {
        error: error,
        timestamp: new Date().toISOString()
      });
    });

    socketRef.current.io.on('ping', () => {
      console.log('🏓 CLIENT DEBUG: Engine.IO ping sent', {
        timestamp: new Date().toISOString()
      });
    });

    // 🔥 ENGINE.IO DETAILED EVENT MONITORING 🔥
    if (socketRef.current.io.engine) {
      const engine = socketRef.current.io.engine as any;
      
      engine.on('pong', (latency: any) => {
        console.log('🏓 CLIENT DEBUG: Engine.IO pong received', {
          latency: latency,
          timestamp: new Date().toISOString()
        });
      });

      engine.on('packet', (packet: any) => {
        console.log('📦 CLIENT DEBUG: Engine.IO packet', {
          type: packet.type,
          data: typeof packet.data === 'string' ? packet.data.substring(0, 100) + '...' : '[binary]',
          timestamp: new Date().toISOString()
        });
      });

      engine.on('packetCreate', (packet: any) => {
        console.log('📤 CLIENT DEBUG: Engine.IO packet created', {
          type: packet.type,
          timestamp: new Date().toISOString()
        });
      });

      engine.on('upgrade', (transport: any) => {
        console.log('🚀 CLIENT DEBUG: Transport upgrade', {
          newTransport: transport.name,
          timestamp: new Date().toISOString()
        });
      });

      engine.on('upgradeError', (error: any) => {
        console.error('❌ CLIENT DEBUG: Transport upgrade error', {
          error: error,
          timestamp: new Date().toISOString()
        });
      });
    }

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
      console.log('Processing log present:', !!data.processing_log);
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
    <div className="app-with-chatbot">
      <div className="main-content">
      {/* Navigation Header */}
      <header className="app-header">
        <h1>📄 PDF OCR & AI Analytics</h1>
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

      {/* OCR Extraction Tab */}
      {activeTab === 'extraction' && (
        <div className="container">
          <div className="tab-header">
            <h2>📄 PDF OCR Extraction</h2>
            <p>Upload a PDF file to extract text using AWS Textract and Tesseract OCR</p>
          </div>

        <div className="upload-section">
          <div className="file-input-wrapper">
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileSelect}
              className="file-input"
              id="pdf-upload"
            />
            <label htmlFor="pdf-upload" className="file-input-label">
              {selectedFile ? selectedFile.name : 'Choose PDF File'}
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
                'Process PDF'
              )}
            </button>
          )}
        </div>

        {error && (
          <div className="error-message">
            <strong>❌ Error:</strong> {error}
          </div>
        )}

        {isProcessing && (
          <div className="processing-status">
            <div className="current-step">
              <h3>🔄 Current Step: {currentStep}</h3>
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
            
            <div className="progress-bar">
              <div className="progress-fill"></div>
            </div>
            <p>Processing your PDF with AI-powered analysis...</p>
          </div>
        )}

        {!isProcessing && currentStep === 'Processing Complete' && (
          <div className="processing-complete">
            <div className="completion-message">
              <h3>✅ Processing Complete!</h3>
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
            <h2>✅ Processing Complete</h2>
            
            <div className="result-item">
              <h3>📁 Original File:</h3>
              <p><strong>{results.filename}</strong></p>
            </div>

            {results.textract && (
              <div className="result-item success">
                <h3>🔍 AWS Textract Results:</h3>
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
            )}

            {results.tesseract && (
              <div className="result-item success">
                <h3>🔤 Tesseract OCR Results:</h3>
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
            )}

            {results.errors.length > 0 && (
              <div className="result-item error">
                <h3>⚠️ Warnings:</h3>
                <ul>
                  {results.errors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {dualAIResults && (
          <div className="ai-results-section">
            <h2>🤖 AI Analysis Complete</h2>
            
            {dualAIResults.extracted_data && (
              <div className="result-item success">
                <h3>📊 Extracted Invoice Data:</h3>
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
            )}

            {dualAIResults.document_classification && (
              <div className="result-item info">
                <h3>📋 Document Classification:</h3>
                <p><strong>Type:</strong> {dualAIResults.document_classification.document_type}</p>
                <p><strong>Confidence:</strong> {(dualAIResults.document_classification.confidence * 100).toFixed(1)}%</p>
              </div>
            )}

            {dualAIResults.validation_result && (
              <div className="result-item info">
                <h3>🔍 Arithmetic Validation:</h3>
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
            )}

            {dualAIResults.duplication_analysis && (
              <div className="result-item warning">
                <h3>🔄 Duplication Analysis:</h3>
                <p><strong>Status:</strong> {dualAIResults.duplication_analysis.is_duplicate ? '⚠️ Potential Duplicate' : '✅ Unique'}</p>
                {dualAIResults.duplication_analysis.confidence && (
                  <p><strong>Confidence:</strong> {(dualAIResults.duplication_analysis.confidence * 100).toFixed(1)}%</p>
                )}
              </div>
            )}

            {dualAIResults.ai_reasoning && (
              <div className="result-item info">
                <h3>🧠 AI Reasoning:</h3>
                <p><strong>Summary:</strong> {dualAIResults.ai_reasoning.summary}</p>
                <p><strong>Confidence:</strong> {dualAIResults.ai_reasoning.confidence_score}/10</p>
                {dualAIResults.ai_reasoning.key_insights && (
                  <div>
                    <strong>Key Insights:</strong>
                    <ul>
                      {dualAIResults.ai_reasoning.key_insights.map((insight: string, index: number) => (
                        <li key={index}>{insight}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {dualAIResults.database_ids && (
              <div className="result-item success">
                <h3>💾 Database Storage:</h3>
                <p>Invoice stored successfully with ID: <code>{dualAIResults.database_ids.invoice_id}</code></p>
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
      </div>

      {/* Always-visible ChatBot Sidebar */}
      <ChatBot socket={socketRef.current} connected={socketConnected} />
    </div>
  )
}

export default App
