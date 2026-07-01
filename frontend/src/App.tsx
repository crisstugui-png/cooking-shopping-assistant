import React, { useState, useEffect, useRef } from 'react';
import './App.css';

interface Message {
  id: string;
  sender: 'user' | 'model' | 'system';
  text: string;
  image?: string; // Base64 data URL for preview
  isWarning?: boolean;
}

interface ShoppingItem {
  name: string;
  price: number;
  quantity?: number;
}

interface PurchaseRecord {
  date: string;
  items: ShoppingItem[];
}

function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      sender: 'model',
      text: "Hello! I am your personal cooking, shopping, and budget assistant. How can I help you today?\n\n- Suggest recipes or plan a menu\n- Log new shopping trips (attach receipt/meal photos)\n- Query expense history"
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const [userId] = useState('default-user');

  // Image Upload States
  const [attachedImage, setAttachedImage] = useState<File | null>(null);
  const [attachedImagePreview, setAttachedImagePreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Split Panel Tab States
  const [shoppingList, setShoppingList] = useState('');
  const [shoppingHistory, setShoppingHistory] = useState<PurchaseRecord[]>([]);
  const [activeTab, setActiveTab] = useState<'shopping-list' | 'shopping-history' | 'receipts-log'>('shopping-list');
  const [uploadedReceipts, setUploadedReceipts] = useState<string[]>([]);

  // Hijacking Guardrail (Interrupt) States
  const [pendingInterrupt, setPendingInterrupt] = useState<{ id: string; message: string } | null>(null);

  // Feedback States
  const [ratedMessages, setRatedMessages] = useState<Record<string, 'up' | 'down'>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Create session on the backend
  const createBackendSession = async (sessId: string) => {
    try {
      await fetch(`/api/apps/app/users/${userId}/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sessionId: sessId })
      });
    } catch (err) {
      console.error("Error creating backend session:", err);
    }
  };

  // Initialize or fetch session
  useEffect(() => {
    let sessId = localStorage.getItem('assistant_session_id');
    if (!sessId) {
      sessId = 'session_' + Math.random().toString(36).substring(2, 15);
      localStorage.setItem('assistant_session_id', sessId);
    }
    setSessionId(sessId);
    createBackendSession(sessId);
    refreshAssets();
  }, []);

  // Poll assets periodically to ensure real-time updates when files change
  useEffect(() => {
    const interval = setInterval(() => {
      refreshAssets();
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const resetSession = () => {
    const sessId = 'session_' + Math.random().toString(36).substring(2, 15);
    localStorage.setItem('assistant_session_id', sessId);
    setSessionId(sessId);
    createBackendSession(sessId);
    setMessages([
      {
        id: 'welcome',
        sender: 'model',
        text: "Hello! I am your personal cooking, shopping, and budget assistant. How can I help you today?\n\n- Suggest recipes or plan a menu\n- Log new shopping trips (attach receipt/meal photos)\n- Query expense history"
      }
    ]);
    setPendingInterrupt(null);
    setAttachedImage(null);
    setAttachedImagePreview(null);
    refreshAssets();
  };

  const refreshAssets = async () => {
    try {
      const listRes = await fetch('/api/shopping-list');
      if (listRes.ok) {
        const text = await listRes.text();
        setShoppingList(text);
      }
      const histRes = await fetch('/api/shopping-history');
      if (histRes.ok) {
        const data = await histRes.json();
        setShoppingHistory(data);
      }
      const receiptsRes = await fetch('/api/uploaded-receipts');
      if (receiptsRes.ok) {
        const data = await receiptsRes.json();
        setUploadedReceipts(data);
      }
    } catch (err) {
      console.error("Failed to load list/history/receipts assets:", err);
    }
  };

  const handleCheckboxToggle = async (lineIndex: number) => {
    const lines = shoppingList.split('\n');
    const line = lines[lineIndex];
    if (line.startsWith('- [ ] ')) {
      lines[lineIndex] = '- [x] ' + line.substring(6);
    } else if (line.startsWith('- [x] ')) {
      lines[lineIndex] = '- [ ] ' + line.substring(6);
    }
    const newContent = lines.join('\n');
    setShoppingList(newContent);

    try {
      await fetch('/api/shopping-list', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: newContent })
      });
    } catch (err) {
      console.error("Failed to save updated shopping list:", err);
    }
  };

  // Convert File to Base64 (strips MIME prefix for raw bytes)
  const convertToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        const result = reader.result as string;
        const base64Data = result.split(',')[1];
        resolve(base64Data);
      };
      reader.onerror = (error) => reject(error);
    });
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setAttachedImage(file);
      setAttachedImagePreview(URL.createObjectURL(file));
    }
  };

  const clearAttachedImage = () => {
    setAttachedImage(null);
    setAttachedImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Send user message
  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputText.trim() && !attachedImage) return;

    const userText = inputText;
    const imgPreview = attachedImagePreview || undefined;
    const imgFile = attachedImage;

    // Append user message immediately
    const userMsgId = 'msg_' + Date.now();
    setMessages(prev => [
      ...prev,
      {
        id: userMsgId,
        sender: 'user',
        text: userText,
        image: imgPreview
      }
    ]);

    setInputText('');
    clearAttachedImage();
    setLoading(true);

    try {
      let parts: any[] = [];
      let base64String = '';
      if (userText.trim()) {
        parts.push({ text: userText });
      }

      if (imgFile) {
        const base64Data = await convertToBase64(imgFile);
        base64String = base64Data;
        parts.push({
          inlineData: {
            data: base64Data,
            mimeType: imgFile.type
          }
        });
      }

      const requestBody = {
        appName: 'app',
        userId,
        sessionId,
        newMessage: {
          role: 'user',
          parts
        }
      };

      const response = await fetch('/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }

      const events = await response.json();
      processEvents(events);

      // Save receipt to backend since it was accepted and run completed
      if (imgFile && base64String) {
        const timestamp = Date.now();
        const fileName = imgFile.name 
          ? `receipt_${timestamp}_${imgFile.name.replace(/[^a-zA-Z0-9._-]/g, '_')}` 
          : `receipt_${timestamp}.png`;
        try {
          await fetch('/api/save-receipt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              fileName,
              base64Data: base64String
            })
          });
        } catch (err) {
          console.error("Failed to save receipt to backend:", err);
        }
      }
    } catch (err: any) {
      setMessages(prev => [
        ...prev,
        {
          id: 'error_' + Date.now(),
          sender: 'system',
          text: `Error connecting to backend: ${err.message}`
        }
      ]);
    } finally {
      setLoading(false);
      refreshAssets();
    }
  };

  // Handle human-in-the-loop interrupt response
  const handleInterruptResponse = async (approved: boolean) => {
    if (!pendingInterrupt) return;

    const decision = approved ? 'yes' : 'no';
    setPendingInterrupt(null);
    setLoading(true);

    // Add decision as a system log in chat
    setMessages(prev => [
      ...prev,
      {
        id: 'system_' + Date.now(),
        sender: 'system',
        text: `User response to guardrail verification: "${decision.toUpperCase()}"`
      }
    ]);

    try {
      const requestBody = {
        appName: 'app',
        userId,
        sessionId,
        newMessage: {
          role: 'user',
          parts: [
            {
              functionResponse: {
                id: pendingInterrupt.id,
                name: pendingInterrupt.id,
                response: { result: decision }
              }
            }
          ]
        }
      };

      const response = await fetch('/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }

      const events = await response.json();
      processEvents(events);
    } catch (err: any) {
      setMessages(prev => [
        ...prev,
        {
          id: 'error_' + Date.now(),
          sender: 'system',
          text: `Error submitting decision to backend: ${err.message}`
        }
      ]);
    } finally {
      setLoading(false);
      refreshAssets();
    }
  };

  // Parse returned event list
  const processEvents = (events: any[]) => {
    let textAccumulator = '';
    let interruptObj: typeof pendingInterrupt = null;

    events.forEach(evt => {
      // Check for message text
      if (evt.content && evt.content.parts) {
        evt.content.parts.forEach((part: any) => {
          if (part.text) {
            textAccumulator += part.text + '\n';
          }
        });
      }

      // Check for interrupt
      if (evt.interrupted) {
        interruptObj = {
          id: 'confirm_hijack', // Default interrupt id matching security_gate
          message: evt.errorMessage || "Potential instruction hijack or safety override detected. Do you want to proceed?"
        };
      }
    });

    const cleanText = textAccumulator.trim();
    if (cleanText) {
      const newMsgId = 'msg_' + Date.now();
      setMessages(prev => [
        ...prev,
        {
          id: newMsgId,
          sender: 'model',
          text: cleanText
        }
      ]);
    }

    if (interruptObj) {
      setPendingInterrupt(interruptObj);
      setMessages(prev => [
        ...prev,
        {
          id: 'warn_' + Date.now(),
          sender: 'system',
          text: `GUARDRAIL TRIGGERED: ${interruptObj!.message}`,
          isWarning: true
        }
      ]);
    }
  };

  // Feedback submission
  const submitQuickFeedback = async (msgId: string, isPositive: boolean) => {
    const score = isPositive ? 5 : 1;
    const ratingType = isPositive ? 'up' : 'down';
    
    setRatedMessages(prev => ({
      ...prev,
      [msgId]: ratingType
    }));

    try {
      await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          score,
          comment: `Quick feedback: ${ratingType.toUpperCase()}`,
          session_id: sessionId
        })
      });
    } catch (err) {
      console.error("Failed to submit feedback:", err);
    }
  };

  // Format shopping list markdown
  const renderShoppingList = () => {
    if (!shoppingList || shoppingList.startsWith("No shopping list")) {
      return (
        <div className="empty-panel-message">
          <p>No shopping list has been generated yet.</p>
          <p className="hint">Finalize a recipe with the Cooking Assistant to generate a shopping list.</p>
        </div>
      );
    }

    // Split markdown lines
    const lines = shoppingList.split('\n');
    return (
      <div className="shopping-list-container">
        {lines.map((line, idx) => {
          if (line.startsWith('# ')) {
            return <h2 key={idx}>{line.substring(2)}</h2>;
          } else if (line.startsWith('- [ ] ') || line.startsWith('- [x] ')) {
            const isChecked = line.startsWith('- [x] ');
            const content = line.substring(6);
            return (
              <label key={idx} className="checkbox-item">
                <input 
                  type="checkbox" 
                  checked={isChecked} 
                  onChange={() => handleCheckboxToggle(idx)} 
                />
                <span>{content}</span>
              </label>
            );
          } else if (line.trim() === '') {
            return <div key={idx} style={{ height: '10px' }} />;
          } else {
            return <p key={idx} className="list-text">{line}</p>;
          }
        })}
      </div>
    );
  };

  // Format shopping history JSON
  const renderShoppingHistory = () => {
    if (!shoppingHistory || shoppingHistory.length === 0) {
      return (
        <div className="empty-panel-message">
          <p>No purchase records found.</p>
          <p className="hint">Upload a receipt or confirm a grocery purchase with the Budget Assistant to log entries.</p>
        </div>
      );
    }

    let grandTotal = 0;
    shoppingHistory.forEach(record => {
      record.items.forEach(item => {
        grandTotal += (item.price * (item.quantity || 1));
      });
    });

    return (
      <div className="shopping-history-container">
        <div className="history-summary">
          <span>Total Logged Spending:</span>
          <strong>${grandTotal.toFixed(2)}</strong>
        </div>
        
        {shoppingHistory.map((record, idx) => (
          <div key={idx} className="history-card">
            <div className="card-header">
              <span className="card-date">📅 {record.date}</span>
              <span className="card-total">
                Subtotal: ${record.items.reduce((acc, item) => acc + (item.price * (item.quantity || 1)), 0).toFixed(2)}
              </span>
            </div>
            <table className="card-table">
              <thead>
                <tr>
                  <th>Item</th>
                  <th style={{ textAlign: 'center' }}>Qty</th>
                  <th style={{ textAlign: 'right' }}>Price</th>
                </tr>
              </thead>
              <tbody>
                {record.items.map((item, itemIdx) => (
                  <tr key={itemIdx}>
                    <td>{item.name}</td>
                    <td style={{ textAlign: 'center' }}>{item.quantity || 1}</td>
                    <td style={{ textAlign: 'right' }}>${item.price.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
      </div>
    );
  };

  // Format receipts log view
  const renderReceiptsLog = () => {
    if (!uploadedReceipts || uploadedReceipts.length === 0) {
      return (
        <div className="empty-panel-message">
          <p>No uploaded receipts found.</p>
          <p className="hint">Attach a receipt or grocery photo and send a message to log it here.</p>
        </div>
      );
    }

    return (
      <div className="receipts-log-container">
        <div className="receipts-grid">
          {uploadedReceipts.map((fileName) => {
            const displayName = fileName.replace(/^receipt_\d+_/, '');
            const fileUrl = `/api/receipts/${fileName}`;
            return (
              <div key={fileName} className="receipt-thumbnail-card">
                <a href={fileUrl} target="_blank" rel="noopener noreferrer" className="receipt-img-link">
                  <img src={fileUrl} alt={displayName} />
                </a>
                <div className="receipt-info">
                  <span className="receipt-name" title={displayName}>{displayName}</span>
                  <a href={fileUrl} download={displayName} className="btn-download-receipt">
                    📥 Download
                  </a>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <div className="app-container">
      {/* HEADER */}
      <header className="app-header">
        <div className="logo-section">
          <span className="emoji-logo">🍳</span>
          <div>
            <h1>Cooking & Shopping Assistant</h1>
            <p className="session-info">Active Session: <code>{sessionId.slice(0, 15)}...</code></p>
          </div>
        </div>
        <div className="actions-section">
          <button className="btn-secondary" onClick={resetSession}>🔄 New Conversation</button>
        </div>
      </header>

      {/* MAIN LAYOUT */}
      <main className="main-content">
        {/* CHAT AREA (LEFT) */}
        <section className="chat-panel">
          <div className="messages-list">
            {messages.map((msg) => (
              <div key={msg.id} className={`message-wrapper ${msg.sender} ${msg.isWarning ? 'warning' : ''}`}>
                <div className="avatar">
                  {msg.sender === 'user' ? '👤' : msg.sender === 'model' ? '🤖' : '⚠️'}
                </div>
                <div className="message-bubble">
                  {msg.image && (
                    <div className="message-image">
                      <img src={msg.image} alt="Uploaded attachment" />
                    </div>
                  )}
                  <p className="message-text">{msg.text}</p>
                  
                  {msg.sender === 'model' && msg.id !== 'welcome' && (
                    <div className="message-quick-feedback">
                      <button 
                        type="button"
                        className={`feedback-icon-btn ${ratedMessages[msg.id] === 'up' ? 'active' : ''}`}
                        onClick={() => submitQuickFeedback(msg.id, true)}
                        disabled={!!ratedMessages[msg.id]}
                        title="Helpful"
                      >
                        👍
                      </button>
                      <button 
                        type="button"
                        className={`feedback-icon-btn ${ratedMessages[msg.id] === 'down' ? 'active' : ''}`}
                        onClick={() => submitQuickFeedback(msg.id, false)}
                        disabled={!!ratedMessages[msg.id]}
                        title="Unhelpful"
                      >
                        👎
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="message-wrapper model loading">
                <div className="avatar">🤖</div>
                <div className="message-bubble">
                  <div className="loading-dots">
                    <span></span><span></span><span></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* INTERRUPT MODAL BANNER */}
          {pendingInterrupt && (
            <div className="interrupt-banner">
              <div className="banner-content">
                <strong>🔒 Guardrail Verification Required</strong>
                <p>{pendingInterrupt.message}</p>
                <div className="banner-actions">
                  <button className="btn-success" onClick={() => handleInterruptResponse(true)}>Yes, proceed</button>
                  <button className="btn-danger" onClick={() => handleInterruptResponse(false)}>No, abort</button>
                </div>
              </div>
            </div>
          )}

          {/* CHAT INPUT AREA */}
          <form className="chat-input-bar" onSubmit={handleSend}>
            {attachedImagePreview && (
              <div className="preview-container">
                <img src={attachedImagePreview} alt="upload preview" />
                <button type="button" className="clear-preview-btn" onClick={clearAttachedImage}>×</button>
              </div>
            )}
            
            <div className="input-row">
              <input
                type="file"
                accept="image/*"
                style={{ display: 'none' }}
                ref={fileInputRef}
                onChange={handleImageChange}
              />
              <button
                type="button"
                className="btn-attach"
                onClick={() => fileInputRef.current?.click()}
                title="Attach Recipe or Receipt Image"
              >
                📎
              </button>
              
              <input
                type="text"
                placeholder="Ask for recipe ideas, paste receipt contents, or check spending history..."
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                disabled={loading || !!pendingInterrupt}
              />
              
              <button type="submit" className="btn-send" disabled={loading || !!pendingInterrupt}>
                Send
              </button>
            </div>
          </form>
        </section>

        {/* ASSETS / STATUS DISPLAY (RIGHT) */}
        <section className="assets-panel">
          <div className="tabs-header">
            <button 
              className={`tab-btn ${activeTab === 'shopping-list' ? 'active' : ''}`}
              onClick={() => setActiveTab('shopping-list')}
            >
              📋 Shopping List
            </button>
            <button 
              className={`tab-btn ${activeTab === 'shopping-history' ? 'active' : ''}`}
              onClick={() => setActiveTab('shopping-history')}
            >
              💵 Purchase History
            </button>
            <button 
              className={`tab-btn ${activeTab === 'receipts-log' ? 'active' : ''}`}
              onClick={() => setActiveTab('receipts-log')}
            >
              🧾 Receipts Log
            </button>
          </div>
          
          <div className="tab-body">
            {activeTab === 'shopping-list' && renderShoppingList()}
            {activeTab === 'shopping-history' && renderShoppingHistory()}
            {activeTab === 'receipts-log' && renderReceiptsLog()}
          </div>
        </section>
      </main>


    </div>
  );
}

export default App;
