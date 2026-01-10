import { useState, useEffect } from 'react'
import { getApiClient } from '../api/client'

interface CalendarEventDisplay {
  id: string
  title: string
  time: string
  bookedBy: 'frontdesk' | 'user' | 'rescheduled'
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

const defaultControls: AIControl[] = [
  { id: 'auto-schedule', label: 'Auto-schedule meetings', description: 'Let Front Desk book meetings on your behalf', enabled: true },
  { id: 'screen-sales', label: 'Screen sales calls', description: 'Automatically filter unsolicited pitches', enabled: true },
  { id: 'high-priority', label: 'Notify only high priority', description: 'Reduce interruptions for low-priority calls', enabled: false },
]

export default function CalendarAlerts() {
  const [events, setEvents] = useState<CalendarEventDisplay[]>([])
  const [alerts] = useState<Alert[]>([]) // Keeping mock alerts for now as backend doesn't serve them yet
  const [controls, setControls] = useState<AIControl[]>(defaultControls)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const client = getApiClient()
        // Check auth first - if not authenticated, we can't fetch events
        // const authStatus = await client.getGoogleAuthStatus()
        // if (!authStatus.authenticated) return 

        const apiEvents = await client.getCalendarEvents()

        const mappedEvents: CalendarEventDisplay[] = apiEvents.map(evt => {
          // Parse start time
          let dateObj: Date
          // Handle 'dateTime' (timed) vs 'date' (all day)
          if ('dateTime' in evt.start) {
            dateObj = new Date(evt.start.dateTime)
          } else {
            dateObj = new Date(evt.start.date) // All day
          }

          const now = new Date()
          const isToday = dateObj.toDateString() === now.toDateString()

          // Format time: "10:00 AM" or "All Day"
          const timeStr = 'dateTime' in evt.start
            ? dateObj.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
            : 'All Day'

          // Simple heuristic for bookedBy (could be improved with real metadata)
          const bookedBy = evt.description?.includes('Donna') ? 'frontdesk' : 'user'

          return {
            id: evt.id,
            title: evt.summary,
            time: timeStr,
            bookedBy,
            isToday
          }
        })

        setEvents(mappedEvents)
      } catch (error) {
        console.error("Failed to fetch calendar events:", error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchEvents()
  }, [])

  const todayEvents = events.filter(e => e.isToday)
  const upcomingEvents = events.filter(e => !e.isToday)

  const toggleControl = (id: string) => {
    setControls(controls.map(c =>
      c.id === id ? { ...c, enabled: !c.enabled } : c
    ))
  }

  const getBookedByLabel = (bookedBy: CalendarEventDisplay['bookedBy']) => {
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
          {isLoading ? (
            <div className="p-6 text-center text-gray-400">
              <span className="inline-block animate-spin rounded-full h-4 w-4 border-2 border-current border-t-transparent mr-2"></span>
              Loading events...
            </div>
          ) : (
            <>
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
                  <p className="text-sm">No upcoming events found</p>
                </div>
              )}
            </>
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
