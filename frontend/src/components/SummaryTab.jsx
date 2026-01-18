function SummaryTab({ summary }) {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold">Summary</h2>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-blue-50 p-4 rounded-lg">
          <div className="text-3xl font-bold text-blue-600">{summary.equations_total}</div>
          <div className="text-sm text-gray-600">Equations</div>
        </div>
        
        <div className="bg-green-50 p-4 rounded-lg">
          <div className="text-3xl font-bold text-green-600">{summary.logic_total}</div>
          <div className="text-sm text-gray-600">Logic Formulas</div>
        </div>
        
        <div className="bg-purple-50 p-4 rounded-lg">
          <div className="text-3xl font-bold text-purple-600">{summary.srs_total}</div>
          <div className="text-sm text-gray-600">SRS Requirements</div>
        </div>
        
        <div className="bg-red-50 p-4 rounded-lg">
          <div className="text-3xl font-bold text-red-600">{summary.errors_total}</div>
          <div className="text-sm text-gray-600">Errors</div>
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <h3 className="font-semibold mb-2">Equations by Type</h3>
          <div className="space-y-1">
            {Object.entries(summary.equations_by_type || {}).map(([type, count]) => (
              <div key={type} className="flex justify-between text-sm">
                <span className="text-gray-600">{type}</span>
                <span className="font-medium">{count}</span>
              </div>
            ))}
          </div>
        </div>
        
        <div>
          <h3 className="font-semibold mb-2">Symbols</h3>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Declared</span>
              <span className="font-medium">{summary.total_declared_symbols}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Initialized</span>
              <span className="font-medium">{summary.total_initialized_symbols}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Defined</span>
              <span className="font-medium">{summary.total_defined_symbols}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SummaryTab
