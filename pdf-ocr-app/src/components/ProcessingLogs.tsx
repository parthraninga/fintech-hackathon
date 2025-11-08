import React, { useState } from 'react';
import './ProcessingLogs.css';

interface ProcessingLogsProps {
  results: any;
  dualAIResults: any;
  processingSteps: any[];
  realTimeLogs: Array<{
    type: string;
    message: string;
    timestamp: string;
    script?: string;
  }>;
  onBack: () => void;
}

const ProcessingLogs: React.FC<ProcessingLogsProps> = ({
  results,
  dualAIResults,
  processingSteps,
  realTimeLogs,
  onBack
}) => {
  const [showDetailedLogs, setShowDetailedLogs] = useState(false);
  const [isDownloadingPDF, setIsDownloadingPDF] = useState(false);

  const formatProcessingLog = (log: string) => {
    // Split log into sections for better formatting
    const lines = log.split('\n');
    const formattedLines = lines.map((line, index) => {
      // Highlight different types of messages
      let className = 'log-line';
      if (line.includes('✅')) className += ' success';
      else if (line.includes('❌')) className += ' error';
      else if (line.includes('⚠️')) className += ' warning';
      else if (line.includes('🔍') || line.includes('🧠')) className += ' processing';
      else if (line.includes('💾')) className += ' database';
      else if (line.includes('📊') || line.includes('📋')) className += ' analysis';

      return (
        <div key={index} className={className}>
          {line}
        </div>
      );
    });

    return formattedLines;
  };

  const downloadPDFReport = async () => {
    setIsDownloadingPDF(true);
    try {
      const response = await fetch('http://localhost:3001/api/generate-pdf-report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          results,
          dualAIResults,
          processingSteps
        })
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `processing-report-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        throw new Error('Failed to generate PDF report');
      }
    } catch (error) {
      console.error('Error downloading PDF:', error);
      alert('Failed to download PDF report. Please try again.');
    } finally {
      setIsDownloadingPDF(false);
    }
  };

  const getStepSummary = () => {
    const completedSteps = processingSteps.filter(step => step.status === 'completed').length;
    const errorSteps = processingSteps.filter(step => step.status === 'error').length;
    const totalSteps = processingSteps.length;

    return {
      completed: completedSteps,
      errors: errorSteps,
      total: totalSteps,
      successRate: totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0
    };
  };

  const summary = getStepSummary();

  return (
    <div className="processing-logs-container">
      <div className="logs-header">
        <h1>📊 Processing Logs & Reports</h1>
        <div className="header-actions">
          <button
            onClick={() => setShowDetailedLogs(!showDetailedLogs)}
            className="toggle-button"
          >
            {showDetailedLogs ? '📋 Show Summary' : '� Show Detailed Logs'}
          </button>
        </div>
      </div>

      {/* Processing Summary */}
      <div className="processing-summary">
        <h2>🎯 Processing Summary</h2>
        <div className="summary-stats">
          <div className="stat-card success">
            <h3>{summary.completed}</h3>
            <p>Completed Steps</p>
          </div>
          <div className="stat-card error">
            <h3>{summary.errors}</h3>
            <p>Errors</p>
          </div>
          <div className="stat-card info">
            <h3>{summary.total}</h3>
            <p>Total Steps</p>
          </div>
          <div className="stat-card">
            <h3>{summary.successRate}%</h3>
            <p>Success Rate</p>
          </div>
        </div>
      </div>

      {/* Real-time Processing Logs */}
      {realTimeLogs && realTimeLogs.length > 0 && (
        <div className="realtime-logs-section">
          <h2>🔴 Real-time Processing Logs</h2>
          <div className="realtime-logs-container">
            {realTimeLogs.map((log, index) => (
              <div 
                key={index} 
                className={`log-entry ${log.type}`}
              >
                <div className="log-header">
                  <span className="log-timestamp">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                  {log.script && (
                    <span className="log-script">
                      📜 {log.script}
                    </span>
                  )}
                  <span className={`log-type ${log.type}`}>
                    {log.type === 'python_stdout' ? '✅' : 
                     log.type === 'python_stderr' ? '⚠️' : '📝'}
                  </span>
                </div>
                <div className="log-message">
                  {log.message}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* File Information */}
      {results && (
        <div className="file-info-section">
          <h2>📁 File Information</h2>
          <div className="info-grid">
            <div className="info-item">
              <strong>Original File:</strong> {results.filename}
            </div>
            <div className="info-item">
              <strong>Textract Output:</strong> 
              {results.textract ? (
                <span className="file-path" title={results.textract}>
                  {results.textract.split('/').pop()}
                </span>
              ) : 'Not available'}
            </div>
            <div className="info-item">
              <strong>Tesseract Output:</strong> 
              {results.tesseract ? (
                <span className="file-path" title={results.tesseract}>
                  {results.tesseract.split('/').pop()}
                </span>
              ) : 'Not available'}
            </div>
          </div>
        </div>
      )}

      {/* AI Analysis Results */}
      {dualAIResults && (
        <div className="ai-analysis-section">
          <h2>🤖 AI Analysis Results</h2>
          
          {dualAIResults.extracted_data && (
            <div className="analysis-card">
              <h3>📊 Extracted Data</h3>
              <div className="extracted-data-grid">
                <div className="data-row">
                  <span className="label">Document Type:</span>
                  <span className="value">{dualAIResults.extracted_data.document_type || 'N/A'}</span>
                </div>
                <div className="data-row">
                  <span className="label">Invoice Number:</span>
                  <span className="value">{dualAIResults.extracted_data.invoice_number || 'N/A'}</span>
                </div>
                <div className="data-row">
                  <span className="label">Total Amount:</span>
                  <span className="value">₹{dualAIResults.extracted_data.total_amount || 'N/A'}</span>
                </div>
                <div className="data-row">
                  <span className="label">Invoice Date:</span>
                  <span className="value">{dualAIResults.extracted_data.invoice_date || 'N/A'}</span>
                </div>
                <div className="data-row">
                  <span className="label">Vendor:</span>
                  <span className="value">{dualAIResults.extracted_data.vendor_name || 'N/A'}</span>
                </div>
              </div>
            </div>
          )}

          {dualAIResults.validation_result && (
            <div className="analysis-card">
              <h3>🔍 Validation Status</h3>
              <div className={`validation-status ${dualAIResults.validation_result.is_valid ? 'valid' : 'invalid'}`}>
                {dualAIResults.validation_result.is_valid ? '✅ Valid' : '❌ Invalid'}
              </div>
              {dualAIResults.validation_result.discrepancies && dualAIResults.validation_result.discrepancies.length > 0 && (
                <div className="discrepancies">
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
        </div>
      )}

      {/* Processing Steps Timeline */}
      <div className="processing-timeline">
        <h2>⏱️ Processing Timeline</h2>
        <div className="timeline">
          {processingSteps.map((step, index) => (
            <div key={index} className={`timeline-item ${step.status}`}>
              <div className="timeline-marker">
                {step.status === 'completed' && '✅'}
                {step.status === 'processing' && '⏳'}
                {step.status === 'error' && '❌'}
                {step.status === 'pending' && '⏸️'}
              </div>
              <div className="timeline-content">
                <h4>{step.step}</h4>
                {step.details && <p>{step.details}</p>}
                {step.timestamp && (
                  <small>{new Date(step.timestamp).toLocaleString()}</small>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Detailed Processing Logs */}
      <div className="detailed-logs-section">
        <div className="logs-header-controls">
          <h2>📝 Detailed Processing Logs</h2>
          <button
            onClick={() => setShowDetailedLogs(!showDetailedLogs)}
            className="toggle-logs-button"
          >
            {showDetailedLogs ? '🔼 Hide Detailed Logs' : '🔽 Show Detailed Logs'}
          </button>
        </div>
        
        {showDetailedLogs && (
          <div className="logs-container">
            {dualAIResults?.processing_log ? (
              <div className="logs-content">
                <div className="log-source-info">
                  <h4>🤖 Dual AI Agent Processing Log</h4>
                  <p>Complete execution log from the AI analysis engine</p>
                </div>
                {formatProcessingLog(dualAIResults.processing_log)}
              </div>
            ) : dualAIResults?.raw_output ? (
              <div className="logs-content">
                <div className="log-source-info">
                  <h4>📄 Raw Processing Output</h4>
                  <p>Raw output from the processing pipeline</p>
                </div>
                {formatProcessingLog(dualAIResults.raw_output)}
              </div>
            ) : (
              <div className="logs-content">
                <div className="no-logs-message">
                  <h4>⚠️ No Detailed Logs Available</h4>
                  <p>Processing logs are not available yet. Please run a PDF through the OCR processing first.</p>
                  {dualAIResults && (
                    <details style={{ marginTop: '1rem', color: '#666' }}>
                      <summary>Debug: Available data keys</summary>
                      <pre>{JSON.stringify(Object.keys(dualAIResults), null, 2)}</pre>
                    </details>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ProcessingLogs;