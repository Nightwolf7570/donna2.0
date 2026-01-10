import { useState, useEffect } from 'react'
import { getApiClient } from '../api/client'

interface QueueItem {
  id: string
  callerName: string
  company: string | null
  callType: 'question' | 'pitch' | 'scheduling' | 'unknown'
  priority: 'high' | 'medium' | 'low'
  timestamp: Date
  isActive: boolean
}

interface CallQueueProps {
  selectedId: string | null
  onSelect: (id: string | null) => void
}

const callTypeLabels = {
  question: 'Question',
  pitch: 'Pitch',
  scheduling: 'Scheduling',
  unknown: 'Unknown',
}

const priorityStyles = {
  high: 'priority-high',
  medium: 'priority-medium',
  low: 'priority-low',
}



export default function CallQueue({ selectedId, onSelect }: CallQueueProps) {
  const [queue, setQueue] = useState<QueueItem[]>([])

  useEffect(() => {
    const fetchCalls = async () => {
      try {
        const client = getApiClient()
        const healthy = await client.checkHealth()
        if (!healthy) return

        const calls = await client.getCallHistory(10)
        if (calls.length > 0) {
          setQueue(calls.map((call: any) => ({
            id: call.callSid,
            callerName: call.identifiedName || call.callerNumber || 'Unknown Caller',
            company: null,
            callType: inferCallType(call.callPurpose),
            priority: inferPriority(call.outcome),
            timestamp: new Date(call.timestamp),
            isActive: call.outcome === 'in-progress',
          })))
        }
      } catch (e) {
        console.error("Failed to fetch call queue", e)
      }
    }

    fetchCalls()
    const interval = setInterval(fetchCalls, 30000)
    return () => clearInterval(interval)
  }, [])

  const inferCallType = (purpose: string | null): QueueItem['callType'] => {
    if (!purpose) return 'unknown'
    const p = purpose.toLowerCase()
    if (p.includes('schedule') || p.includes('meeting') || p.includes('book')) return 'scheduling'
    if (p.includes('pitch') || p.includes('sell') || p.includes('offer')) return 'pitch'
    if (p.includes('question') || p.includes('ask') || p.includes('help')) return 'question'
    return 'unknown'
  }

  const inferPriority = (outcome: string): QueueItem['priority'] => {
    if (outcome === 'escalated' || outcome === 'in-progress') return 'high'
    if (outcome === 'scheduled' || outcome === 'connected') return 'medium'
    return 'low'
  }

  const formatTime = (date: Date): string => {
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`

    const diffHours = Math.floor(diffMins / 60)
    if (diffHours < 24) return `${diffHours}h ago`

    return date.toLocaleDateString()
  }

  return (
    <div className="h-full flex flex-col">
      <div className="mb-4">
        <h2 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">
          Live Reception Queue
        </h2>
        <p className="text-xs text-gray-500 mt-1">
          {queue.filter(q => q.isActive).length} active · {queue.length} total
        </p>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 pr-1">
        {queue.map((item) => (
          <button
            key={item.id}
            onClick={() => onSelect(selectedId === item.id ? null : item.id)}
            className={`w-full text-left card p-4 transition-all ${selectedId === item.id
              ? 'ring-2 ring-slate-400 ring-offset-2'
              : 'hover:border-gray-300'
              } ${item.isActive ? 'border-l-4 border-l-green-500' : ''}`}
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-900 truncate">
                  {item.callerName}
                </p>
                {item.company && (
                  <p className="text-sm text-gray-500 truncate">{item.company}</p>
                )}
              </div>
              <span className={`ml-2 px-2 py-0.5 text-xs font-medium rounded-full ${priorityStyles[item.priority]}`}>
                {item.priority}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                {callTypeLabels[item.callType]}
              </span>
              <span className="text-xs text-gray-400">
                {formatTime(item.timestamp)}
              </span>
            </div>

            {item.isActive && (
              <div className="mt-3 flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span className="text-xs text-green-600 font-medium">Active call</span>
              </div>
            )}
          </button>
        ))}

        {queue.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <svg className="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
            </svg>
            <p className="text-sm">No calls in queue</p>
          </div>
        )}
      </div>
    </div>
  )
}
