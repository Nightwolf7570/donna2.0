import { useState, useEffect } from 'react'
import { getApiClient } from '../api/client'
import type { Email } from '../types'

export default function Emails() {
  const [emails, setEmails] = useState<Email[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null)

  useEffect(() => {
    fetchEmails()
  }, [])

  const fetchEmails = async () => {
    setLoading(true)
    try {
      const client = getApiClient()
      const data = await client.getEmails(100)
      setEmails(data)
      setError(null)
    } catch (e) {
      console.error('Failed to fetch emails:', e)
      setError('Failed to load emails')
    } finally {
      setLoading(false)
    }
  }

  const filteredEmails = emails.filter(email =>
    email.sender.toLowerCase().includes(searchQuery.toLowerCase()) ||
    email.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
    email.body.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this email?')) return
    
    try {
      const client = getApiClient()
      await client.deleteEmail(id)
      setEmails(emails.filter(e => e.id !== id))
      if (selectedEmail?.id === id) setSelectedEmail(null)
    } catch (e) {
      console.error('Failed to delete email:', e)
      alert('Failed to delete email')
    }
  }

  const formatTimestamp = (date: Date) => {
    return new Date(date).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    })
  }

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[#6366f1] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-[#a0a0b0]">Loading emails...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 animate-slide-up">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">Emails</h1>
          <p className="text-[#a0a0b0] mt-1">Indexed emails for context retrieval.</p>
        </div>
        <button onClick={fetchEmails} className="btn-primary flex items-center gap-2">
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

      {/* Search */}
      <div className="mb-6">
        <div className="relative max-w-md">
          <svg className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-[#a0a0b0]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            placeholder="Search emails..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input pl-10"
          />
        </div>
      </div>

      {filteredEmails.length === 0 ? (
        <div className="card p-12 text-center">
          <div className="w-16 h-16 rounded-full bg-[#1a1a24] flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-[#a0a0b0]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <p className="text-[#a0a0b0]">No emails indexed</p>
          <p className="text-sm text-[#6a6a7a] mt-1">Import emails to help Donna provide context during calls</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Email List */}
          <div className="lg:col-span-1 card overflow-hidden">
            <div className="p-4 border-b border-[#2a2a3a]">
              <span className="text-sm text-[#a0a0b0]">{filteredEmails.length} emails indexed</span>
            </div>
            <div className="divide-y divide-[#2a2a3a] max-h-[600px] overflow-y-auto">
              {filteredEmails.map((email) => (
                <div 
                  key={email.id} 
                  onClick={() => setSelectedEmail(email)}
                  className={`p-4 cursor-pointer transition-colors group ${
                    selectedEmail?.id === email.id 
                      ? 'bg-[#6366f1]/10 border-l-2 border-[#6366f1]' 
                      : 'hover:bg-[#1a1a24]'
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <p className="font-medium text-white text-sm truncate flex-1">{email.sender}</p>
                    <button 
                      onClick={(e) => { e.stopPropagation(); handleDelete(email.id) }}
                      className="p-1 hover:bg-red-500/20 rounded transition-colors text-[#a0a0b0] hover:text-red-400 opacity-0 group-hover:opacity-100"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                  <p className="text-sm text-white truncate mb-1">{email.subject}</p>
                  <p className="text-xs text-[#a0a0b0] truncate">{email.body}</p>
                  <p className="text-xs text-[#6366f1] mt-2">{formatTimestamp(email.timestamp)}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Email Preview */}
          <div className="lg:col-span-2 card">
            {selectedEmail ? (
              <div className="p-6">
                <div className="flex items-start justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-semibold text-white mb-2">{selectedEmail.subject}</h2>
                    <div className="flex items-center gap-4 text-sm text-[#a0a0b0]">
                      <span>From: <span className="text-[#8b5cf6]">{selectedEmail.sender}</span></span>
                      <span>{formatTimestamp(selectedEmail.timestamp)}</span>
                    </div>
                  </div>
                  <button 
                    onClick={() => handleDelete(selectedEmail.id)}
                    className="btn-secondary text-red-400 border-red-500/30 hover:bg-red-500/20"
                  >
                    Delete
                  </button>
                </div>
                <div className="prose prose-invert max-w-none">
                  <p className="text-[#a0a0b0] leading-relaxed whitespace-pre-wrap">{selectedEmail.body}</p>
                </div>
                <div className="mt-6 pt-6 border-t border-[#2a2a3a]">
                  <div className="flex items-center gap-2 text-sm text-[#a0a0b0]">
                    <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>Indexed for semantic search</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-6 flex flex-col items-center justify-center h-full min-h-[400px] text-center">
                <div className="w-16 h-16 rounded-full bg-[#1a1a24] flex items-center justify-center mb-4">
                  <svg className="w-8 h-8 text-[#a0a0b0]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <p className="text-[#a0a0b0]">Select an email to view details</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
