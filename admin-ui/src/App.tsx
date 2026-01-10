import { useState } from 'react'
import Sidebar from './components/Sidebar'
import Dashboard from './views/Dashboard'

type View = 'dashboard' | 'calls' | 'contacts' | 'emails' | 'settings'

function App() {
  const [currentView, setCurrentView] = useState<View>('dashboard')

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard />
      case 'calls':
        return <div className="p-6"><h1 className="text-2xl font-bold">Call History</h1><p className="text-gray-600 mt-2">Coming soon...</p></div>
      case 'contacts':
        return <div className="p-6"><h1 className="text-2xl font-bold">Contact Manager</h1><p className="text-gray-600 mt-2">Coming soon...</p></div>
      case 'emails':
        return <div className="p-6"><h1 className="text-2xl font-bold">Email Manager</h1><p className="text-gray-600 mt-2">Coming soon...</p></div>
      case 'settings':
        return <div className="p-6"><h1 className="text-2xl font-bold">Settings</h1><p className="text-gray-600 mt-2">Coming soon...</p></div>
      default:
        return <Dashboard />
    }
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar currentView={currentView} onViewChange={setCurrentView} />
      <main className="flex-1 overflow-auto">
        {renderView()}
      </main>
    </div>
  )
}

export default App
