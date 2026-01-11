import { useState } from 'react'

interface CalendarEvent {
  id: string
  title: string
  time: string
  bookedBy: 'frontdesk' | 'user' | 'rescheduled' | null
  isToday: boolean
}

interface Alert {
  id: string
  type: 'priority' | 'change' | 'reminder'
  message: string
  timestamp: Date
}

interface AIControl {
  id: string
  label: string
  description: string
  enabled: boolean
}

// Demo data
const demoEvents: CalendarEvent[] = [
  { id: '1', title: 'Sarah Chen - Product Demo', time: '2:00 PM', bookedBy: 'frontdesk', isToday: true },
  { id: '2', title: 'Team Standup', time: '3:30 PM', bookedBy: 'user', isToday: true },
  { id: '3', title: 'James Liu - Investor Check-in', time: '10:00 AM', bookedBy: 'frontdesk', isToday: false },
  { id: '4', title: 'Design Review', time: '11:30 AM', bookedBy: 'rescheduled', isToday: false },
]

const demoAlerts: Alert[] = [
  { id: '1', type: 'priority', message: 'High-priority caller Emily Watson attempted to reach you', timestamp: new Date(Date.now() - 30 * 60000) },
  { id: '2', type: 'change', message: 'Meeting with Alex moved to 3:30 PM', timestamp: new Date(Date.now() - 2 * 3600000) },
  { id: '3', type: 'reminder', message: 'Call with Sarah Chen in 15 minutes', timestamp: new Date(Date.now() - 15 * 60000) },
]

const defaultControls: AIControl[] = [
  { id: 'auto-schedule', label: 'Auto-schedule meetings', description: 'Let Front Desk book meetings on your behalf', enabled: true },
  { id: 'screen-sales', label: 'Screen sales calls', description: 'Automatically filter unsolicited pitches', enabled: true },
  { id: 'high-priority', label: 'Notify only high priority', description: 'Reduce interruptions for low-priority calls', enabled: false },
]

export default function CalendarAlerts() {
  const [events] = useState<CalendarEvent[]>(demoEvents)
  const [alerts] = useState<Alert[]>(demoAlerts)
  const [controls, setControls] = useState<AIControl[]>(defaultControls)

  const todayEvents = events.filter(e => e.isToday)
  const upcomingEvents = events.filter(e => !e.isToday)

  const toggleControl = (id: string) => {
    setControls(controls.map(c =>
      c.id === id ? { ...c, enabled: !c.enabled } : c
    ))
  }

  const getBookedByLabel = (bookedBy: CalendarEvent['bookedBy']) => {
    switch (bookedBy) {
      case 'frontdesk': return 'Booked by Front Desk'
      case 'rescheduled': return 'Rescheduled automatically'
      default: return null
    }
  }

  const getAlertIcon = (type: Alert['type']) => {
    switch (type) {
      case 'priority':
        return (
          <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
            <svg className="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
        )
      case 'change':
        return (
          <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
            <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
        )
      case 'reminder':
        return (
          <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0">
            <svg className="w-4 h-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        )
    }
  }

  const formatAlertTime = (date: Date): string => {
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`

    const diffHours = Math.floor(diffMins / 60)
    return `${diffHours}h ago`
  }

  return (
    <div className="h-full flex flex-col space-y-6 overflow-y-auto">
      {/* Upcoming Schedule */}
      <section>
        <h2 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-3">
          Upcoming Schedule
        </h2>

        <div className="card divide-y divide-gray-100">
          {/* Today */}
          {todayEvents.length > 0 && (
            <div className="p-3">
              <p className="text-xs font-medium text-gray-400 uppercase mb-2">Today</p>
              <div className="space-y-2">
                {todayEvents.map(event => (
                  <div key={event.id} className="flex items-start gap-3">
                    <span className="text-sm font-medium text-gray-900 w-16">{event.time}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-700 truncate">{event.title}</p>
                      {getBookedByLabel(event.bookedBy) && (
                        <p className="text-xs text-blue-600">{getBookedByLabel(event.bookedBy)}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tomorrow / Upcoming */}
          {upcomingEvents.length > 0 && (
            <div className="p-3">
              <p className="text-xs font-medium text-gray-400 uppercase mb-2">Tomorrow</p>
              <div className="space-y-2">
                {upcomingEvents.map(event => (
                  <div key={event.id} className="flex items-start gap-3">
                    <span className="text-sm font-medium text-gray-900 w-16">{event.time}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-700 truncate">{event.title}</p>
                      {getBookedByLabel(event.bookedBy) && (
                        <p className="text-xs text-blue-600">{getBookedByLabel(event.bookedBy)}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {events.length === 0 && (
            <div className="p-6 text-center text-gray-500">
              <p className="text-sm">No upcoming events</p>
            </div>
          )}
        </div>
      </section>

      {/* Important Alerts */}
      <section>
        <h2 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-3">
          Important Alerts
        </h2>

        <div className="space-y-2">
          {alerts.map(alert => (
            <div key={alert.id} className="card p-3 flex items-start gap-3">
              {getAlertIcon(alert.type)}
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-700">{alert.message}</p>
                <p className="text-xs text-gray-400 mt-1">{formatAlertTime(alert.timestamp)}</p>
              </div>
            </div>
          ))}

          {alerts.length === 0 && (
            <div className="card p-6 text-center text-gray-500">
              <p className="text-sm">No alerts</p>
            </div>
          )}
        </div>
      </section>

      {/* AI Behavior Controls */}
      <section>
        <h2 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-3">
          AI Behavior
        </h2>

        <div className="card divide-y divide-gray-100">
          {controls.map(control => (
            <div key={control.id} className="p-3 flex items-center justify-between">
              <div className="flex-1 min-w-0 pr-4">
                <p className="text-sm font-medium text-gray-900">{control.label}</p>
                <p className="text-xs text-gray-500 mt-0.5">{control.description}</p>
              </div>
              <button
                onClick={() => toggleControl(control.id)}
                className={`toggle ${control.enabled ? 'active' : ''}`}
                aria-label={`Toggle ${control.label}`}
              />
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
