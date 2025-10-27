import React, { useState, useEffect, useRef } from 'react';

const DOMAIN_OPTIONS = [
  { id: 'auto', label: 'Auto' },
  { id: 'hr', label: 'HR' },
  { id: 'legal', label: 'Legal' },
  { id: 'l1', label: 'L1 Support' },
  { id: 'l2', label: 'L2 Support' },
];

export default function App() {
  const [domain, setDomain] = useState('auto');
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [view, setView] = useState('chat'); // 'chat' or 'files'
  const listRef = useRef(null);

  useEffect(() => {
    // scroll to bottom when messages update
    if (listRef.current)
      listRef.current.scrollTop = listRef.current.scrollHeight;
  }, [messages]);

  async function send() {
    if (!input.trim()) return;
    const newMessages = [...messages, { role: 'user', content: input }];
    setMessages(newMessages);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          domain,
          session_id: sessionId,
          messages: newMessages,
        }),
      });
      const data = await res.json();
      // append assistant reply and save session id
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.reply },
      ]);
      if (data.session_id) setSessionId(data.session_id);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Error: ' + (e.message || e) },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  return (
    <div className="app-root dark">
      <aside className="sidebar">
        <div className="brand">Chatbot</div>
        <nav className="domains">
          {DOMAIN_OPTIONS.map((d) => (
            <button
              key={d.id}
              className={`domain-btn ${domain === d.id ? 'active' : ''}`}
              onClick={() => setDomain(d.id)}
            >
              {d.label}
            </button>
          ))}
          {/* Files view button */}
          <button
            key="files"
            className={`domain-btn ${view === 'files' ? 'active' : ''}`}
            onClick={() => setView('files')}
          >
            Files
          </button>
        </nav>
        <div className="session">
          Session: <small>{sessionId || '—'}</small>
        </div>
      </aside>

      <main className="main">
        <header className="main-header">
          <div className="header-left">
            {/* Top-left persistent Files toggle */}
            {view === 'files' ? (
              <button className="top-left-files-btn" onClick={() => setView('chat')}>
                ← Chat
              </button>
            ) : (
              <button className="top-left-files-btn" onClick={() => setView('files')}>
                Files
              </button>
            )}
          </div>

          <h2>
            {view === 'chat'
              ? `${DOMAIN_OPTIONS.find((d) => d.id === domain).label} Conversation`
              : 'Files'}
          </h2>
        </header>
        {view === 'chat' ? (
          <>
            <div className="chat-list" ref={listRef}>
              {messages.length === 0 && (
                <div className="empty">Start the conversation — ask a question.</div>
              )}
              {messages.map((m, i) => (
                <div key={i} className={`msg ${m.role}`}>
                  <div className="bubble">
                    <div className="role">{m.role}</div>
                    <div className="content">{m.content}</div>
                  </div>
                </div>
              ))}
            </div>

            <div className="composer">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your message and press Enter to send"
              />
              <button onClick={send} disabled={loading} className="send-btn">
                {loading ? '...' : 'Send'}
              </button>
            </div>
          </>
        ) : (
          <FilesPanel />
        )}
      </main>
    </div>
  );
}

function FilesPanel() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadFiles();
  }, []);

  async function loadFiles() {
    setLoading(true);
    try {
      const res = await fetch('/api/files/list');
      const data = await res.json();
      setFiles(data);
    } catch (e) {
      console.error('Failed to load files', e);
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(e) {
    const f = e.target.files[0];
    if (!f) return;
    const fd = new FormData();
    fd.append('file', f);
    try {
      const res = await fetch('/api/files/upload', {
        method: 'POST',
        body: fd,
      });
      const data = await res.json();
      // refresh list
      loadFiles();
    } catch (err) {
      console.error('upload error', err);
    }
  }

  return (
    <div style={{ padding: 20 }}>
      <div style={{ marginBottom: 12 }}>
        <label className="send-btn" style={{ display: 'inline-block', cursor: 'pointer' }}>
          Upload file
          <input type="file" onChange={handleUpload} style={{ display: 'none' }} />
        </label>
      </div>

      {loading ? (
        <div className="empty">Loading files...</div>
      ) : files.length === 0 ? (
        <div className="empty">No files uploaded yet.</div>
      ) : (
        <div className="files-grid">
          {files.map((f) => (
            <div key={f.name} className="file-card">
              <a href={f.url} target="_blank" rel="noreferrer" className="file-link">
                <div className="file-name">{f.name}</div>
                <div className="file-meta">{Math.round((f.size || 0) / 1024)} KB</div>
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
