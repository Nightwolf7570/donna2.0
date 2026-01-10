import { useState, useEffect, useRef } from 'react'
import { getApiClient } from '../api/client'

interface TranscriptMessage {
  id: string
  callSid: string
  speaker: 'caller' | 'assistant'
  text: string
  timestamp: Date
}

interface ActiveCall {
  callSid: string
  callerNumber: string
  callerName: string | null
  startedAt: Date
  status: 'ringing' | 'in-progress' | 'ended'
}

interface LiveCallViewProps {
  selectedCallId: string | null
  onCallSelect: (callId: string | null) => void
}

export default function LiveCallView({ selectedCallId, onCallSelect }: LiveCallViewProps) {
  const [activeCalls, setActiveCalls] = useState<ActiveCall[]>([])
  const [transcripts, setTranscripts] = useState<Map<string, TranscriptMessage[]>>(new Map())
  const [connected, setConnected] = useState(false)
  const [currentSpeaker, setCurrentSpeaker] = useState<'caller' | 'assistant' | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const transcriptEndRef = useRef<HTMLDivElement>(null)

  // Connect to WebSocket for live transcription
  useEffect(() => {
    const connectWs = () => {
      const ws = new WebSocket('ws://localhost:8000/ws/transcription')
      wsRef.current = ws

      ws.onopen = () => {
        setConnected(true)
        console.log('Live transcription connected')
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          const message: TranscriptMessage = {
            id: `${data.call_sid}-${Date.now()}`,
            callSid: data.call_sid,
            speaker: data.speaker || 'caller',
            text: data.transcript,
            timestamp: new Date(data.timestamp || Date.now()),
          }

          setCurrentSpeaker(message.speaker)
          
          // Clear speaker indicator after 2 seconds of no new messages
          setTimeout(() => setCurrentSpeaker(null), 2000)

          setTranscripts(prev => {
            const updated = new Map(prev)
            const existing = updated.get(data.call_sid) || []
            updated.set(data.call_sid, [...existing, message])
            return updated
          })

          // Add to active calls if not already there
          setActiveCalls(prev => {
            if (!prev.find(c => c.callSid === data.call_sid)) {
              return [...prev, {
                callSid: data.call_sid,
                callerNumber: 'Unknown',
                callerName: null,
                startedAt: new Date(),
                status: 'in-progress',
              }]
            }
            return prev
          })

          // Auto-select if no call selected
          if (!selectedCallId) {
            onCallSelect(data.call_sid)
          }
        } catch (e) {
          console.error('Failed to parse transcription:', e)
        }
      }

      ws.onclose = () => {
        setConnected(false)
        console.log('Live transcription disconnected')
        // Reconnect after 3 seconds
        setTimeout(connectWs, 3000)
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
    }

    connectWs()

    return () => {
      wsRef.current?.close()
    }
  }, [selectedCallId, onCallSelect])

  // Fetch active calls from API
  useEffect(() => {
    const fetchActiveCalls = async () => {
      try {
        const client = getApiClient()
        const calls = await client.getCallHistory(10)
        
        // Filter for recent/active calls
        const recentCalls = calls
          .filter((c: any) => {
            const callTime = new Date(c.timestamp)
            const now = new Date()
            const diffMins = (now.getTime() - callTime.getTime()) / 60000
            return diffMins < 60 // Last hour
          })
          .map((c: any): ActiveCall => ({
            callSid: c.callSid,
            callerNumber: c.callerNumber,
            callerName: c.identifiedName,
            startedAt: new Date(c.timestamp),
            status: c.outcome === 'in-progress' ? 'in-progress' : 'ended',
          }))

        setActiveCalls(prev => {
          // Merge with WebSocket-discovered calls
          const merged = [...prev]
          recentCalls.forEach((call: ActiveCall) => {
            if (!merged.find(c => c.callSid === call.callSid)) {
              merged.push(call)
            }
          })
          return merged
        })
      } catch (e) {
        console.error('Failed to fetch calls:', e)
      }
    }

    fetchActiveCalls()
    const interval = setInterval(fetchActiveCalls, 10000)
    return () => clearInterval(interval)
  }, [])

  // Auto-scroll transcript
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [transcripts])

  const selectedCall = activeCalls.find(c => c.callSid === selectedCallId)
  const selectedTranscripts = selectedCallId ? transcripts.get(selectedCallId) || [] : []

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit',
      second: '2-digit',
      hour12: true 
    })
  }

  const formatDuration = (startedAt: Date) => {
    const now = new Date()
    const diffSecs = Math.floor((now.getTime() - startedAt.getTime()) / 1000)
    const mins = Math.floor(diffSecs / 60)
    const secs = diffSecs % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">
            Live Call Monitor
          </h2>
          <div className="flex items-center gap-2 mt-1">
            <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
            <span className="text-xs text-gray-500">
              {connected ? 'Connected' : 'Reconnecting...'}
            </span>
          </div>
        </div>
        {activeCalls.filter(c => c.status === 'in-progress').length > 0 && (
          <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-700 rounded-full">
            {activeCalls.filter(c => c.status === 'in-progress').length} Active
          </span>
        )}
      </div>

      {/* Active Calls List */}
      {activeCalls.length > 0 && (
        <div className="mb-4 space-y-2">
          {activeCalls.slice(0, 3).map(call => (
            <button
              key={call.callSid}
              onClick={() => onCallSelect(call.callSid)}
              className={`w-full text-left p-3 rounded-lg border transition-all ${
                selectedCallId === call.callSid
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 bg-white hover:border-gray-300'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {call.status === 'in-progress' && (
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                  )}
                  <span className="font-medium text-gray-900 text-sm">
                    {call.callerName || call.callerNumber}
                  </span>
                </div>
                <span className="text-xs text-gray-500">
                  {formatDuration(call.startedAt)}
                </span>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Live Transcription Panel */}
      <div className="flex-1 card overflow-hidden flex flex-col">
        {selectedCall ? (
          <>
            {/* Call Header */}
            <div className="p-4 border-b border-gray-100 bg-gray-50">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-gray-900">
                    {selectedCall.callerName || selectedCall.callerNumber}
                  </h3>
                  <p className="text-xs text-gray-500">{selectedCall.callerNumber}</p>
                </div>
                <div className="flex items-center gap-3">
                  {/* Speaking Indicator */}
                  {currentSpeaker && selectedCallId && transcripts.get(selectedCallId)?.length ? (
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-100 rounded-full">
                      <div className="flex gap-0.5">
                        <div className="w-1 h-3 bg-blue-500 rounded-full animate-sound-wave" style={{ animationDelay: '0ms' }} />
                        <div className="w-1 h-3 bg-blue-500 rounded-full animate-sound-wave" style={{ animationDelay: '150ms' }} />
                        <div className="w-1 h-3 bg-blue-500 rounded-full animate-sound-wave" style={{ animationDelay: '300ms' }} />
                      </div>
                      <span className="text-xs font-medium text-blue-700">
                        {currentSpeaker === 'caller' ? 'Caller speaking' : 'Assistant speaking'}
                      </span>
                    </div>
                  ) : (
                    <span className="text-xs text-gray-400">Waiting for speech...</span>
                  )}
                </div>
              </div>
            </div>

            {/* Transcript */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {selectedTranscripts.length === 0 ? (
                <div className="h-full flex items-center justify-center text-gray-400">
                  <div className="text-center">
                    <svg className="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                    </svg>
                    <p className="text-sm">Listening for speech...</p>
                    <p className="text-xs mt-1">Transcription will appear here in real-time</p>
                  </div>
                </div>
              ) : (
                selectedTranscripts.map((msg, idx) => (
                  <div
                    key={msg.id}
                    className={`flex ${msg.speaker === 'assistant' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-2xl px-4 py-2 ${
                        msg.speaker === 'assistant'
                          ? 'bg-blue-500 text-white rounded-br-md'
                          : 'bg-gray-100 text-gray-900 rounded-bl-md'
                      } ${idx === selectedTranscripts.length - 1 ? 'animate-slide-up' : ''}`}
                    >
                      <p className="text-sm">{msg.text}</p>
                      <p className={`text-xs mt-1 ${
                        msg.speaker === 'assistant' ? 'text-blue-200' : 'text-gray-400'
                      }`}>
                        {formatTime(msg.timestamp)}
                      </p>
                    </div>
                  </div>
                ))
              )}
              <div ref={transcriptEndRef} />
            </div>
          </>
        ) : (
          <div className="h-full flex items-center justify-center text-gray-400">
            <div className="text-center">
              <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
              </svg>
              <p className="text-sm font-medium">No active call selected</p>
              <p className="text-xs mt-1">Select a call or wait for incoming calls</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
