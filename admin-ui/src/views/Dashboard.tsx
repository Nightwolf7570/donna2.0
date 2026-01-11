import { useState } from 'react'
import CallQueue from '../components/CallQueue'
import DecisionTimeline from '../components/DecisionTimeline'
import LiveCallView from '../components/LiveCallView'

export default function Dashboard() {
  const [selectedCallId, setSelectedCallId] = useState<string | null>(null)

  return (
    <div className="w-full max-w-[1600px] flex gap-6 h-[calc(100vh-88px)] mx-auto">
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

      {/* Right Column - 25% - Live Transcription */}
      <div className="w-1/4 min-w-[280px]">
        <LiveCallView
          selectedCallId={selectedCallId}
          onCallSelect={setSelectedCallId}
        />
      </div>
    </div>
  )
}
