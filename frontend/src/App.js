import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [url, setUrl] = useState('');
  const [scrapeMode, setScrapeMode] = useState('full');
  const [isIngesting, setIsIngesting] = useState(false);
  const [ingestSuccess, setIngestSuccess] = useState(false);
  const [ingestStatus, setIngestStatus] = useState('');
  
  const [question, setQuestion] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [isChatting, setIsChatting] = useState(false);

  // --- NEW: CHAT SESSION MEMORY ---
  const [chatSessions, setChatSessions] = useState(() => {
    const saved = localStorage.getItem('dataScoutChats');
    return saved ? JSON.parse(saved) : [];
  });
  const [currentSessionId, setCurrentSessionId] = useState(Date.now().toString());

  // Auto-save chat to local storage whenever it updates
  useEffect(() => {
    if (chatHistory.length > 0) {
      setChatSessions(prev => {
        const existing = prev.find(s => s.id === currentSessionId);
        // Create a title based on the first question
        const title = chatHistory[0].text.length > 22 ? chatHistory[0].text.substring(0, 22) + '...' : chatHistory[0].text;
        
        let updated;
        if (existing) {
          updated = prev.map(s => s.id === currentSessionId ? { ...s, history: chatHistory } : s);
        } else {
          updated = [{ id: currentSessionId, title: title, history: chatHistory }, ...prev];
        }
        localStorage.setItem('dataScoutChats', JSON.stringify(updated));
        return updated;
      });
    }
  }, [chatHistory, currentSessionId]);

  const handleNewChat = () => {
    setChatHistory([]);
    setCurrentSessionId(Date.now().toString());
  };

  const loadSession = (id) => {
    const session = chatSessions.find(s => s.id === id);
    if (session) {
      setChatHistory(session.history);
      setCurrentSessionId(session.id);
    }
  };
  // --------------------------------

  const [logIndex, setLogIndex] = useState(0);
  const loadingLogs = [
    "> Initializing web crawler...",
    "> Bypassing bot protections...",
    "> Mapping domain architecture...",
    "> Extracting clean HTML payload...",
    "> Ignoring media and PDF files...",
    "> Generating high-dimensional vector embeddings...",
    "> Pushing to Supabase pgvector...",
    "> Activating RAG query pipeline..."
  ];

  useEffect(() => {
    let interval;
    if (isIngesting) {
      interval = setInterval(() => {
        setLogIndex((prev) => (prev < loadingLogs.length - 1 ? prev + 1 : prev));
      }, 1200); 
    } else {
      setLogIndex(0);
    }
    return () => clearInterval(interval);
  }, [isIngesting, loadingLogs.length]);

  const handleIngest = async (e) => {
    e.preventDefault();
    setIsIngesting(true);
    setIngestSuccess(false);
    setIngestStatus('');
    try {
      const response = await axios.post('http://localhost:8000/api/ingest/', { url, mode: scrapeMode });
      setIngestStatus(response.data.message);
      setIngestSuccess(true);
    } catch (error) {
      setIngestStatus('Error: Ingestion failed. Site may be blocking scrapers.');
    } finally {
      setIsIngesting(false);
    }
  };

  const handleChat = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    const currentQuestion = question;
    const previousHistory = [...chatHistory];
    
    const newHistory = [...previousHistory, { role: 'user', text: currentQuestion }];
    setChatHistory(newHistory);
    setQuestion('');
    setIsChatting(true);

    try {
      const response = await axios.post('http://localhost:8000/api/chat/', { 
        question: currentQuestion, 
        history: previousHistory 
      });
      setChatHistory([...newHistory, { role: 'ai', text: response.data.answer || "No response generated." }]);
    } catch (error) {
      setChatHistory([...newHistory, { role: 'ai', text: 'Error connecting to LLM.' }]);
    } finally {
      setIsChatting(false);
    }
  };

  return (
    <div style={styles.page}>
      <style>{`
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
        .cursor { animation: blink 1s step-end infinite; }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
      `}</style>

      <div style={styles.container}>
        {/* HEADER */}
        <header style={styles.header}>
          <h1 style={styles.title}>DataScout<span style={{color: '#3b82f6'}}>.AI</span></h1>
          <p style={styles.subtitle}>Retrieval-Augmented Generation Engine</p>
        </header>

        {/* INGESTION MODULE */}
        <div style={styles.card}>
          <form onSubmit={handleIngest} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
            <div style={{ display: 'flex', gap: '10px' }}>
              <input 
                type="url" 
                value={url} 
                onChange={(e) => setUrl(e.target.value)} 
                placeholder="Enter target URL..." 
                required 
                style={{ ...styles.input, flex: 1 }}
                disabled={isIngesting}
              />
              <select 
                value={scrapeMode} 
                onChange={(e) => setScrapeMode(e.target.value)}
                style={{ ...styles.input, flex: '0 0 180px', cursor: 'pointer' }}
                disabled={isIngesting}
              >
                <option value="full">Deep Dive (20 Pages)</option>
                <option value="single">Quick Scan (1 Page)</option>
              </select>
            </div>
            <button type="submit" disabled={isIngesting} style={isIngesting ? styles.buttonDisabled : styles.button}>
              {isIngesting ? 'INITIALIZING SCAN...' : 'INGEST DATA'}
            </button>
          </form>

          {/* HACKER LOGS */}
          {isIngesting && (
            <div style={styles.terminal}>
              <span style={{color: '#22c55e'}}>{loadingLogs[logIndex]}<span className="cursor">_</span></span>
            </div>
          )}
          {ingestStatus && !isIngesting && (
            <p style={{ color: ingestSuccess ? '#22c55e' : '#ef4444', marginTop: '15px', fontSize: '0.9rem' }}>
               {ingestStatus}
            </p>
          )}
        </div>

        {/* CHAT MODULE WITH SIDEBAR */}
        {ingestSuccess && (
          <div style={styles.chatLayout}>
            {/* Sidebar for Sessions */}
            <div style={styles.sidebar}>
              <button onClick={handleNewChat} style={styles.newChatBtn}>
                + NEW CHAT
              </button>
              <div style={styles.sessionList}>
                {chatSessions.length === 0 && <p style={{color: '#64748b', fontSize: '0.8rem', textAlign: 'center'}}>No saved chats</p>}
                {chatSessions.map(session => (
                  <div 
                    key={session.id} 
                    onClick={() => loadSession(session.id)}
                    style={{
                      ...styles.sessionItem, 
                      backgroundColor: session.id === currentSessionId ? '#1e293b' : 'transparent',
                      borderLeft: session.id === currentSessionId ? '3px solid #3b82f6' : '3px solid transparent'
                    }}
                  >
                    {session.title}
                  </div>
                ))}
              </div>
            </div>

            {/* Main Chat Area */}
            <div style={styles.chatArea}>
              <div style={styles.chatBox}>
                {chatHistory.length === 0 ? (
                  <p style={{color: '#64748b', textAlign: 'center', marginTop: '40px'}}>System ready. Awaiting query...</p>
                ) : (
                  chatHistory.map((msg, idx) => (
                    <div key={idx} style={{ textAlign: msg.role === 'user' ? 'right' : 'left', marginBottom: '15px' }}>
                      <span style={msg.role === 'user' ? styles.userBubble : styles.aiBubble}>
                        {msg.text}
                      </span>
                    </div>
                  ))
                )}
                {isChatting && <p style={{ color: '#3b82f6', fontSize: '0.9rem' }}>Generating response<span className="cursor">...</span></p>}
              </div>
              
              <form onSubmit={handleChat} style={styles.form}>
                <input 
                  type="text" 
                  value={question} 
                  onChange={(e) => setQuestion(e.target.value)} 
                  placeholder="Query the dataset..." 
                  style={styles.input}
                  disabled={isChatting}
                />
                <button type="submit" disabled={isChatting} style={isChatting ? styles.buttonDisabled : styles.button}>
                  SEND
                </button>
              </form>
            </div>
          </div>
        )}
      </div>

      {/* FOOTER */}
      <footer style={styles.footer}>
        <div style={styles.footerContent}>
          <p style={{ margin: '0 0 10px 0' }}><strong>Hackathon Submission</strong> | Job Drive 2026</p>
          <p style={styles.techStack}>
            <span>⚙️ React</span>
            <span>🐍 Django</span>
            <span>🗄️ Supabase (pgvector)</span>
            <span>🤖 HuggingFace & Groq API</span>
          </p>
        </div>
      </footer>
    </div>
  );
}

const styles = {
  page: { minHeight: '100vh', backgroundColor: '#020617', color: '#f8fafc', fontFamily: '"JetBrains Mono", "Courier New", monospace', display: 'flex', flexDirection: 'column', alignItems: 'center' },
  container: { width: '100%', maxWidth: '900px', padding: '40px 20px', flex: 1 },
  header: { textAlign: 'center', marginBottom: '40px' },
  title: { margin: 0, fontSize: '2.5rem', fontWeight: 'bold', letterSpacing: '2px' },
  subtitle: { color: '#64748b', fontSize: '0.9rem', marginTop: '5px', textTransform: 'uppercase' },
  card: { backgroundColor: '#0f172a', padding: '25px', borderRadius: '12px', border: '1px solid #1e293b', marginBottom: '20px' },
  form: { display: 'flex', gap: '10px' },
  input: { flex: 1, padding: '15px', backgroundColor: '#020617', border: '1px solid #334155', color: '#f8fafc', borderRadius: '6px', fontSize: '0.9rem', fontFamily: 'inherit', outline: 'none' },
  button: { padding: '0 25px', backgroundColor: '#3b82f6', color: '#fff', border: 'none', borderRadius: '6px', fontSize: '0.9rem', fontWeight: 'bold', cursor: 'pointer', fontFamily: 'inherit', transition: 'background 0.2s' },
  buttonDisabled: { padding: '0 25px', backgroundColor: '#1e293b', color: '#64748b', border: '1px solid #334155', borderRadius: '6px', fontSize: '0.9rem', cursor: 'not-allowed', fontFamily: 'inherit' },
  terminal: { marginTop: '20px', padding: '15px', backgroundColor: '#020617', border: '1px solid #1e293b', borderRadius: '6px', fontSize: '0.85rem' },
  
  // NEW LAYOUT STYLES
  chatLayout: { display: 'flex', gap: '20px', backgroundColor: '#0f172a', padding: '20px', borderRadius: '12px', border: '1px solid #1e293b', height: '500px' },
  sidebar: { width: '220px', display: 'flex', flexDirection: 'column', gap: '15px', borderRight: '1px solid #1e293b', paddingRight: '15px' },
  newChatBtn: { width: '100%', padding: '12px', backgroundColor: 'transparent', border: '1px dashed #3b82f6', color: '#3b82f6', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', fontFamily: 'inherit', transition: 'all 0.2s' },
  sessionList: { flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '5px' },
  sessionItem: { padding: '10px', fontSize: '0.85rem', color: '#cbd5e1', cursor: 'pointer', borderRadius: '4px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', transition: 'background 0.2s' },
  chatArea: { flex: 1, display: 'flex', flexDirection: 'column', gap: '15px' },
  chatBox: { flex: 1, overflowY: 'auto', padding: '15px', backgroundColor: '#020617', borderRadius: '6px', border: '1px solid #1e293b' },
  userBubble: { backgroundColor: '#3b82f6', color: '#fff', padding: '12px 18px', borderRadius: '8px', display: 'inline-block', maxWidth: '85%', fontSize: '0.9rem' },
  aiBubble: { backgroundColor: '#1e293b', color: '#cbd5e1', padding: '12px 18px', borderRadius: '8px', border: '1px solid #334155', display: 'inline-block', maxWidth: '85%', fontSize: '0.9rem', lineHeight: '1.5' },
  
  footer: { width: '100%', backgroundColor: '#0f172a', borderTop: '1px solid #1e293b', color: '#94a3b8', textAlign: 'center', padding: '25px 20px', marginTop: 'auto' },
  footerContent: { maxWidth: '800px', margin: '0 auto', fontSize: '0.9rem' },
  techStack: { display: 'flex', justifyContent: 'center', gap: '15px', margin: 0, flexWrap: 'wrap' }
};

export default App;