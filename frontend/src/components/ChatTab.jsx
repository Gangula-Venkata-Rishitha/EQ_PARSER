import { useState } from 'react'
import axios from 'axios'

function ChatTab({ docId, apiBase }) {
  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)

  const handleSend = async (e) => {
    e.preventDefault()
    if (!message.trim()) return

    const userMessage = message.trim()
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setMessage('')
    setLoading(true)

    try {
      const response = await axios.post(`${apiBase}/chat`, {
        doc_id: docId,
        message: userMessage
      })

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.data.response,
        references: response.data.references || []
      }])
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${err.response?.data?.detail || 'Unknown error'}`,
        references: []
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Chat</h2>
      
      <div className="border border-gray-200 rounded-lg h-96 overflow-y-auto p-4 bg-gray-50">
        {messages.length === 0 ? (
          <div className="text-gray-500 text-center mt-8">
            Ask questions about the parsed document. For example:
            <ul className="mt-4 text-left space-y-1 text-sm">
              <li>• "Explain equation eq-0001"</li>
              <li>• "Which equations have errors?"</li>
              <li>• "Convert 'product of mass and acceleration' to equation"</li>
              <li>• "What is Net Force?"</li>
            </ul>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-lg ${
                  msg.role === 'user'
                    ? 'bg-blue-100 ml-8'
                    : 'bg-white mr-8'
                }`}
              >
                <div className="text-sm font-semibold mb-1">
                  {msg.role === 'user' ? 'You' : 'Assistant'}
                </div>
                <div className="text-sm">{msg.content}</div>
                {msg.references && msg.references.length > 0 && (
                  <div className="mt-2 text-xs text-gray-600">
                    References: {msg.references.map(ref => ref.id || ref.type).join(', ')}
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="text-gray-500 text-sm">Thinking...</div>
            )}
          </div>
        )}
      </div>
      
      <form onSubmit={handleSend} className="flex gap-2">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type your message..."
          className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !message.trim()}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          Send
        </button>
      </form>
    </div>
  )
}

export default ChatTab
