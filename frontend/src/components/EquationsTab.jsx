import { useState } from 'react'

function EquationsTab({ equations }) {
  const [expandedEq, setExpandedEq] = useState(null)

  if (!equations || equations.length === 0) {
    return <div className="text-gray-500">No equations found.</div>
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Equations ({equations.length})</h2>
      
      {equations.map((eq) => (
        <div key={eq.eq_id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="font-mono text-sm text-gray-600">{eq.eq_id}</span>
              <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">{eq.type}</span>
              {eq.errors && eq.errors.length > 0 && (
                <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded">
                  {eq.errors.length} error{eq.errors.length > 1 ? 's' : ''}
                </span>
              )}
            </div>
            <button
              onClick={() => setExpandedEq(expandedEq === eq.eq_id ? null : eq.eq_id)}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              {expandedEq === eq.eq_id ? 'Hide' : 'Show details'}
            </button>
          </div>
          
          <div className="font-mono text-sm bg-gray-50 p-2 rounded mb-2">
            {eq.raw}
          </div>
          
          {expandedEq === eq.eq_id && (
            <div className="mt-4 space-y-3 text-sm border-t pt-3">
              <div>
                <span className="font-semibold">Normalized:</span>
                <div className="font-mono bg-gray-50 p-2 rounded mt-1">{eq.normalized}</div>
              </div>
              
              <div>
                <span className="font-semibold">Explanation:</span>
                <p className="mt-1 text-gray-700">{eq.explanation_nlp}</p>
              </div>
              
              {eq.variables && (
                <div>
                  <span className="font-semibold">Variables:</span>
                  <div className="mt-1 space-y-1 text-gray-600">
                    <div>Used: {eq.variables.used_symbols?.join(', ') || 'none'}</div>
                    <div>Declared: {eq.variables.declared_symbols?.join(', ') || 'none'}</div>
                    <div>Initialized: {eq.variables.initialized_symbols?.join(', ') || 'none'}</div>
                    <div>Defined: {eq.variables.defined_symbols?.join(', ') || 'none'}</div>
                    {eq.variables.missing_declaration?.length > 0 && (
                      <div className="text-orange-600">Missing declaration: {eq.variables.missing_declaration.join(', ')}</div>
                    )}
                    {eq.variables.missing_initialization?.length > 0 && (
                      <div className="text-orange-600">Missing initialization: {eq.variables.missing_initialization.join(', ')}</div>
                    )}
                  </div>
                </div>
              )}
              
              {eq.errors && eq.errors.length > 0 && (
                <div>
                  <span className="font-semibold text-red-600">Errors:</span>
                  <ul className="mt-1 list-disc list-inside text-red-600">
                    {eq.errors.map((err, idx) => (
                      <li key={idx}>{err.error_type}: {err.message}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

export default EquationsTab
