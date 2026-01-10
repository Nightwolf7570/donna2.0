import { useState, useEffect } from 'react'
import { getApiClient } from '../api/client'
import { Email } from '../types'

export default function Emails() {
  const [emails, setEmails] = useState<Email[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  useEffect(() => {
    fetchEmails()
  }, [])

  const fetchEmails = async () => {
    try {
      const client = getApiClient()
      const data = await client.getEmails(50)
      setEmails(data)
    } catch (error) {
      console.error('Failed to fetch emails:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredEmails = emails.filter(email =>
    email.subject.toLowerCase().includes(search.toLowerCase()) ||
    email.sender.toLowerCase().includes(search.toLowerCase()) ||
    email.body.toLowerCase().includes(search.toLowerCase())
  )

  const formatDate = (date: Date | string) => {
    return new Date(date).toLocaleString()
  }

  return (
    <div className="h-full flex flex-col max-w-[1200px] mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Emails</h1>
          <p className="text-gray-500">Searchable email context for AI receptionist</p>
        </div>
        <div className="w-64">
          <input
            type="text"
            placeholder="Search emails..."
            className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="flex-1 card overflow-hidden flex flex-col">
        {loading ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
          </div>
        ) : filteredEmails.length === 0 ? (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            No emails found
          </div>
        ) : (
          <div className="overflow-y-auto">
            <table className="w-full text-left">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Sender</th>
                  <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Subject</th>
                  <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Preview</th>
                  <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Received</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredEmails.map((email) => (
                  <tr key={email.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">{email.sender}</td>
                    <td className="px-6 py-4 text-sm text-gray-700">{email.subject}</td>
                    <td className="px-6 py-4 text-sm text-gray-500 max-w-md truncate">{email.body}</td>
                    <td className="px-6 py-4 text-sm text-gray-500 whitespace-nowrap">{formatDate(email.timestamp)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
