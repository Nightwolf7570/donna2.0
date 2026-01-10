import { useState, useEffect } from 'react'
import { getApiClient } from '../api/client'

interface Decision {
  id: string
  callerName: string
  company: string | null
  duration: string
  timestamp: Date
  summary: string
  decision: 'handled' | 'scheduled' | 'escalated' | 'rejected'
  decisionLabel: string
  reasoning: string
  actionTaken: string
}

interface DecisionTimelineProps {
  selectedCallId: string | null
}

const decisionStyles: Record<string, string> = {
  handled: 'decision-handled',
  scheduled: 'decision-scheduled',
  escalated: 'decision-escalated',
  rejected: 'decision-rejected',
}

export default function DecisionTimeline({ selectedCallId }: DecisionTimelineProps) {
  const [decisions, setDecisions] = useState<Decision[]>([])
  const [filter, setFilter] = useState<'all' | Decision['decision']>('all')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchDecisions = async () => {
      try {
        const client = getApiClient()
        const calls = await client.getCallHistory(50)

        const mappedDecisions: Decision[] = calls.map((call: any) => ({
          id: call.call_sid,
          callerName: call.identified_name || call.caller_number,
          company: call.company || null,
          duration: formatDuration(call.duration),
          timestamp: new Date(call.timestamp),
          summary: call.summary || 'No summary available',
          decision: (call.decision?.toLowerCase() as Decision['decision']) || 'handled',
          decisionLabel: call.decision_label || 'Processed',
          reasoning: call.reasoning || 'No details provided',
          actionTaken: call.action_taken || 'Call logged',
        }))

        setDecisions(mappedDecisions)
      } catch (err) {
        console.error('Error fetching decisions:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchDecisions()

    // Refresh every 30 seconds
    const interval = setInterval(fetchDecisions, 30000)
    return () => clearInterval(interval)
  }, [])

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const filteredDecisions = filter === 'all'
    ? decisions
    : decisions.filter(d => d.decision === filter)

  const formatTime = (date: Date): string => {
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    })
  }

  const formatDate = (date: Date): string => {
    const today = new Date()
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)

    if (date.toDateString() === today.toDateString()) return 'Today'
    if (date.toDateString() === yesterday.toDateString()) return 'Yesterday'
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  // Group decisions by date
  const groupedDecisions = filteredDecisions.reduce((groups, decision) => {
    const dateKey = formatDate(decision.timestamp)
    if (!groups[dateKey]) groups[dateKey] = []
    groups[dateKey].push(decision)
    return groups
  }, {} as Record<string, Decision[]>)

  if (loading && decisions.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-gray-400">
        <div className="flex flex-col items-center gap-2">
          <svg className="animate-spin h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span className="text-sm">Loading timeline...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">
            Decision Timeline
          </h2>
          <p className="text-xs text-gray-500 mt-1">
            How Front Desk is handling your calls
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex gap-1">
          {(['all', 'handled', 'scheduled', 'escalated', 'rejected'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${filter === f
                ? 'bg-slate-800 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
            >
              {f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Timeline */}
      <div className="flex-1 overflow-y-auto pr-2">
        {Object.entries(groupedDecisions).map(([dateLabel, items]) => (
          <div key={dateLabel} className="mb-6">
            <div className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-3">
              {dateLabel}
            </div>

            <div className="space-y-4">
              {items.map((decision, idx) => (
                <div
                  key={decision.id}
                  className={`card p-5 animate-slide-up ${selectedCallId === decision.id ? 'ring-2 ring-slate-400' : ''
                    }`}
                  style={{ animationDelay: `${idx * 50}ms` }}
                >
                  {/* Header */}
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium text-gray-900">{decision.callerName}</h3>
                        {decision.company && (
                          <span className="text-sm text-gray-500">· {decision.company}</span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 mt-1 text-xs text-gray-400">
                        <span>{formatTime(decision.timestamp)}</span>
                        <span>·</span>
                        <span>{decision.duration}</span>
                      </div>
                    </div>
                    <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${decisionStyles[decision.decision] || decisionStyles.handled}`}>
                      {decision.decisionLabel}
                    </span>
                  </div>

                  {/* Summary */}
                  <p className="text-sm text-gray-700 mb-4 leading-relaxed">
                    {decision.summary}
                  </p>

                  {/* Reasoning & Action */}
                  <div className="space-y-2 pt-3 border-t border-gray-100">
                    <div className="flex items-start gap-2">
                      <svg className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                      <p className="text-xs text-gray-500">{decision.reasoning}</p>
                    </div>
                    <div className="flex items-start gap-2">
                      <svg className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <p className="text-xs text-gray-600 font-medium">{decision.actionTaken}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}

        {decisions.length === 0 && (
          <div className="text-center py-16 text-gray-500">
            <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <p className="text-sm">No decisions to show</p>
            <p className="text-xs text-gray-400 mt-1">Calls will appear here as they're handled</p>
          </div>
        )}
      </div>
    </div>
  )
}
