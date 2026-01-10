import { useState, useEffect } from 'react'
import { getApiClient } from '../api/client'
import type { CallRecord } from '../types'

interface StatCard {
  label: string
  value: string | number
  change?: string
  trend?: 'up' | 'down'
  icon: React.ReactNode
}

interface DashboardStats {
  callsToday: number
  totalContacts: number
  emailsIndexed: number
  avgResponseTime: number
}

export default function Dashboard() {
  const [stats, setStats] = useState<StatCard[]>([])
  const [recentCalls, setRecentCalls] = useState<Array<{
    id: string
    caller: string
    time: string
    duration: string
    status: 'connected' | 'voicemail' | 'missed'
  }>>([])
  const [isLive, setIsLive] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      const client = getApiClient()
      
      try {
        // Check server health
        const healthy = await client.checkHealth()
        setIsLive(healthy)
        
        if (!healthy) {
          setError('Server is offline')
          setLoading(false)
          return
        }

        // Fetch dashboard stats
        let dashboardStats: DashboardStats = {
          callsToday: 0,
          totalContacts: 0,
          emailsIndexed: 0,
          avgResponseTime: 0
        }
        
        try {
          dashboardStats = await client.getDashboardStats()
        } catch (e) {
          console.warn('Failed to fetch stats:', e)
        }

        setStats([
          { 
            label: 'Calls Today', 
            value: dashboardStats.callsToday, 
            icon: (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
              </svg>
            )
          },
          { 
            label: 'Contacts', 
            value: dashboardStats.totalContacts, 
            icon: (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            )
          },
          { 
            label: 'Emails Indexed', 
            value: dashboardStats.emailsIndexed, 
            icon: (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            )
          },
          { 
            label: 'Avg Response', 
            value: `${dashboardStats.avgResponseTime.toFixed(1)}s`, 
            icon: (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            )
          },
        ])

        // Fetch recent calls
        try {
          const calls = await client.getCallHistory(5)
          setRecentCalls(calls.map((call: CallRecord) => ({
            id: call.callSid,
            caller: call.identifiedName || call.callerNumber,
            time: formatTimeAgo(new Date(call.timestamp)),
            duration: formatDuration(call.duration),
            status: mapOutcome(call.outcome)
          })))
        } catch (e) {
          console.warn('Failed to fetch calls:', e)
          setRecentCalls([])
        }

        setError(null)
      } catch (e) {
        console.error('Dashboard fetch error:', e)
        setError('Failed to load dashboard data')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  const formatTimeAgo = (date: Date): string => {
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    
    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins} min ago`
    
    const diffHours = Math.floor(diffMins / 60)
    if (diffHours < 24) return `${diffHours} hr${diffHours > 1 ? 's' : ''} ago`
    
    const diffDays = Math.floor(diffHours / 24)
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
  }

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const mapOutcome = (outcome: string): 'connected' | 'voicemail' | 'missed' => {
    if (outcome === 'connected') return 'connected'
    if (outcome === 'voicemail') return 'voicemail'
    return 'missed'
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
      case 'voicemail': return 'bg-amber-500/20 text-amber-400 border-amber-500/30'
      case 'missed': return 'bg-red-500/20 text-red-400 border-red-500/30'
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30'
    }
  }

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[#6366f1] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-[#a0a0b0]">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 animate-slide-up">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">Dashboard</h1>
          <p className="text-[#a0a0b0] mt-1">Welcome back! Here's what's happening with Donna.</p>
        </div>
        <div className="flex items-center gap-3">
          <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${isLive ? 'bg-emerald-500/20 border border-emerald-500/30' : 'bg-red-500/20 border border-red-500/30'}`}>
            <div className={`w-2 h-2 rounded-full ${isLive ? 'bg-emerald-400 animate-pulse' : 'bg-red-400'}`}></div>
            <span className={`text-sm font-medium ${isLive ? 'text-emerald-400' : 'text-red-400'}`}>
              {isLive ? 'Live' : 'Offline'}
            </span>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400">
          {error}
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat, index) => (
          <div key={index} className="card p-6 group">
            <div className="flex items-start justify-between">
              <div className="p-3 rounded-xl bg-gradient-to-br from-[#6366f1]/20 to-[#8b5cf6]/20 text-[#8b5cf6] group-hover:scale-110 transition-transform">
                {stat.icon}
              </div>
              {stat.change && (
                <span className={`text-sm font-medium ${stat.trend === 'up' ? 'text-emerald-400' : 'text-emerald-400'}`}>
                  {stat.change}
                </span>
              )}
            </div>
            <div className="mt-4">
              <p className="text-3xl font-bold text-white">{stat.value}</p>
              <p className="text-sm text-[#a0a0b0] mt-1">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Calls */}
        <div className="lg:col-span-2 card">
          <div className="p-6 border-b border-[#2a2a3a] flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">Recent Calls</h2>
            <button className="text-sm text-[#6366f1] hover:text-[#8b5cf6] transition-colors">
              View All →
            </button>
          </div>
          <div className="divide-y divide-[#2a2a3a]">
            {recentCalls.length === 0 ? (
              <div className="p-8 text-center text-[#a0a0b0]">
                No calls yet. Calls will appear here when received.
              </div>
            ) : (
              recentCalls.map((call) => (
                <div key={call.id} className="p-4 flex items-center justify-between hover:bg-[#1a1a24] transition-colors">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#6366f1] to-[#8b5cf6] flex items-center justify-center text-white font-medium">
                      {call.caller.charAt(0)}
                    </div>
                    <div>
                      <p className="font-medium text-white">{call.caller}</p>
                      <p className="text-sm text-[#a0a0b0]">{call.time} • {call.duration}</p>
                    </div>
                  </div>
                  <span className={`px-3 py-1 text-xs font-medium rounded-full border ${getStatusColor(call.status)}`}>
                    {call.status}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* System Status */}
        <div className="card">
          <div className="p-6 border-b border-[#2a2a3a]">
            <h2 className="text-lg font-semibold text-white">System Status</h2>
          </div>
          <div className="p-6 space-y-4">
            <StatusItem label="API Server" status={isLive ? "operational" : "offline"} />
            <StatusItem label="Twilio Gateway" status={isLive ? "operational" : "unknown"} />
            <StatusItem label="Deepgram STT" status={isLive ? "operational" : "unknown"} />
            <StatusItem label="Fireworks AI" status={isLive ? "operational" : "unknown"} />
            <StatusItem label="MongoDB Atlas" status={isLive ? "operational" : "unknown"} />
            <StatusItem label="Voyage AI" status={isLive ? "operational" : "unknown"} />
          </div>
        </div>
      </div>
    </div>
  )
}

function StatusItem({ label, status }: { label: string; status: string }) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className={`w-2 h-2 rounded-full ${status === 'operational' ? 'bg-emerald-400 glow-success' : status === 'offline' ? 'bg-red-400' : 'bg-gray-400'}`}></div>
        <span className="text-sm text-white">{label}</span>
      </div>
      <span className={`text-xs ${status === 'operational' ? 'text-emerald-400' : status === 'offline' ? 'text-red-400' : 'text-[#a0a0b0]'}`}>
        {status}
      </span>
    </div>
  )
}
