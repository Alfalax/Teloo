import { useState } from 'react'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          TeLOO Admin V3
        </h1>
        <p className="text-lg text-gray-600 mb-8">
          Marketplace Inteligente de Repuestos Automotrices
        </p>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <button
            className="bg-amber-500 hover:bg-amber-600 text-white font-bold py-2 px-4 rounded"
            onClick={() => setCount((count) => count + 1)}
          >
            Count is {count}
          </button>
          <p className="mt-4 text-sm text-gray-500">
            Panel administrativo en desarrollo
          </p>
        </div>
      </div>
    </div>
  )
}

export default App