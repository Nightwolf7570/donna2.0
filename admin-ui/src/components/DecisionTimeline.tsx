import { useState } from 'react'

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

const decisionStyles = {
  handled: 'decision-handled',
  scheduled: 'decision-scheduled',
  escalated: 'decision-escalated',
  rejected: 'decision-rejected',
}

// Demo timeline data
const demoDecisions: Decision[] = [
  {
    id: '1',
    callerName: 'Sarah Chen',
    company: 'Acme Corp',
    duration: '4:32',
    timestamp: new Date(Date.now() - 2 * 60000),
    summary: 'VP of Engineering requesting a product demo. Mentioned they\'re evaluating solutions for Q2.',
    decision: 'scheduled',
    decisionLabel: 'Scheduled meeting',
    reasoning: 'High-value prospect matching your target customer profile.',
    actionTaken: 'Meeting booked: Tuesday 2:00 PM',
  },
  {
    id: '2',
    callerName: 'Unknown Caller',
    company: null,
    duration: '1:15',
    timestamp: new Date(Date.now() - 15 * 60000),
    summary: 'Cold call pitching SEO services. No prior relationship.',
    decision: 'rejected',
    decisionLabel: 'Rejected politely',
    reasoning: 'Unsolicited sales call. Low relevance to current goals.',
    actionTaken: 'Declined and ended call professionally.',
  },
  {
    id: '3',
    callerName: 'Michael Torres',
    company: 'TechStart Inc',
    duration: '2:48',
    timestamp: new Date(Date.now() - 45 * 60000),
    summary: 'Existing customer asking about API rate limits and upgrade options.',
    decision: 'handled',
    decisionLabel: 'Handled automatically',
    reasoning: 'Standard support question. Found answer in knowledge base.',
    actionTaken: 'Provided rate limit info and sent upgrade pricing via email.',
  },
  {
    id: '4',
    callerName: 'Emily Watson',
    company: 'Design Studio',
    duration: '3:21',
    timestamp: new Date(Date.now() - 2 * 3600000),
    summary: 'Partner agency requesting urgent callback about delayed deliverables.',
    decision: 'escalated',
    decisionLabel: 'Escalated to you',
    reasoning: 'Urgent partner issue requiring your direct attention.',
    actionTaken: 'Marked as high priority. Notification sent.',
  },
  {
    id: '5',
    callerName: 'James Liu',
    company: 'Venture Capital',
    duration: '5:12',
    timestamp: new Date(Date.now() - 4 * 3600000),
    summary: 'Investor from Series A round checking in on quarterly progress.',
    decision: 'scheduled',
    decisionLabel: 'Scheduled meeting',
    reasoning: 'Existing investor relationship. Quarterly check-in is expected.',
    actionTaken: 'Meeting booked: Thursday 10:00 AM',
  },
]

export default function DecisionTimeline({ selectedCallId }: DecisionTimelineProps) {
  const [decisions] = useState<Decision[]>(demoDecisions)
  const [filter, setFilter] = useState<'all' | Decision['decision']>('all')

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
              className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${
                filter === f
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
                  className={`card p-5 animate-slide-up ${
                    selectedCallId === decision.id ? 'ring-2 ring-slate-400' : ''
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
                    <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${decisionStyles[decision.decision]}`}>
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

        {filteredDecisions.length === 0 && (
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
