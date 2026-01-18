function SRSTab({ requirements }) {
  if (!requirements || requirements.length === 0) {
    return <div className="text-gray-500">No SRS requirements found.</div>
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">SRS Requirements ({requirements.length})</h2>
      
      {requirements.map((req) => (
        <div key={req.req_id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
          <div className="flex items-center gap-2 mb-2">
            <span className="font-mono text-sm text-gray-600">{req.req_id}</span>
            <span className="text-xs text-gray-500">Page {req.page}</span>
          </div>
          
          <div className="text-sm text-gray-700 mb-2">
            {req.requirement_text}
          </div>
          
          {req.linked_logic && (
            <div className="mt-2 p-2 bg-green-50 rounded border border-green-200">
              <div className="text-xs font-semibold text-green-700 mb-1">Linked Logic:</div>
              <div className="font-mono text-xs">{req.linked_logic.raw}</div>
            </div>
          )}
          
          <div className="mt-2 text-xs text-gray-600">
            {req.explanation}
          </div>
        </div>
      ))}
    </div>
  )
}

export default SRSTab
