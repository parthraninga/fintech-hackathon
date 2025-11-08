import { useState, useEffect } from 'react';

interface DocumentContentsProps {
  results: any;
  dualAIResults: any;
  onBack: () => void;
}

interface ExtractedContent {
  textract?: {
    raw_text?: string;
    tables?: any[];
    forms?: any[];
    blocks?: any[];
  };
  tesseract?: {
    raw_text?: string;
    confidence?: number;
  };
  extracted_data?: {
    invoice_number?: string;
    invoice_date?: string;
    supplier_name?: string;
    buyer_name?: string;
    total_amount?: number;
    line_items?: any[];
    [key: string]: any;
  };
}

const DocumentContents: React.FC<DocumentContentsProps> = ({ results, dualAIResults, onBack }) => {
  const [content, setContent] = useState<ExtractedContent>({});
  const [loading, setLoading] = useState(false);
  const [activeContentTab, setActiveContentTab] = useState<'textract' | 'tesseract' | 'extracted'>('extracted');

  useEffect(() => {
    loadDocumentContents();
  }, [results, dualAIResults]);

  const loadDocumentContents = async () => {
    if (!results) return;

    setLoading(true);
    const newContent: ExtractedContent = {};

    try {
      // Load Textract content
      if (results.textract) {
        try {
          const response = await fetch(`/api/file-content?path=${encodeURIComponent(results.textract)}`);
          if (response.ok) {
            const textractData = await response.json();
            newContent.textract = {
              raw_text: extractTextFromTextract(textractData),
              blocks: textractData.Blocks || [],
              tables: extractTablesFromTextract(textractData),
              forms: extractFormsFromTextract(textractData)
            };
          }
        } catch (error) {
          console.error('Error loading Textract content:', error);
        }
      }

      // Load Tesseract content
      if (results.tesseract) {
        try {
          const response = await fetch(`/api/file-content?path=${encodeURIComponent(results.tesseract)}`);
          if (response.ok) {
            const tesseractData = await response.json();
            newContent.tesseract = {
              raw_text: tesseractData.text || tesseractData.raw_text,
              confidence: tesseractData.confidence
            };
          }
        } catch (error) {
          console.error('Error loading Tesseract content:', error);
        }
      }

      // Load extracted data from AI
      if (dualAIResults?.extracted_data) {
        newContent.extracted_data = dualAIResults.extracted_data;
      }

      setContent(newContent);
    } catch (error) {
      console.error('Error loading document contents:', error);
    } finally {
      setLoading(false);
    }
  };

  const extractTextFromTextract = (textractData: any): string => {
    if (!textractData.Blocks) return 'No text blocks found';
    
    return textractData.Blocks
      .filter((block: any) => block.BlockType === 'LINE')
      .map((line: any) => line.Text)
      .join('\n');
  };

  const extractTablesFromTextract = (textractData: any): any[] => {
    if (!textractData.Blocks) return [];
    
    return textractData.Blocks
      .filter((block: any) => block.BlockType === 'TABLE')
      .map((table: any, index: number) => ({
        id: table.Id,
        index: index + 1,
        confidence: table.Confidence,
        relationships: table.Relationships || []
      }));
  };

  const extractFormsFromTextract = (textractData: any): any[] => {
    if (!textractData.Blocks) return [];
    
    return textractData.Blocks
      .filter((block: any) => block.BlockType === 'KEY_VALUE_SET')
      .map((form: any, index: number) => ({
        id: form.Id,
        index: index + 1,
        entityTypes: form.EntityTypes,
        confidence: form.Confidence,
        text: form.Text
      }));
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  if (loading) {
    return (
      <div className="document-contents">
        <div className="contents-header">
          <button onClick={onBack} className="back-button">← Back to Results</button>
          <h2>📄 Document Contents</h2>
        </div>
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading document contents...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="document-contents">
      <div className="contents-header">
        <button onClick={onBack} className="back-button">← Back to Results</button>
        <h2>📄 Document Contents</h2>
        <p>View the actual extracted text and data from your uploaded document</p>
      </div>

      <div className="content-tabs">
        <button 
          className={`content-tab ${activeContentTab === 'extracted' ? 'active' : ''}`}
          onClick={() => setActiveContentTab('extracted')}
        >
          🤖 AI Extracted Data
        </button>
        <button 
          className={`content-tab ${activeContentTab === 'textract' ? 'active' : ''}`}
          onClick={() => setActiveContentTab('textract')}
        >
          🔍 AWS Textract
        </button>
        <button 
          className={`content-tab ${activeContentTab === 'tesseract' ? 'active' : ''}`}
          onClick={() => setActiveContentTab('tesseract')}
        >
          🔤 Tesseract OCR
        </button>
      </div>

      <div className="content-display">
        {activeContentTab === 'extracted' && content.extracted_data && (
          <div className="extracted-content">
            <div className="content-section">
              <div className="section-header">
                <h3>📊 Structured Invoice Data</h3>
                <button 
                  onClick={() => copyToClipboard(JSON.stringify(content.extracted_data, null, 2))}
                  className="copy-button"
                  title="Copy JSON"
                >
                  📋 Copy JSON
                </button>
              </div>
              
              <div className="data-grid">
                {Object.entries(content.extracted_data).map(([key, value]) => (
                  <div key={key} className="data-item">
                    <div className="data-label">{key.replace(/_/g, ' ').toUpperCase()}</div>
                    <div className="data-value">
                      {typeof value === 'object' ? (
                        <pre>{JSON.stringify(value, null, 2)}</pre>
                      ) : (
                        String(value || 'N/A')
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {content.extracted_data.line_items && content.extracted_data.line_items.length > 0 && (
                <div className="line-items-section">
                  <h4>📋 Line Items</h4>
                  <div className="line-items-grid">
                    {content.extracted_data.line_items.map((item: any, index: number) => (
                      <div key={index} className="line-item-card">
                        <h5>Item {index + 1}</h5>
                        {Object.entries(item).map(([itemKey, itemValue]) => (
                          <div key={itemKey} className="line-item-field">
                            <span className="field-name">{itemKey}:</span>
                            <span className="field-value">{String(itemValue || 'N/A')}</span>
                          </div>
                        ))}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeContentTab === 'textract' && content.textract && (
          <div className="textract-content">
            <div className="content-section">
              <div className="section-header">
                <h3>🔍 AWS Textract Raw Text</h3>
                <button 
                  onClick={() => copyToClipboard(content.textract?.raw_text || '')}
                  className="copy-button"
                  title="Copy Text"
                >
                  📋 Copy Text
                </button>
              </div>
              <div className="text-content">
                <pre>{content.textract.raw_text}</pre>
              </div>
            </div>

            {content.textract.tables && content.textract.tables.length > 0 && (
              <div className="content-section">
                <h3>📊 Detected Tables ({content.textract.tables.length})</h3>
                <div className="tables-grid">
                  {content.textract.tables.map((table, index) => (
                    <div key={index} className="table-card">
                      <h4>Table {table.index}</h4>
                      <p>Confidence: {table.confidence?.toFixed(2)}%</p>
                      <p>ID: {table.id}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {content.textract.forms && content.textract.forms.length > 0 && (
              <div className="content-section">
                <h3>📝 Detected Forms ({content.textract.forms.length})</h3>
                <div className="forms-grid">
                  {content.textract.forms.map((form, index) => (
                    <div key={index} className="form-card">
                      <h4>Form Field {form.index}</h4>
                      <p>Type: {form.entityTypes?.join(', ')}</p>
                      <p>Confidence: {form.confidence?.toFixed(2)}%</p>
                      {form.text && <p>Text: {form.text}</p>}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeContentTab === 'tesseract' && content.tesseract && (
          <div className="tesseract-content">
            <div className="content-section">
              <div className="section-header">
                <h3>🔤 Tesseract OCR Raw Text</h3>
                <div className="confidence-badge">
                  Confidence: {content.tesseract.confidence?.toFixed(2)}%
                </div>
                <button 
                  onClick={() => copyToClipboard(content.tesseract?.raw_text || '')}
                  className="copy-button"
                  title="Copy Text"
                >
                  📋 Copy Text
                </button>
              </div>
              <div className="text-content">
                <pre>{content.tesseract.raw_text}</pre>
              </div>
            </div>
          </div>
        )}

        {!content.extracted_data && !content.textract && !content.tesseract && (
          <div className="no-content">
            <h3>📄 No Content Available</h3>
            <p>Please process a document first to view its contents.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentContents;