import { useState } from 'react'
import SummaryTab from './SummaryTab'
import EquationsTab from './EquationsTab'
import LogicTab from './LogicTab'
import SRSTab from './SRSTab'
import ErrorsTab from './ErrorsTab'
import ChatTab from './ChatTab'

function ResultsDashboard({ parseResult, apiBase }) {
  const [activeTab, setActiveTab] = useState('summary')

  const tabs = [
    { id: 'summary', label: 'Summary' },
    { id: 'equations', label: 'Equations' },
    { id: 'logic', label: 'Logic' },
    { id: 'srs', label: 'SRS' },
    { id: 'errors', label: 'Errors' },
    { id: 'chat', label: 'Ask' }
  ]

  return (
    <div className="bg-white rounded-lg shadow-md">
      <div className="border-b border-gray-200">
        <nav className="flex space-x-1 px-4" aria-label="Tabs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>
      
      <div className="p-6">
        {activeTab === 'summary' && <SummaryTab summary={parseResult.summary} />}
        {activeTab === 'equations' && <EquationsTab equations={parseResult.equations} />}
        {activeTab === 'logic' && <LogicTab formulas={parseResult.logic_formulas} />}
        {activeTab === 'srs' && <SRSTab requirements={parseResult.srs_requirements} />}
        {activeTab === 'errors' && <ErrorsTab errors={parseResult.errors} equations={parseResult.equations} />}
        {activeTab === 'chat' && <ChatTab docId={parseResult.doc_id} apiBase={apiBase} />}
      </div>
    </div>
  )
}

export default ResultsDashboard
