import express from 'express';
import multer from 'multer';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';
import { spawn } from 'child_process';
import fs from 'fs';
import { createServer } from 'http';
import { Server } from 'socket.io';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const server = createServer(app);
// 🔥 EXTREME WEBSOCKET DEBUGGING CONFIGURATION 🔥
console.log('🚀 WEBSOCKET DEBUG: Initializing Socket.IO with extreme debugging...');

const io = new Server(server, {
  cors: {
    origin: ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "http://localhost:4173"],
    methods: ["GET", "POST", "OPTIONS"],
    allowedHeaders: ["*"],
    credentials: true
  },
  transports: ['websocket', 'polling'],
  allowEIO3: true,
  pingTimeout: 60000,
  pingInterval: 25000,
  upgradeTimeout: 10000,
  maxHttpBufferSize: 1e6,
  allowRequest: (req, callback) => {
    console.log('🔍 WEBSOCKET DEBUG: allowRequest called', {
      url: req.url,
      headers: req.headers,
      method: req.method,
      origin: req.headers.origin,
      timestamp: new Date().toISOString()
    });
    callback(null, true);
  }
});

// 🔥 EXTREME ENGINE.IO DEBUGGING 🔥
io.engine.on('initial_headers', (headers, req) => {
  console.log('🔧 WEBSOCKET DEBUG: Engine.IO initial headers', {
    headers: Object.keys(headers),
    url: req.url,
    timestamp: new Date().toISOString()
  });
});

io.engine.on('headers', (headers, req) => {
  console.log('🔧 WEBSOCKET DEBUG: Engine.IO headers event', {
    url: req.url,
    headers: Object.keys(headers),
    timestamp: new Date().toISOString()
  });
});

io.engine.on('connection_error', (err) => {
  console.error('💥 WEBSOCKET DEBUG: Engine.IO connection error', {
    error: err.message,
    code: err.code,
    context: err.context,
    type: err.type,
    timestamp: new Date().toISOString()
  });
});

// 🔥 SOCKET.IO MIDDLEWARE DEBUGGING 🔥
io.use((socket, next) => {
  console.log('🔍 WEBSOCKET DEBUG: Socket.IO middleware called', {
    socketId: socket.id,
    transport: socket.conn.transport.name,
    readyState: socket.conn.readyState,
    upgraded: socket.conn.upgraded,
    handshake: {
      headers: Object.keys(socket.handshake.headers),
      query: socket.handshake.query,
      url: socket.handshake.url,
      address: socket.handshake.address,
      time: socket.handshake.time,
      issued: socket.handshake.issued,
      xdomain: socket.handshake.xdomain,
      secure: socket.handshake.secure
    },
    timestamp: new Date().toISOString()
  });
  next();
});
const PORT = 3001;

// Configure CORS
app.use(cors({
  origin: ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "http://localhost:4173"],
  methods: ["GET", "POST", "OPTIONS"],
  allowedHeaders: ["Content-Type", "Authorization"],
  credentials: true,
  optionsSuccessStatus: 200
}));
app.use(express.json());

// 🔥 EXTREME SOCKET.IO CONNECTION DEBUGGING 🔥
io.on('connection', (socket) => {
  console.log('🎯 WEBSOCKET DEBUG: Client connection established!', {
    socketId: socket.id,
    transport: socket.conn.transport.name,
    readyState: socket.conn.readyState,
    upgraded: socket.conn.upgraded,
    clientIP: socket.handshake.address,
    userAgent: socket.handshake.headers['user-agent'],
    origin: socket.handshake.headers.origin,
    timestamp: new Date().toISOString()
  });
  
  // 🔥 EXTREME TRANSPORT MONITORING 🔥
  console.log('� WEBSOCKET DEBUG: Transport details', {
    name: socket.conn.transport.name,
    writable: socket.conn.transport.writable,
    readyState: socket.conn.transport.readyState,
    supportsBinary: socket.conn.transport.supportsBinary,
    supportsFraming: socket.conn.transport.supportsFraming,
    timestamp: new Date().toISOString()
  });

  // Send enhanced connection confirmation with debug info
  const connectionData = { 
    socketId: socket.id, 
    timestamp: new Date().toISOString(),
    transport: socket.conn.transport.name,
    serverDebugMode: 'EXTREME',
    connectionState: 'ESTABLISHED',
    debugInfo: {
      readyState: socket.conn.readyState,
      upgraded: socket.conn.upgraded,
      pingInterval: socket.conn.pingInterval,
      pingTimeout: socket.conn.pingTimeout
    }
  };
  
  console.log('📤 WEBSOCKET DEBUG: Sending connection_confirmed', connectionData);
  socket.emit('connection_confirmed', connectionData);

  // 🔥 EXTREME EVENT MONITORING 🔥
  socket.on('join_session', (sessionId) => {
    console.log('🔍 WEBSOCKET DEBUG: join_session event received', {
      socketId: socket.id,
      sessionId: sessionId,
      timestamp: new Date().toISOString()
    });
    
    socket.join(sessionId);
    console.log(`📍 WEBSOCKET DEBUG: Client ${socket.id} joined session: ${sessionId}`);
    
    const sessionData = { sessionId, socketId: socket.id, timestamp: new Date().toISOString() };
    console.log('📤 WEBSOCKET DEBUG: Sending session_joined', sessionData);
    socket.emit('session_joined', sessionData);
  });

  socket.on('disconnect', (reason) => {
    console.log('💔 WEBSOCKET DEBUG: Client disconnection initiated', {
      socketId: socket.id,
      reason: reason,
      transport: socket.conn.transport.name,
      timestamp: new Date().toISOString()
    });
  });

  socket.on('error', (error) => {
    console.error('🚨 WEBSOCKET DEBUG: Socket error occurred', {
      socketId: socket.id,
      error: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString()
    });
  });

  socket.on('connect_error', (error) => {
    console.error('💥 WEBSOCKET DEBUG: Connection error', {
      socketId: socket.id,
      error: error.message,
      description: error.description,
      context: error.context,
      type: error.type,
      timestamp: new Date().toISOString()
    });
  });

  // 🔥 EXTREME TRANSPORT EVENT MONITORING 🔥
  socket.conn.on('upgrade', () => {
    console.log('🚀 WEBSOCKET DEBUG: Transport upgrade successful', {
      socketId: socket.id,
      newTransport: socket.conn.transport.name,
      readyState: socket.conn.readyState,
      upgraded: socket.conn.upgraded,
      timestamp: new Date().toISOString()
    });
  });

  socket.conn.on('upgradeError', (error) => {
    console.error('❌ WEBSOCKET DEBUG: Transport upgrade failed', {
      socketId: socket.id,
      error: error.message,
      transport: socket.conn.transport.name,
      timestamp: new Date().toISOString()
    });
  });

  socket.conn.on('packet', (packet) => {
    console.log('📦 WEBSOCKET DEBUG: Packet received', {
      socketId: socket.id,
      packetType: packet.type,
      packetData: typeof packet.data === 'string' ? packet.data.substring(0, 100) + '...' : '[binary]',
      timestamp: new Date().toISOString()
    });
  });

  socket.conn.on('packetCreate', (packet) => {
    console.log('📤 WEBSOCKET DEBUG: Packet created for sending', {
      socketId: socket.id,
      packetType: packet.type,
      timestamp: new Date().toISOString()
    });
  });

  socket.conn.on('ping', () => {
    console.log('🏓 WEBSOCKET DEBUG: Ping sent', {
      socketId: socket.id,
      transport: socket.conn.transport.name,
      timestamp: new Date().toISOString()
    });
  });

  socket.conn.on('pong', () => {
    console.log('🏓 WEBSOCKET DEBUG: Pong received', {
      socketId: socket.id,
      transport: socket.conn.transport.name,
      timestamp: new Date().toISOString()
    });
  });

  socket.conn.on('close', (reason) => {
    console.log('🔚 WEBSOCKET DEBUG: Connection closed', {
      socketId: socket.id,
      reason: reason,
      transport: socket.conn.transport.name,
      timestamp: new Date().toISOString()
    });
  });

  socket.conn.on('drain', () => {
    console.log('💧 WEBSOCKET DEBUG: Socket drained', {
      socketId: socket.id,
      timestamp: new Date().toISOString()
    });
  });

  socket.conn.on('flush', () => {
    console.log('🚿 WEBSOCKET DEBUG: Socket flushed', {
      socketId: socket.id,
      timestamp: new Date().toISOString()
    });
  });

  // 🔥 EXTREME CHAT MESSAGE DEBUGGING 🔥
  socket.on('chat_message', async (data) => {
    const startTime = Date.now();
    const { message, sessionId } = data;
    
    console.log('💬 WEBSOCKET DEBUG: Chat message event received', {
      socketId: socket.id,
      messageLength: message?.length || 0,
      sessionId: sessionId,
      dataKeys: Object.keys(data),
      timestamp: new Date().toISOString(),
      messagePreview: message?.substring(0, 50) + (message?.length > 50 ? '...' : '')
    });
    
    try {
      // Emit typing indicator with debug
      console.log('💭 WEBSOCKET DEBUG: Emitting typing indicator', {
        socketId: socket.id,
        sessionId: sessionId,
        timestamp: new Date().toISOString()
      });
      socket.emit('chat_typing', { 
        sessionId, 
        timestamp: new Date().toISOString(),
        debugMode: 'EXTREME'
      });
      
      // Call Advanced Financial Chatbot with extreme debugging
      console.log('🤖 WEBSOCKET DEBUG: Calling Advanced Financial Chatbot', {
        socketId: socket.id,
        sessionId: sessionId,
        messageLength: message.length,
        timestamp: new Date().toISOString()
      });
      
      const chatbotStartTime = Date.now();
      const chatResult = await runPythonChatbot(message, sessionId || `session_${Date.now()}`);
      const chatbotEndTime = Date.now();
      
      console.log('✅ WEBSOCKET DEBUG: Advanced Financial Chatbot response received', {
        socketId: socket.id,
        sessionId: sessionId,
        processingTime: chatbotEndTime - chatbotStartTime,
        responseLength: chatResult.response?.length || 0,
        confidence: chatResult.confidence,
        queryType: chatResult.queryType,
        chatbotVersion: chatResult.chatbotVersion,
        hasDebugInfo: !!chatResult.debugInfo,
        timestamp: new Date().toISOString()
      });
      
      // Enhanced response with extreme debugging info
      const responseData = {
        message: chatResult.response,
        confidence: chatResult.confidence,
        queryType: chatResult.queryType,
        timestamp: new Date().toISOString(),
        sessionId: sessionId,
        processingTime: chatResult.processingTime,
        chatbotVersion: chatResult.chatbotVersion || 'advanced_financial_v2.0',
        socketDebugInfo: {
          socketId: socket.id,
          transport: socket.conn.transport.name,
          totalProcessingTime: Date.now() - startTime,
          chatbotProcessingTime: chatbotEndTime - chatbotStartTime
        },
        debugInfo: chatResult.debugInfo
      };
      
      // Emit response with comprehensive debugging
      console.log('📤 WEBSOCKET DEBUG: Emitting chat response', {
        socketId: socket.id,
        responseDataKeys: Object.keys(responseData),
        messageLength: responseData.message?.length || 0,
        confidence: responseData.confidence,
        queryType: responseData.queryType,
        totalTime: Date.now() - startTime,
        timestamp: new Date().toISOString()
      });
      
      socket.emit('chat_response', responseData);
      
      // Additional debug confirmation
      console.log('🎯 WEBSOCKET DEBUG: Chat response sent successfully', {
        socketId: socket.id,
        sessionId: sessionId,
        totalProcessingTime: Date.now() - startTime,
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      console.error('💥 WEBSOCKET DEBUG: Chat processing error', {
        socketId: socket.id,
        sessionId: sessionId,
        error: error.message,
        stack: error.stack,
        errorType: error.constructor.name,
        processingTime: Date.now() - startTime,
        timestamp: new Date().toISOString()
      });
      
      const errorData = {
        error: 'Sorry, I encountered an issue processing your message. Please try again.',
        sessionId: sessionId,
        timestamp: new Date().toISOString(),
        debugInfo: {
          errorType: error.constructor.name,
          errorMessage: error.message,
          processingTime: Date.now() - startTime,
          socketId: socket.id
        }
      };
      
      console.log('📤 WEBSOCKET DEBUG: Emitting chat error', errorData);
      socket.emit('chat_error', errorData);
    }
  });
});

// Helper function to emit processing steps
  const emitStep = (sessionId, step, status, message = '') => {
    const stepData = { step, status, message, timestamp: new Date().toISOString() };
    console.log(`Step: ${sessionId} - ${step} (${status})${message ? ` - ${message}` : ''}`);
    io.to(sessionId).emit('processing_step', stepData);
  };

  const emitLog = (sessionId, logType, message, details = null) => {
    const logData = { 
      type: logType, 
      message, 
      details,
      timestamp: new Date().toISOString() 
    };
    console.log(`📝 ${logType.toUpperCase()}: ${message}`);
    io.to(sessionId).emit('processing_log', logData);
  };

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const uploadDir = path.join(__dirname, 'uploads');
    if (!fs.existsSync(uploadDir)) {
      fs.mkdirSync(uploadDir, { recursive: true });
    }
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    // Keep original filename with timestamp
    const timestamp = Date.now();
    const name = file.originalname.replace(/\.[^/.]+$/, "");
    const ext = path.extname(file.originalname);
    cb(null, `${name}_${timestamp}${ext}`);
  }
});

const upload = multer({ 
  storage: storage,
  fileFilter: (req, file, cb) => {
    if (file.mimetype === 'application/pdf') {
      cb(null, true);
    } else {
      cb(new Error('Only PDF files are allowed!'), false);
    }
  }
});

// Function to run Python script
const runPythonScript = (scriptPath, pdfPath, additionalArgs = [], sessionId = null) => {
  return new Promise((resolve, reject) => {
    const args = [scriptPath, pdfPath, ...additionalArgs];
    console.log(`Running: python3 ${args.join(' ')}`);
    
    const python = spawn('python3', args);
    
    let stdout = '';
    let stderr = '';
    
    python.stdout.on('data', (data) => {
      const output = data.toString();
      stdout += output;
      console.log(`stdout: ${output}`);
      
      // Emit real-time logs to frontend if sessionId provided
      if (sessionId) {
        const lines = output.split('\n').filter(line => line.trim());
        lines.forEach(line => {
          io.to(sessionId).emit('processing_log', {
            type: 'python_stdout',
            message: line.trim(),
            timestamp: new Date().toISOString(),
            script: path.basename(scriptPath)
          });
        });
      }
    });
    
    python.stderr.on('data', (data) => {
      const output = data.toString();
      stderr += output;
      console.error(`stderr: ${output}`);
      
      // Emit real-time error logs to frontend if sessionId provided
      if (sessionId) {
        const lines = output.split('\n').filter(line => line.trim());
        lines.forEach(line => {
          io.to(sessionId).emit('processing_log', {
            type: 'python_stderr',
            message: line.trim(),
            timestamp: new Date().toISOString(),
            script: path.basename(scriptPath)
          });
        });
      }
    });
    
    python.on('close', (code) => {
      if (code === 0) {
        resolve({ success: true, output: stdout, stderr });
      } else {
        reject({ success: false, error: stderr, code, stdout });
      }
    });
  });
};

// 🔥 EXTREME FINANCIAL CHATBOT DEBUGGING 🔥
const runPythonChatbot = (message, sessionId) => {
  return new Promise((resolve, reject) => {
    const chatbotStartTime = Date.now();
    const chatScript = '/Users/admin/gst-extractor/chatbot_interface.py';
    const args = ['python3', chatScript, message, sessionId];

    console.log('🤖 CHATBOT DEBUG: Initializing Advanced Financial Chatbot', {
      script: chatScript,
      message: message.substring(0, 100) + (message.length > 100 ? '...' : ''),
      sessionId: sessionId,
      messageLength: message.length,
      timestamp: new Date().toISOString(),
      command: args.join(' ')
    });
    
    const python = spawn(args[0], args.slice(1));
    
    let stdout = '';
    let stderr = '';
    let dataChunks = 0;
    let errorChunks = 0;
    
    python.stdout.on('data', (data) => {
      dataChunks++;
      const chunk = data.toString();
      stdout += chunk;
      
      console.log('📥 CHATBOT DEBUG: stdout chunk received', {
        chunkNumber: dataChunks,
        chunkSize: chunk.length,
        totalSize: stdout.length,
        preview: chunk.substring(0, 150) + (chunk.length > 150 ? '...' : ''),
        timestamp: new Date().toISOString()
      });
    });
    
    python.stderr.on('data', (data) => {
      errorChunks++;
      const chunk = data.toString();
      stderr += chunk;
      
      console.log('📥 CHATBOT DEBUG: stderr chunk received', {
        chunkNumber: errorChunks,
        chunkSize: chunk.length,
        totalSize: stderr.length,
        content: chunk,
        timestamp: new Date().toISOString()
      });
    });
    
    python.on('close', (code) => {
      const processingTime = Date.now() - chatbotStartTime;
      
      console.log('🏁 CHATBOT DEBUG: Process completed', {
        exitCode: code,
        processingTime: processingTime,
        stdoutSize: stdout.length,
        stderrSize: stderr.length,
        dataChunks: dataChunks,
        errorChunks: errorChunks,
        timestamp: new Date().toISOString()
      });
      
      if (code === 0) {
        try {
          console.log('🔍 CHATBOT DEBUG: Parsing response...', {
            rawStdoutLength: stdout.length,
            rawStderrLength: stderr.length,
            timestamp: new Date().toISOString()
          });
          
          // Extract JSON from the output - it should be the last complete JSON object
          const lines = stdout.trim().split('\n');
          let jsonLine = '';
          
          console.log('🔍 CHATBOT DEBUG: Searching for JSON in output', {
            totalLines: lines.length,
            lastFewLines: lines.slice(-3),
            timestamp: new Date().toISOString()
          });
          
          // Find the line that looks like JSON (starts with { and ends with })
          for (let i = lines.length - 1; i >= 0; i--) {
            const line = lines[i].trim();
            if (line.startsWith('{') && line.endsWith('}')) {
              jsonLine = line;
              console.log('✅ CHATBOT DEBUG: Found JSON line', {
                lineIndex: i,
                lineLength: line.length,
                preview: line.substring(0, 200) + (line.length > 200 ? '...' : ''),
                timestamp: new Date().toISOString()
              });
              break;
            }
          }
          
          if (!jsonLine) {
            throw new Error('No JSON found in output');
          }
          
          const result = JSON.parse(jsonLine);
          
          console.log('🎯 CHATBOT DEBUG: Successfully parsed response', {
            responseLength: result.response?.length || 0,
            confidence: result.confidence,
            queryType: result.queryType,
            sessionId: result.sessionId,
            chatbotVersion: result.chatbotVersion,
            processingTime: result.processingTime,
            hasDebugInfo: !!result.debugInfo,
            debugInfoKeys: result.debugInfo ? Object.keys(result.debugInfo) : [],
            timestamp: new Date().toISOString()
          });
          
          resolve(result);
          
        } catch (parseError) {
          console.error('💥 CHATBOT DEBUG: JSON parsing failed', {
            error: parseError.message,
            rawStdout: stdout,
            rawStderr: stderr,
            stdoutLines: stdout.split('\n').length,
            stderrLines: stderr.split('\n').length,
            processingTime: processingTime,
            timestamp: new Date().toISOString()
          });
          
          resolve({
            response: "I received your message but had trouble formatting the response. The advanced financial chatbot is active but experiencing parsing issues. Please try again.",
            confidence: 0.0,
            queryType: "parsing_error",
            chatbotVersion: "advanced_financial_v2.0",
            debugInfo: {
              parseError: parseError.message,
              stdoutLength: stdout.length,
              stderrLength: stderr.length,
              processingTime: processingTime
            }
          });
        }
      } else {
        console.error('💥 CHATBOT DEBUG: Process failed', {
          exitCode: code,
          stderr: stderr,
          stdout: stdout,
          processingTime: processingTime,
          timestamp: new Date().toISOString()
        });
        
        reject({
          error: `Advanced Financial Chatbot process failed with code ${code}: ${stderr}`,
          response: "The advanced financial chatbot is currently unavailable. Please try again later.",
          confidence: 0.0,
          queryType: "system_error",
          chatbotVersion: "advanced_financial_v2.0",
          debugInfo: {
            exitCode: code,
            stderr: stderr,
            processingTime: processingTime
          }
        });
      }
    });
    
    // Enhanced timeout handling
    const timeout = setTimeout(() => {
      console.error('⏰ CHATBOT DEBUG: Process timeout', {
        processingTime: Date.now() - chatbotStartTime,
        sessionId: sessionId,
        messageLength: message.length,
        stdoutSoFar: stdout.length,
        stderrSoFar: stderr.length,
        timestamp: new Date().toISOString()
      });
      
      python.kill('SIGKILL');
      reject({
        error: "Advanced Financial Chatbot response timeout",
        response: "The financial analysis is taking longer than expected. Please try a simpler question or try again later.",
        confidence: 0.0,
        queryType: "timeout_error",
        chatbotVersion: "advanced_financial_v2.0",
        debugInfo: {
          timeoutAfter: Date.now() - chatbotStartTime,
          stdoutLength: stdout.length,
          stderrLength: stderr.length
        }
      });
    }, 45000); // Extended to 45 seconds for complex analysis
    
    // Clear timeout on successful completion
    python.on('close', () => {
      clearTimeout(timeout);
    });
  });
};

// OCR processing endpoint with real-time updates
app.post('/api/process-pdf', upload.single('pdf'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No PDF file uploaded' });
    }

    const pdfPath = req.file.path;
    const filename = req.file.filename;
    const sessionId = req.query.sessionId || 'default';
    
    console.log(`Processing PDF: ${filename} (Session: ${sessionId})`);
    
    emitStep(sessionId, 'File Upload', 'completed', `Uploaded ${req.file.originalname}`);
    
    const results = {
      filename: req.file.originalname,
      uploadedFile: pdfPath,
      textract: null,
      tesseract: null,
      dualAI: null,
      errors: [],
      sessionId
    };

    // Step 1: Run Textract analysis
    try {
      emitStep(sessionId, 'AWS Textract Analysis', 'processing', 'Running AWS Textract OCR...');
      
      console.log('Running Textract analysis...');
      const textractScript = '/Users/admin/gst-extractor/textract_analyzer.py';
      const textractResult = await runPythonScript(textractScript, pdfPath, [], sessionId);
      
            // Look for generated Textract files (try both simple and timestamped naming)
      const originalName = path.basename(filename, '.pdf');
      // Match the exact cleaning logic from textract_analyzer.py
      const cleanName = originalName.split('').filter(c => /[a-zA-Z0-9_-]/.test(c)).join('');
      
      console.log(`🔍 TEXTRACT FILE SEARCH DEBUG:`);
      console.log(`   Original filename: ${filename}`);
      console.log(`   Extracted basename: ${originalName}`);
      console.log(`   Clean name: ${cleanName}`);
      
      // Check in current directory and parent directory
      const searchDirs = [
        __dirname,
        '/Users/admin/gst-extractor',
        path.dirname(pdfPath)
      ];
      
      console.log(`   Search directories: ${JSON.stringify(searchDirs)}`);
      
      let found = false;
      for (let i = 0; i < searchDirs.length; i++) {
        const dir = searchDirs[i];
        console.log(`\n   📂 Searching directory ${i + 1}/${searchDirs.length}: ${dir}`);
        
        if (fs.existsSync(dir)) {
          const files = fs.readdirSync(dir);
          console.log(`      Total files in directory: ${files.length}`);
          
          // Show all files that start with 'textract_analysis'
          const textractRelatedFiles = files.filter(f => f.startsWith('textract_analysis'));
          console.log(`      Textract-related files found: ${textractRelatedFiles.length}`);
          textractRelatedFiles.forEach((file, idx) => {
            console.log(`        ${idx + 1}. ${file}`);
          });
          
          // First try simplified naming (preferred)
          const expectedFile = `textract_analysis_${cleanName}.json`;
          console.log(`      Looking for simplified name: ${expectedFile}`);
          
          if (files.includes(expectedFile)) {
            results.textract = path.join(dir, expectedFile);
            found = true;
            console.log(`      ✅ FOUND (simple naming): ${results.textract}`);
            break;
          } else {
            console.log(`      ❌ Simplified name not found`);
          }
          
          // Fallback 1: look for timestamped files with clean name
          console.log(`      Looking for timestamped pattern: textract_analysis_${cleanName}_*.json`);
          let textractFiles = files.filter(f => 
            f.startsWith(`textract_analysis_${cleanName}_`) && f.endsWith('.json')
          );
          
          console.log(`      Matching timestamped files (clean name): ${textractFiles.length}`);
          textractFiles.forEach((file, idx) => {
            console.log(`        ${idx + 1}. ${file}`);
          });
          
          // Fallback 2: If clean name doesn't work, try original name variations
          if (textractFiles.length === 0) {
            console.log(`      Trying original name pattern: textract_analysis_${originalName}_*.json`);
            textractFiles = files.filter(f => 
              f.startsWith(`textract_analysis_${originalName}_`) && f.endsWith('.json')
            );
            console.log(`      Matching timestamped files (original name): ${textractFiles.length}`);
          }
          
          // Fallback 3: More flexible pattern matching for very long/complex filenames
          if (textractFiles.length === 0) {
            console.log(`      Trying flexible pattern matching for long filenames`);
            // Look for any textract file that contains parts of our filename
            const baseNameParts = originalName.replace(/[^a-zA-Z0-9]/g, '').toLowerCase();
            textractFiles = files.filter(f => {
              if (!f.startsWith('textract_analysis_') || !f.endsWith('.json')) return false;
              const fileBasePart = f.replace('textract_analysis_', '').replace(/[^a-zA-Z0-9]/g, '').toLowerCase();
              // Check if significant portion of the filename matches
              return baseNameParts.length > 8 && fileBasePart.includes(baseNameParts.substring(0, Math.min(12, baseNameParts.length)));
            });
            console.log(`      Matching files (flexible pattern): ${textractFiles.length}`);
            textractFiles.forEach((file, idx) => {
              console.log(`        ${idx + 1}. ${file}`);
            });
          }
          
          if (textractFiles.length > 0) {
            // Get the most recent file
            const mostRecent = textractFiles.sort().pop();
            results.textract = path.join(dir, mostRecent);
            found = true;
            console.log(`      ✅ FOUND (timestamped): ${results.textract}`);
            break;
          } else {
            console.log(`      ❌ No timestamped files found`);
          }
        } else {
          console.log(`      ❌ Directory does not exist: ${dir}`);
        }
      }
      
      console.log(`\n🎯 SEARCH RESULT: ${found ? 'SUCCESS' : 'FAILED'}`);
      if (found) {
        console.log(`   Final file path: ${results.textract}`);
      } else {
        console.log(`   ❌ No Textract file found in any directory`);
      }
      
      if (found) {
        emitStep(sessionId, 'AWS Textract Analysis', 'completed', `Saved to: ${path.basename(results.textract)}`);
      } else {
        results.errors.push('Textract: Output file not found after processing');
        console.log('Textract stdout:', textractResult.output);
        emitStep(sessionId, 'AWS Textract Analysis', 'error', 'Output file not found');
      }
      
    } catch (error) {
      console.error('Textract error:', error);
      results.errors.push(`Textract failed: ${error.error || error.message}`);
      if (error.stdout) console.log('Textract stdout:', error.stdout);
      emitStep(sessionId, 'AWS Textract Analysis', 'error', error.error || error.message);
    }

    // Step 2: Run Tesseract OCR
    try {
      emitStep(sessionId, 'Tesseract OCR Analysis', 'processing', 'Running Tesseract OCR...');
      
      console.log('Running Tesseract OCR...');
      const tesseractScript = '/Users/admin/gst-extractor/tesseract_ocr.py';
      
      // Generate output base name for tesseract (simplified)
      const originalName = path.basename(filename, '.pdf');
      const cleanName = originalName.replace(/[^a-zA-Z0-9]/g, '_');
      const outputBase = path.join('/Users/admin/gst-extractor', `${cleanName}_ocr`);
      
      const tesseractResult = await runPythonScript(tesseractScript, pdfPath, ['--output', outputBase], sessionId);
      
      // Check for generated files with simplified naming
      const expectedJsonFile = `${outputBase}.json`;
      const expectedTxtFile = `${outputBase}.txt`;
      
      if (fs.existsSync(expectedJsonFile)) {
        results.tesseract = expectedJsonFile;
        console.log(`✅ Tesseract JSON file found: ${results.tesseract}`);
        
        if (fs.existsSync(expectedTxtFile)) {
          results.tesseract_txt = expectedTxtFile;
          console.log(`✅ Tesseract TXT file found: ${results.tesseract_txt}`);
        }
        
        emitStep(sessionId, 'Tesseract OCR Analysis', 'completed', `Saved to: ${path.basename(results.tesseract)}`);
      } else {
        results.errors.push('Tesseract: JSON output file not found');
        console.log('Tesseract stdout:', tesseractResult.output);
        
        // Check if the script said "no" (meaning dependencies missing)
        if (tesseractResult.output && tesseractResult.output.trim().startsWith('no')) {
          results.errors.push('Tesseract: Dependencies not available (tesseract or poppler missing)');
          emitStep(sessionId, 'Tesseract OCR Analysis', 'error', 'Dependencies missing (tesseract/poppler)');
        } else {
          emitStep(sessionId, 'Tesseract OCR Analysis', 'error', 'JSON output file not found');
        }
      }
      
    } catch (error) {
      console.error('Tesseract error:', error);
      results.errors.push(`Tesseract failed: ${error.error || error.message}`);
      if (error.stdout) console.log('Tesseract stdout:', error.stdout);
      emitStep(sessionId, 'Tesseract OCR Analysis', 'error', error.error || error.message);
    }

    // Step 3: Run Dual Input AI Agent (if both OCR methods succeeded)
    if (results.textract && results.tesseract) {
      try {
        emitStep(sessionId, 'Dual AI Agent Processing', 'processing', 'Running intelligent invoice analysis...');
        
        console.log('Running Dual Input AI Agent...');
        const dualAIScript = '/Users/admin/gst-extractor/dual_input_ai_agent.py';
        const aiResult = await runPythonScript(dualAIScript, results.textract, [results.tesseract], sessionId);
        
        // The dual AI agent doesn't create a specific output file, but processes data into database
        results.dualAI = {
          status: 'completed',
          textract_input: results.textract,
          tesseract_input: results.tesseract,
          processing_log: aiResult.output || 'Processing completed'
        };
        
        emitStep(sessionId, 'Dual AI Agent Processing', 'completed', 'Invoice analysis completed with database storage');
        
        console.log('✅ Dual Input AI Agent completed successfully');
        
        // Parse AI output for structured results and always include processing_log
        try {
          const outputLines = aiResult.output.split('\n');
          const jsonLine = outputLines.find(line => line.trim().startsWith('{') && line.trim().endsWith('}'));
            if (jsonLine) {
            const parsedResult = JSON.parse(jsonLine.trim());
            // Always include the full processing log
            parsedResult.processing_log = aiResult.output;
            parsedResult.textract_input = results.textract;
            parsedResult.tesseract_input = results.tesseract;
            
            // Step 4: Generate Database Insertion Report
            if (parsedResult.database_ids) {
              try {
                emitStep(sessionId, 'Database Report Generation', 'processing', 'Generating detailed database insertion report...');
                
                console.log('🗃️ Running Database Reporter...');
                const dbReporterScript = '/Users/admin/gst-extractor/database_reporter.py';
                const dbIds = JSON.stringify(parsedResult.database_ids);
                const dbReporterResult = await runPythonScript(dbReporterScript, dbIds, [], sessionId);
                
                // Parse database report
                try {
                  const dbReportLines = dbReporterResult.output.split('\n');
                  const dbJsonLine = dbReportLines.find(line => line.trim().startsWith('{'));
                  if (dbJsonLine) {
                    const dbReport = JSON.parse(dbJsonLine.trim());
                    parsedResult.database_report = dbReport;
                    // Also attach the report to the HTTP response payload so API callers receive it
                    try {
                      results.database_report = dbReport;
                      if (parsedResult.database_ids) results.database_ids = parsedResult.database_ids;
                    } catch (e) {
                      console.warn('Could not attach database_report to results object:', e.message || e);
                    }
                    console.log('✅ Database report generated successfully');
                    emitStep(sessionId, 'Database Report Generation', 'completed', `Report covers ${dbReport.summary.total_tables_affected} tables with ${dbReport.summary.total_records_inserted} records`);
                  }
                } catch (dbParseError) {
                  console.log('Could not parse database report, including raw output');
                    parsedResult.database_report = {
                    raw_output: dbReporterResult.output,
                    parse_error: dbParseError.message
                  };
                    try {
                      results.database_report = parsedResult.database_report;
                      if (parsedResult.database_ids) results.database_ids = parsedResult.database_ids;
                    } catch (e) {
                      console.warn('Could not attach raw database_report to results object:', e.message || e);
                    }
                  emitStep(sessionId, 'Database Report Generation', 'completed', 'Report generated (raw format)');
                }
              } catch (dbError) {
                console.error('Database Reporter error:', dbError);
                parsedResult.database_report = {
                  error: `Database report failed: ${dbError.error || dbError.message}`,
                  fallback_ids: parsedResult.database_ids
                };
                try {
                  results.database_report = parsedResult.database_report;
                  if (parsedResult.database_ids) results.database_ids = parsedResult.database_ids;
                } catch (e) {
                  console.warn('Could not attach failed database_report to results object:', e.message || e);
                }
                emitStep(sessionId, 'Database Report Generation', 'error', 'Report generation failed');
              }
            }
            
            io.to(sessionId).emit('dual_ai_complete', parsedResult);
          } else {
            // No JSON found, send everything as raw output with processing_log
            io.to(sessionId).emit('dual_ai_complete', {
              success: true,
              processing_log: aiResult.output,
              textract_input: results.textract,
              tesseract_input: results.tesseract
            });
          }
        } catch (parseError) {
          console.log('Could not parse AI result as JSON, sending raw output with full log');
          io.to(sessionId).emit('dual_ai_complete', {
            success: true,
            processing_log: aiResult.output,
            textract_input: results.textract,
            tesseract_input: results.tesseract,
            parse_error: parseError.message
          });
        }
        
      } catch (error) {
        console.error('Dual AI error:', error);
        results.errors.push(`Dual AI Agent failed: ${error.error || error.message}`);
        if (error.stdout) console.log('Dual AI stdout:', error.stdout);
        
        emitStep(sessionId, 'Dual AI Agent Processing', 'error', error.error || error.message);
        io.to(sessionId).emit('processing_error', { error: `Dual AI processing failed: ${error.error || error.message}` });
      }
    } else {
      emitStep(sessionId, 'Dual AI Agent Processing', 'error', 'Skipped - missing OCR results');
      const errorMsg = 'Cannot run AI analysis - missing OCR results';
      io.to(sessionId).emit('processing_error', { error: errorMsg });
    }
    
    // Final completion
    io.emit('processing-update', {
      sessionId,
      step: 'complete',
      message: 'All processing completed!',
      progress: 100,
      results: results
    });

    console.log('Processing complete:', results);
    res.json(results);

  } catch (error) {
    console.error('Processing error:', error);
    res.status(500).json({ 
      error: 'Processing failed', 
      details: error.message 
    });
  }
});

// Dashboard API Endpoints
app.get('/api/dashboard/metrics', async (req, res) => {
  try {
    const dashboardScript = '/Users/admin/gst-extractor/dashboard_service.py';
    const result = await runPythonScript(dashboardScript, 'metrics', []);
    
    const outputLines = result.output.split('\n');
    const jsonLine = outputLines.find(line => line.trim().startsWith('{'));
    if (jsonLine) {
      const metricsData = JSON.parse(jsonLine.trim());
      res.json(metricsData);
    } else {
      res.json({
        totalDocuments: 0,
        activeCompanies: 0,
        totalRevenue: 0,
        recentInvoices: 0,
        validationRate: 0
      });
    }
  } catch (error) {
    console.error('Dashboard metrics error:', error);
    res.status(500).json({ error: 'Failed to fetch metrics' });
  }
});

app.get('/api/dashboard/invoices/recent', async (req, res) => {
  try {
    const dashboardScript = '/Users/admin/gst-extractor/dashboard_service.py';
    const result = await runPythonScript(dashboardScript, 'recent_invoices', []);
    
    const outputLines = result.output.split('\n');
    const jsonLine = outputLines.find(line => line.trim().startsWith('['));
    if (jsonLine) {
      const invoicesData = JSON.parse(jsonLine.trim());
      res.json(invoicesData);
    } else {
      res.json([]);
    }
  } catch (error) {
    console.error('Dashboard recent invoices error:', error);
    res.status(500).json({ error: 'Failed to fetch recent invoices' });
  }
});

app.get('/api/dashboard/companies/top', async (req, res) => {
  try {
    const dashboardScript = '/Users/admin/gst-extractor/dashboard_service.py';
    const result = await runPythonScript(dashboardScript, 'top_companies', []);
    
    const outputLines = result.output.split('\n');
    const jsonLine = outputLines.find(line => line.trim().startsWith('['));
    if (jsonLine) {
      const companiesData = JSON.parse(jsonLine.trim());
      res.json(companiesData);
    } else {
      res.json([]);
    }
  } catch (error) {
    console.error('Dashboard top companies error:', error);
    res.status(500).json({ error: 'Failed to fetch top companies' });
  }
});

app.get('/api/dashboard/revenue/trends', async (req, res) => {
  try {
    const dashboardScript = '/Users/admin/gst-extractor/dashboard_service.py';
    const result = await runPythonScript(dashboardScript, 'revenue_trends', []);
    
    const outputLines = result.output.split('\n');
    const jsonLine = outputLines.find(line => line.trim().startsWith('['));
    if (jsonLine) {
      const revenueData = JSON.parse(jsonLine.trim());
      res.json(revenueData);
    } else {
      res.json([]);
    }
  } catch (error) {
    console.error('Dashboard revenue trends error:', error);
    res.status(500).json({ error: 'Failed to fetch revenue trends' });
  }
});

app.get('/api/dashboard/compliance', async (req, res) => {
  try {
    const dashboardScript = '/Users/admin/gst-extractor/dashboard_service.py';
    const result = await runPythonScript(dashboardScript, 'compliance', []);
    
    const outputLines = result.output.split('\n');
    const jsonLine = outputLines.find(line => line.trim().startsWith('{'));
    if (jsonLine) {
      const complianceData = JSON.parse(jsonLine.trim());
      res.json(complianceData);
    } else {
      res.json({
        total_companies: 0,
        with_gstin: 0,
        validation_success: 0,
        duplicate_detection: 0
      });
    }
  } catch (error) {
    console.error('Dashboard compliance error:', error);
    res.status(500).json({ error: 'Failed to fetch compliance data' });
  }
});

// PDF Report Generation endpoint
app.post('/api/generate-pdf-report', async (req, res) => {
  try {
    const { results, dualAIResults, processingSteps } = req.body;

    // Call the Python PDF generator script
    const pdfScript = '/Users/admin/gst-extractor/pdf_report_generator.py';
    
    // Create temporary JSON file with the data
    const tempDataFile = path.join(__dirname, 'temp_report_data.json');
    const reportData = {
      results,
      dualAIResults,
      processingSteps,
      generated_at: new Date().toISOString()
    };
    
    fs.writeFileSync(tempDataFile, JSON.stringify(reportData, null, 2));

    try {
      // Run the PDF generator
      const pdfResult = await runPythonScript(pdfScript, tempDataFile, [], sessionId);
      
      // Look for generated PDF file
      const expectedPdfFile = tempDataFile.replace('.json', '_report.pdf');
      
      if (fs.existsSync(expectedPdfFile)) {
        // Send the PDF file
        res.setHeader('Content-Type', 'application/pdf');
        res.setHeader('Content-Disposition', 'attachment; filename="processing-report.pdf"');
        
        const pdfBuffer = fs.readFileSync(expectedPdfFile);
        res.send(pdfBuffer);
        
        // Cleanup
        fs.unlinkSync(tempDataFile);
        fs.unlinkSync(expectedPdfFile);
      } else {
        throw new Error('PDF file not generated');
      }
      
    } catch (error) {
      console.error('PDF generation error:', error);
      
      // Fallback: create a simple text-based report
      const textReport = `
PDF OCR Processing Report
========================
Generated: ${new Date().toLocaleString()}

File: ${results?.filename || 'N/A'}
Textract Output: ${results?.textract || 'N/A'}
Tesseract Output: ${results?.tesseract || 'N/A'}

Processing Steps:
${processingSteps?.map(step => `- ${step.step}: ${step.status}`).join('\n') || 'None'}

AI Analysis Results:
${dualAIResults ? JSON.stringify(dualAIResults, null, 2) : 'No AI results available'}
      `;
      
      res.setHeader('Content-Type', 'text/plain');
      res.setHeader('Content-Disposition', 'attachment; filename="processing-report.txt"');
      res.send(textReport);
    }
    
    // Cleanup temp file
    try {
      fs.unlinkSync(tempDataFile);
    } catch (e) {
      // Ignore cleanup errors
    }

  } catch (error) {
    console.error('Report generation error:', error);
    res.status(500).json({ 
      error: 'Failed to generate report', 
      details: error.message 
    });
  }
});

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

// File content endpoint to serve JSON files for document contents
app.get('/api/file-content', (req, res) => {
  try {
    const filePath = req.query.path;
    if (!filePath) {
      return res.status(400).json({ error: 'File path is required' });
    }

    // Security check - only allow files in the workspace directory
    const workspaceDir = path.resolve('/Users/admin/gst-extractor');
    const requestedPath = path.resolve(filePath);
    
    if (!requestedPath.startsWith(workspaceDir)) {
      return res.status(403).json({ error: 'Access to file outside workspace is forbidden' });
    }

    // Check if file exists
    if (!fs.existsSync(requestedPath)) {
      return res.status(404).json({ error: 'File not found' });
    }

    // Read and return file content
    const fileContent = fs.readFileSync(requestedPath, 'utf8');
    
    // Try to parse as JSON, otherwise return as text
    try {
      const jsonContent = JSON.parse(fileContent);
      res.json(jsonContent);
    } catch (parseError) {
      res.json({ text: fileContent, type: 'text' });
    }
  } catch (error) {
    console.error('Error serving file content:', error);
    res.status(500).json({ error: 'Failed to read file content' });
  }
});

server.listen(PORT, () => {
  console.log(`🚀 OCR Server running on http://localhost:${PORT}`);
  console.log(`📁 Upload directory: ${path.join(__dirname, 'uploads')}`);
  console.log(`🔌 Socket.IO enabled for real-time updates`);
});