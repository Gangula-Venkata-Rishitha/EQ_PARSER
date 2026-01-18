function LogicTab({ formulas }) {
  if (!formulas || formulas.length === 0) {
    return <div className="text-gray-500">No logic formulas found.</div>
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Logic Formulas ({formulas.length})</h2>
      
      {formulas.map((formula) => (
        <div key={formula.formula_id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
          <div className="flex items-center gap-2 mb-2">
            <span className="font-mono text-sm text-gray-600">{formula.formula_id}</span>
            <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded">{formula.logic_type}</span>
            <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">{formula.form}</span>
            {formula.is_valid ? (
              <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded">Valid</span>
            ) : (
              <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded">Invalid</span>
            )}
          </div>
          
          <div className="font-mono text-sm bg-gray-50 p-2 rounded mb-2">
            {formula.raw}
          </div>
          
          <div className="text-sm text-gray-700">
            <p>{formula.explanation_nlp}</p>
          </div>
          
          {formula.syntax_errors && formula.syntax_errors.length > 0 && (
            <div className="mt-2 text-sm text-red-600">
              <span className="font-semibold">Errors:</span>
              <ul className="list-disc list-inside">
                {formula.syntax_errors.map((err, idx) => (
                  <li key={idx}>{err.error_type}: {err.message}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

export default LogicTab
