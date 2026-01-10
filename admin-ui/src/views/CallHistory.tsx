import { useState, useEffect } from 'react'
import { getApiClient } from '../api/client'
import type { CallRecord } from '../types'

export default function CallHistory() {
  const [calls, setCalls] = useState<CallRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterStatus, setFilterStatus] = useState<string>('all')

  useEffect(() => {
    fetchCalls()
  }, [])

  const fetchCalls = async () => {
    setLoading(true)
    try {
      const client = getApiClient()
      const data = await client.getCallHistory(100)
      setCalls(data)
      setError(null)
    } catch (e) {
      console.error('Failed to fetch calls:', e)
      setError('Failed to load call history')
    } finally {
      setLoading(false)
    }
  }

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const formatTimestamp = (date: Date) => {
    return new Date(date).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    })
  }

  const getOutcomeStyle = (outcome: string) => {
    switch (outcome) {
      case 'connected': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
      case 'voicemail': return 'bg-amber-500/20 text-amber-400 border-amber-500/30'
      case 'missed': return 'bg-red-500/20 text-red-400 border-red-500/30'
      case 'rejected': return 'bg-gray-500/20 text-gray-400 border-gray-500/30'
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30'
    }
  }

  const filteredCalls = calls.filter(call => {
    const matchesSearch = call.callerNumber.includes(searchQuery) || 
                         call.identifiedName?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         call.callPurpose?.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesFilter = filterStatus === 'all' || call.outcome === filterStatus
    return matchesSearch && matchesFilter
  })

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[#6366f1] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-[#a0a0b0]">Loading call history...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 animate-slide-up">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">Call History</h1>
          <p className="text-[#a0a0b0] mt-1">View and manage all incoming calls handled by Donna.</p>
        </div>
        <button onClick={fetchCalls} className="btn-primary flex items-center gap-2">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400">
          {error}
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <div className="flex-1 relative">
          <svg className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-[#a0a0b0]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            placeholder="Search by name, number, or purpose..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input pl-10"
          />
        </div>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="input w-48"
        >
          <option value="all">All Outcomes</option>
          <option value="connected">Connected</option>
          <option value="voicemail">Voicemail</option>
          <option value="missed">Missed</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        {filteredCalls.length === 0 ? (
          <div className="p-12 text-center">
            <div className="w-16 h-16 rounded-full bg-[#1a1a24] flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-[#a0a0b0]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
              </svg>
            </div>
            <p className="text-[#a0a0b0]">No calls found</p>
            <p className="text-sm text-[#6a6a7a] mt-1">Calls will appear here when received</p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-[#2a2a3a] bg-[#12121a]">
                <th className="text-left p-4 text-sm font-medium text-[#a0a0b0]">Caller</th>
                <th className="text-left p-4 text-sm font-medium text-[#a0a0b0]">Purpose</th>
                <th className="text-left p-4 text-sm font-medium text-[#a0a0b0]">Outcome</th>
                <th className="text-left p-4 text-sm font-medium text-[#a0a0b0]">Duration</th>
                <th className="text-left p-4 text-sm font-medium text-[#a0a0b0]">Time</th>
                <th className="text-right p-4 text-sm font-medium text-[#a0a0b0]">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredCalls.map((call) => (
                <tr key={call.callSid} className="table-row">
                  <td className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#6366f1] to-[#8b5cf6] flex items-center justify-center text-white font-medium">
                        {(call.identifiedName || call.callerNumber).charAt(0)}
                      </div>
                      <div>
                        <p className="font-medium text-white">{call.identifiedName || 'Unknown'}</p>
                        <p className="text-sm text-[#a0a0b0]">{call.callerNumber}</p>
                      </div>
                    </div>
                  </td>
                  <td className="p-4">
                    <span className="text-[#a0a0b0]">{call.callPurpose || '—'}</span>
                  </td>
                  <td className="p-4">
                    <span className={`px-3 py-1 text-xs font-medium rounded-full border ${getOutcomeStyle(call.outcome)}`}>
                      {call.outcome}
                    </span>
                  </td>
                  <td className="p-4 text-[#a0a0b0]">{formatDuration(call.duration)}</td>
                  <td className="p-4 text-[#a0a0b0]">{formatTimestamp(call.timestamp)}</td>
                  <td className="p-4 text-right">
                    <button className="p-2 hover:bg-[#1a1a24] rounded-lg transition-colors text-[#a0a0b0] hover:text-white">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
