import { useState, useRef, useEffect } from 'react'
import api, { BASE } from '../../config/api'
import { MessageSquare, X, Send, Bot, Loader } from 'lucide-react'

export default function Chatbot() {
  const [open,          setOpen]          = useState(false)
  const [messages,      setMessages]      = useState([])
  const [conversationId,setConversationId]= useState(null)
  const [input,         setInput]         = useState('')
  const [loading,       setLoading]       = useState(false)
  const [starting,      setStarting]      = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    if (open && !conversationId) demarrer()
  }, [open])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const demarrer = async () => {
    setStarting(true)
    try {
      const r = await api.post(`${BASE.chatbot}/conversations/`, {})
      setConversationId(r.data.id)
      const msgs = r.data.messages || []
      setMessages(msgs.map(m => ({ id: m.id, text: m.contenu, from: m.emetteur })))
    } catch {
      setMessages([{ id:0, text:"Bonjour ! Comment puis-je vous aider ?", from:'chatbot' }])
    } finally { setStarting(false) }
  }

  const envoyer = async () => {
    const txt = input.trim()
    if (!txt || loading) return
    setInput('')

    const idUser = Date.now()
    setMessages(m => [...m, { id: idUser, text: txt, from: 'etudiant' }])
    setLoading(true)

    try {
      const r = await api.post(`${BASE.chatbot}/conversations/${conversationId}/messages/`, { contenu: txt })
      const reponse = r.data.reponse_chatbot
      setMessages(m => [...m, {
        id  : reponse.id || Date.now() + 1,
        text: reponse.contenu,
        from: 'chatbot',
      }])
    } catch {
      setMessages(m => [...m, {
        id  : Date.now() + 1,
        text: 'Désolé, une erreur s\'est produite. Veuillez réessayer.',
        from: 'chatbot',
      }])
    } finally { setLoading(false) }
  }

  const handleKey = e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); envoyer() }
  }

  const fermer = () => {
    setOpen(false)
    setConversationId(null)
    setMessages([])
  }

  return (
    <div className="chat-widget">
      {/* Fenêtre chat */}
      {open && (
        <div className="chat-window">
          {/* Header */}
          <div className="chat-header">
            <div className="chat-avatar"><Bot size={17}/></div>
            <div style={{flex:1}}>
              <div className="chat-header-name">Assistant UADB</div>
              <div className="chat-header-status">
                <span style={{
                  display:'inline-block',width:6,height:6,
                  borderRadius:'50%',background:'#4ade80',marginRight:5,
                }}/>
                En ligne
              </div>
            </div>
            <button onClick={fermer}
              style={{background:'none',border:'none',cursor:'pointer',color:'rgba(255,255,255,.6)',padding:4}}>
              <X size={16}/>
            </button>
          </div>

          {/* Messages */}
          <div className="chat-messages">
            {starting && (
              <div style={{display:'flex',alignItems:'center',gap:8,color:'var(--gray-300)',fontSize:12}}>
                <Loader size={13} style={{animation:'spin .7s linear infinite'}}/>
                Démarrage...
              </div>
            )}
            {messages.map(msg => (
              <div key={msg.id} className={`chat-msg ${msg.from === 'etudiant' ? 'user' : 'bot'}`}>
                {msg.text}
              </div>
            ))}
            {loading && (
              <div className="chat-msg bot" style={{display:'flex',alignItems:'center',gap:6}}>
                <span style={{
                  display:'flex',gap:3,alignItems:'center'
                }}>
                  {[0,1,2].map(i=>(
                    <span key={i} style={{
                      width:6,height:6,borderRadius:'50%',
                      background:'var(--gray-300)',
                      animation:`pulse 1.2s ease ${i*0.2}s infinite`,
                    }}/>
                  ))}
                </span>
              </div>
            )}
            <div ref={bottomRef}/>
          </div>

          {/* Input */}
          <div className="chat-input-area">
            <input
              className="chat-input"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Écrivez votre question..."
              disabled={loading || starting}
            />
            <button className="chat-send" onClick={envoyer} disabled={!input.trim() || loading}>
              <Send size={15}/>
            </button>
          </div>
        </div>
      )}

      {/* Bouton flottant */}
      <button
        className="chat-toggle"
        onClick={() => open ? fermer() : setOpen(true)}
        title="Assistant UADB"
      >
        {open ? <X size={22}/> : <MessageSquare size={22}/>}
      </button>

      {/* Badge non-lu */}
      {!open && (
        <span style={{
          position:'absolute', top:-4, right:-4,
          background:'var(--red)', color:'white',
          width:18, height:18, borderRadius:'50%',
          display:'flex', alignItems:'center', justifyContent:'center',
          fontSize:10, fontWeight:700,
          boxShadow:'0 0 0 2px white',
        }}>1</span>
      )}
    </div>
  )
}
