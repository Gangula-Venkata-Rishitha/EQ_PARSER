function ErrorsTab({ errors, equations }) {
  const allErrors = errors || []
  const equationErrors = equations?.flatMap(eq => 
    eq.errors?.map(err => ({ ...err, source: eq.eq_id, category: 'equation' })) || []
  ) || []

  const combinedErrors = [...allErrors, ...equationErrors]

  if (combinedErrors.length === 0) {
    return <div className="text-gray-500">No errors found.</div>
  }

  // Group by error type
  const groupedErrors = combinedErrors.reduce((acc, err) => {
    const type = err.error_type || 'unknown'
    if (!acc[type]) {
      acc[type] = []
    }
    acc[type].push(err)
    return acc
  }, {})

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Errors ({combinedErrors.length})</h2>
      
      {Object.entries(groupedErrors).map(([type, errs]) => (
        <div key={type} className="border border-red-200 rounded-lg p-4 bg-red-50">
          <div className="font-semibold text-red-700 mb-2">
            {type} ({errs.length})
          </div>
          <ul className="space-y-1 text-sm">
            {errs.map((err, idx) => (
              <li key={idx} className="text-gray-700">
                {err.source && <span className="font-mono text-xs text-gray-500">[{err.source}] </span>}
                {err.message}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}

export default ErrorsTab
