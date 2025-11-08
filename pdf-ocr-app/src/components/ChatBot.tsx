import React, { useState, useEffect, useRef } from 'react';
import { Socket } from 'socket.io-client';
import './ChatBot.css';

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  message: string;
  timestamp: string;
  confidence?: number;
  queryType?: string;
}

interface ChatBotProps {
  socket: Socket | null;
  connected?: boolean;
}

const ChatBot: React.FC<ChatBotProps> = ({ socket, connected = false }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [sessionId] = useState(`chat_${Date.now()}`);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 🔥 EXTREME SOCKET.IO EVENT DEBUGGING 🔥
  useEffect(() => {
    console.log('� CHATBOT DEBUG: Socket event setup initiated', {
      hasSocket: !!socket,
      socketConnected: socket?.connected,
      socketId: socket?.id,
      timestamp: new Date().toISOString()
    });

    if (!socket) {
      console.log('💀 CHATBOT DEBUG: No socket available in useEffect');
      return;
    }

    console.log('✅ CHATBOT DEBUG: Setting up extreme event monitoring');

    // 🔥 CHAT RESPONSE DEBUGGING 🔥
    socket.on('chat_response', (data: {
      message: string;
      confidence?: number;
      queryType?: string;
      timestamp: string;
      sessionId?: string;
      processingTime?: number;
      chatbotVersion?: string;
      socketDebugInfo?: any;
      debugInfo?: any;
    }) => {
      console.log('📥 CHATBOT DEBUG: chat_response event received', {
        dataKeys: Object.keys(data),
        messageLength: data.message?.length || 0,
        confidence: data.confidence,
        queryType: data.queryType,
        sessionId: data.sessionId,
        processingTime: data.processingTime,
        chatbotVersion: data.chatbotVersion,
        hasSocketDebugInfo: !!data.socketDebugInfo,
        hasDebugInfo: !!data.debugInfo,
        timestamp: new Date().toISOString()
      });
      
      setIsTyping(false);
      setMessages(prev => [...prev, {
        id: `assistant_${Date.now()}`,
        type: 'assistant',
        message: data.message,
        timestamp: data.timestamp,
        confidence: data.confidence,
        queryType: data.queryType
      }]);
      
      console.log('✅ CHATBOT DEBUG: Message added to chat interface');
    });

    // 🔥 CHAT ERROR DEBUGGING 🔥
    socket.on('chat_error', (data: { 
      error: string; 
      sessionId?: string; 
      debugInfo?: any; 
      timestamp?: string; 
    }) => {
      console.error('💥 CHATBOT DEBUG: chat_error event received', {
        error: data.error,
        sessionId: data.sessionId,
        hasDebugInfo: !!data.debugInfo,
        debugInfo: data.debugInfo,
        timestamp: data.timestamp || new Date().toISOString()
      });
      
      setIsTyping(false);
      setMessages(prev => [...prev, {
        id: `error_${Date.now()}`,
        type: 'assistant',
        message: `❌ Error: ${data.error}`,
        timestamp: data.timestamp || new Date().toISOString()
      }]);
    });

    // 🔥 TYPING INDICATOR DEBUGGING 🔥
    socket.on('chat_typing', (data?: any) => {
      console.log('💭 CHATBOT DEBUG: chat_typing event received', {
        data: data,
        timestamp: new Date().toISOString()
      });
      setIsTyping(true);
    });

    // 🔥 ADVANCED CONNECTION MONITORING 🔥
    socket.on('connect', () => {
      console.log('🎯 CHATBOT DEBUG: Socket reconnected in chatbot', {
        socketId: socket.id,
        timestamp: new Date().toISOString()
      });
    });

    socket.on('disconnect', (reason) => {
      console.log('💔 CHATBOT DEBUG: Socket disconnected in chatbot', {
        reason: reason,
        timestamp: new Date().toISOString()
      });
    });

    // Cleanup function with extreme debugging
    return () => {
      console.log('🧹 CHATBOT DEBUG: Cleaning up socket event listeners', {
        socketId: socket?.id,
        timestamp: new Date().toISOString()
      });
      
      socket.off('chat_response');
      socket.off('chat_error');
      socket.off('chat_typing');
      socket.off('connect');
      socket.off('disconnect');
    };
  }, [socket]);

  // Welcome message
  useEffect(() => {
    const welcomeMessage: ChatMessage = {
      id: 'welcome',
      type: 'assistant',
      message: `🏦 **Financial Assistant Ready!**

I can help you with:
📊 Invoice analysis and search
🏢 Company & GST validation  
📦 Product & HSN code lookup
💰 Financial reporting & trends
✅ Data validation & compliance
💳 Payment tracking & status

Try asking:
• "Show me all invoices from last month"
• "Find company details for GSTIN 24AAXFA5297L1ZN"
• "What's the total tax amount?"
• "Validate GSTIN format"

Type your question below! 👇`,
      timestamp: new Date().toISOString()
    };
    setMessages([welcomeMessage]);
  }, []);

  const handleSendMessage = async () => {
    const sendStartTime = Date.now();
    
    console.log('� CHATBOT DEBUG: Send message initiated', {
      inputMessage: inputMessage.trim(),
      messageLength: inputMessage.trim().length,
      hasSocket: !!socket,
      socketConnected: socket?.connected,
      socketId: socket?.id,
      sessionId: sessionId,
      timestamp: new Date().toISOString()
    });

    if (!inputMessage.trim()) {
      console.log('❌ CHATBOT DEBUG: Empty message, aborting send');
      return;
    }

    if (!socket) {
      console.log('💀 CHATBOT DEBUG: No socket connection available');
      setMessages(prev => [...prev, {
        id: `error_${Date.now()}`,
        type: 'assistant',
        message: '❌ Connection Error: No socket connection available. Please refresh the page.',
        timestamp: new Date().toISOString()
      }]);
      return;
    }

    if (!socket.connected) {
      console.log('💀 CHATBOT DEBUG: Socket not connected');
      setMessages(prev => [...prev, {
        id: `error_${Date.now()}`,
        type: 'assistant',
        message: '❌ Connection Error: Socket not connected. Please wait for reconnection or refresh the page.',
        timestamp: new Date().toISOString()
      }]);
      return;
    }

    const userMessage: ChatMessage = {
      id: `user_${Date.now()}`,
      type: 'user',
      message: inputMessage.trim(),
      timestamp: new Date().toISOString()
    };

    console.log('✅ CHATBOT DEBUG: Adding user message to interface', {
      messageId: userMessage.id,
      messageLength: userMessage.message.length,
      timestamp: userMessage.timestamp
    });
    
    setMessages(prev => [...prev, userMessage]);
    setIsTyping(true);

    // Send message via Socket.IO with extreme debugging
    const messageData = {
      message: inputMessage.trim(),
      sessionId: sessionId,
      clientTimestamp: new Date().toISOString(),
      debugMode: 'EXTREME'
    };
    
    console.log('📤 CHATBOT DEBUG: Emitting chat_message event', {
      eventName: 'chat_message',
      messageData: messageData,
      socketId: socket.id,
      transport: (socket as any).io?.engine?.transport?.name,
      socketConnected: socket.connected,
      sendTime: Date.now() - sendStartTime,
      timestamp: new Date().toISOString()
    });
    
    try {
      socket.emit('chat_message', messageData);
      console.log('✅ CHATBOT DEBUG: chat_message event emitted successfully');
    } catch (error) {
      console.error('💥 CHATBOT DEBUG: Failed to emit chat_message', {
        error: error,
        timestamp: new Date().toISOString()
      });
    }

    setInputMessage('');
    inputRef.current?.focus();
    
    console.log('🏁 CHATBOT DEBUG: Send message completed', {
      totalTime: Date.now() - sendStartTime,
      timestamp: new Date().toISOString()
    });
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatMessage = (message: string) => {
    // Convert markdown-style formatting to HTML
    return message
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br />');
  };

  const clearChat = () => {
    setMessages([{
      id: 'welcome',
      type: 'assistant',
      message: '🗑️ Chat cleared! How can I help you with your financial data?',
      timestamp: new Date().toISOString()
    }]);
  };

  return (
    <div className={`chatbot-container ${isMinimized ? 'minimized' : ''}`}>
      {/* Header */}
      <div className="chatbot-header">
        <div className="header-left">
          <div className="bot-avatar">🤖</div>
          <div className="header-info">
            <h3>Financial Assistant</h3>
            <span className="status">
              {isTyping ? '💭 Thinking...' : '🟢 Online'}
            </span>
            <div style={{fontSize: '0.7rem', color: 'rgba(255,255,255,0.8)'}}>
              Socket: {connected ? '✅ Connected' : '❌ Disconnected'}
            </div>
          </div>
        </div>
        <div className="header-actions">
          <button 
            className="clear-btn"
            onClick={() => {
              console.log('🧪 TEST: Socket test button clicked');
              if (socket) {
                console.log('🧪 TEST: Socket exists, sending test message');
                socket.emit('chat_message', {
                  message: 'test',
                  sessionId: sessionId
                });
              } else {
                console.log('🧪 TEST: No socket connection');
              }
            }}
            title="Test Socket"
          >
            🧪
          </button>
          <button 
            className="clear-btn"
            onClick={clearChat}
            title="Clear Chat"
          >
            🗑️
          </button>
          <button 
            className="minimize-btn"
            onClick={() => setIsMinimized(!isMinimized)}
            title={isMinimized ? 'Expand' : 'Minimize'}
          >
            {isMinimized ? '⬆️' : '⬇️'}
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="chatbot-messages">
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.type}`}>
            <div className="message-content">
              <div 
                className="message-text"
                dangerouslySetInnerHTML={{
                  __html: formatMessage(msg.message)
                }}
              />
              <div className="message-meta">
                <span className="timestamp">
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </span>
                {msg.confidence && (
                  <span className="confidence">
                    🎯 {Math.round(msg.confidence * 100)}%
                  </span>
                )}
                {msg.queryType && (
                  <span className="query-type">
                    📋 {msg.queryType}
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
        
        {isTyping && (
          <div className="message assistant typing">
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="chatbot-input">
        <div className="input-container">
          <input
            ref={inputRef}
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about your financial data..."
            disabled={isTyping}
            className="message-input"
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isTyping}
            className="send-button"
          >
            {isTyping ? '⏳' : '➤'}
          </button>
        </div>
        <div className="input-hint">
          💡 Try: "Show me recent invoices" or "Validate GSTIN"
        </div>
      </div>
    </div>
  );
};

export default ChatBot;