import { useState } from 'react'
import Sidebar from './components/Sidebar'
import TopNav from './components/TopNav'
import Dashboard from './views/Dashboard'
import Emails from './views/Emails'
import LiveCallView from './components/LiveCallView'

export type StatusMode = 'on-duty' | 'quiet-hours' | 'do-not-disturb'

function App() {
  const [status, setStatus] = useState<StatusMode>('on-duty')
  const [currentView, setCurrentView] = useState('dashboard')

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard />
      case 'emails':
        return <Emails />
      case 'calls':
        return <LiveCallView selectedCallId={null} onCallSelect={() => { }} />
      default:
        return <Dashboard />
    }
  }

  return (
    <div className="min-h-screen bg-[#f8f9fa] flex font-sans">
      <Sidebar
        currentView={currentView} // @ts-ignore
        onViewChange={(view) => setCurrentView(view)}
      />

      <div className="flex-1 flex flex-col min-w-0 h-screen">
        <TopNav status={status} onStatusChange={setStatus} />

        <main className="flex-1 p-6 overflow-hidden">
          {renderView()}
        </main>
      </div>
    </div>
  )
}

export default App
