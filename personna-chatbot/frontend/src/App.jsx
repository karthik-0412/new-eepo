import React, { useState } from 'react'

export default function App() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)

  async function send() {
    if (!input.trim()) return
    const userMsg = { user: input }
    setMessages(prev => [...prev, { role: 'user', text: input }])
    setInput('')
    setLoading(true)
    try {
      const resp = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input, history: messages.filter(m => m.role).map(m => ({ user: m.role === 'user' ? m.text : '', assistant: m.role === 'assistant' ? m.text : '' })) })
      })
      const data = await resp.json()
      setMessages(prev => [...prev, { role: 'assistant', text: data.reply }])
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', text: 'Error: ' + err.message }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <h1>Personna Chatbot</h1>
      <div className="chat">
        {messages.map((m, i) => (
          <div key={i} className={"msg " + m.role}>{m.text}</div>
        ))}
        {loading && <div className="msg assistant">...</div>}
      </div>
      <div className="composer">
        <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') send() }} placeholder="Type a message..." />
        <button onClick={send} disabled={loading}>Send</button>
      </div>
    </div>
  )
}
