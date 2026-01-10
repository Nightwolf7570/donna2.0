import { useState, useEffect } from 'react'

interface QuickStat {
  label: string
  value: string | number
  icon: string
}

export default function Dashboard() {
  const [stats, setStats] = useState<QuickStat[]>([
    { label: 'Calls Today', value: 0, icon: '📞' },
    { label: 'Total Contacts', value: 0, icon: '👥' },
    { label: 'Emails Indexed', value: 0, icon: '📧' },
    { label: 'Avg Response Time', value: '0s', icon: '⏱️' },
  ])
  const [recentCalls, setRecentCalls] = useState<Array<{
    id: string
    caller: string
    time: string
    status: string
  }>>([])

  useEffect(() => {
    // Placeholder for fetching dashboard data
    // Will be connected to API client in task 11.2
    setStats([
      { label: 'Calls Today', value: 12, icon: '📞' },
      { label: 'Total Contacts', value: 156, icon: '👥' },
      { label: 'Emails Indexed', value: 1243, icon: '📧' },
      { label: 'Avg Response Time', value: '1.2s', icon: '⏱️' },
    ])
    
    setRecentCalls([
      { id: '1', caller: 'John Smith', time: '10:30 AM', status: 'Connected' },
      { id: '2', caller: 'Unknown', time: '10:15 AM', status: 'Voicemail' },
      { id: '3', caller: 'Sarah Johnson', time: '9:45 AM', status: 'Connected' },
    ])
  }, [])

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>
      
      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map((stat, index) => (
          <div key={index} className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="flex items-center gap-3">
              <span className="text-2xl">{stat.icon}</span>
              <div>
                <p className="text-sm text-gray-500">{stat.label}</p>
                <p className="text-xl font-semibold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Recent Calls */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Recent Calls</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {recentCalls.length === 0 ? (
            <div className="p-4 text-center text-gray-500">No recent calls</div>
          ) : (
            recentCalls.map((call) => (
              <div key={call.id} className="p-4 flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">{call.caller}</p>
                  <p className="text-sm text-gray-500">{call.time}</p>
                </div>
                <span className={`px-2 py-1 text-xs rounded-full ${
                  call.status === 'Connected' 
                    ? 'bg-green-100 text-green-700' 
                    : 'bg-yellow-100 text-yellow-700'
                }`}>
                  {call.status}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
      
      {/* System Status */}
      <div className="mt-6 bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">System Status</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatusIndicator label="API Server" status="online" />
          <StatusIndicator label="Twilio" status="online" />
          <StatusIndicator label="Deepgram" status="online" />
          <StatusIndicator label="MongoDB" status="online" />
        </div>
      </div>
    </div>
  )
}

function StatusIndicator({ label, status }: { label: string; status: 'online' | 'offline' | 'warning' }) {
  const statusColors = {
    online: 'bg-green-500',
    offline: 'bg-red-500',
    warning: 'bg-yellow-500',
  }
  
  return (
    <div className="flex items-center gap-2">
      <span className={`w-2 h-2 rounded-full ${statusColors[status]}`}></span>
      <span className="text-sm text-gray-600">{label}</span>
    </div>
  )
}
