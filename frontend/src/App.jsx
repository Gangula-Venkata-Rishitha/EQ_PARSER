import { useState } from 'react'
import axios from 'axios'
import UploadPanel from './components/UploadPanel'
import ResultsDashboard from './components/ResultsDashboard'

const API_BASE = 'http://localhost:8000'

function App() {
  const [parseResult, setParseResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleUpload = async (file) => {
    setLoading(true)
    setError(null)
    
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await axios.post(`${API_BASE}/parse`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      
      setParseResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Error parsing PDF')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-semibold text-gray-900">Equation Parser</h1>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto px-4 py-8">
        <UploadPanel onUpload={handleUpload} loading={loading} error={error} />
        
        {parseResult && (
          <ResultsDashboard parseResult={parseResult} apiBase={API_BASE} />
        )}
      </main>
    </div>
  )
}

export default App
