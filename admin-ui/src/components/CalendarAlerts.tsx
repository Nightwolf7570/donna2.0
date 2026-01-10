import { useState, useEffect } from 'react'
import { getApiClient } from '../api/client'

interface CalendarEventDisplay {
  id: string
  title: string
  time: string
  bookedBy: 'frontdesk' | 'user' | 'rescheduled'
  isToday: boolean
}

export default function CalendarAlerts() {
  const [events, setEvents] = useState<CalendarEventDisplay[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const client = getApiClient()
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

  const getBookedByLabel = (bookedBy: CalendarEventDisplay['bookedBy']) => {
    switch (bookedBy) {
      case 'frontdesk': return 'Booked by Front Desk'
      case 'rescheduled': return 'Rescheduled automatically'
      default: return null
    }
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
    </div>
  )
}
