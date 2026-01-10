import { useState } from 'react'
import TopNav from './components/TopNav'
import CallQueue from './components/CallQueue'
import DecisionTimeline from './components/DecisionTimeline'
import CalendarAlerts from './components/CalendarAlerts'

export type StatusMode = 'on-duty' | 'quiet-hours' | 'do-not-disturb'

function App() {
  const [status, setStatus] = useState<StatusMode>('on-duty')
  const [selectedCallId, setSelectedCallId] = useState<string | null>(null)

  return (
    <div className="min-h-screen bg-[#f8f9fa] flex flex-col">
      <TopNav status={status} onStatusChange={setStatus} />
      
      <main className="flex-1 flex justify-center px-6 py-6">
        <div className="w-full max-w-[1400px] flex gap-6 h-[calc(100vh-88px)]">
          {/* Left Column - 25% */}
          <div className="w-1/4 min-w-[280px]">
            <CallQueue 
              selectedId={selectedCallId} 
              onSelect={setSelectedCallId} 
            />
          </div>
          
          {/* Center Column - 50% */}
          <div className="w-1/2 min-w-[500px]">
            <DecisionTimeline selectedCallId={selectedCallId} />
          </div>
          
          {/* Right Column - 25% */}
          <div className="w-1/4 min-w-[280px]">
            <CalendarAlerts />
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
