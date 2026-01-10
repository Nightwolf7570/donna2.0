import { useState, useEffect } from 'react'
import { getApiClient } from '../api/client'
import type { Contact } from '../types'

export default function Contacts() {
  const [contacts, setContacts] = useState<Contact[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingContact, setEditingContact] = useState<Contact | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetchContacts()
  }, [])

  const fetchContacts = async () => {
    setLoading(true)
    try {
      const client = getApiClient()
      const data = await client.getContacts()
      setContacts(data)
      setError(null)
    } catch (e) {
      console.error('Failed to fetch contacts:', e)
      setError('Failed to load contacts')
    } finally {
      setLoading(false)
    }
  }

  const filteredContacts = contacts.filter(contact =>
    contact.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    contact.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    contact.company?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this contact?')) return
    
    try {
      const client = getApiClient()
      await client.deleteContact(id)
      setContacts(contacts.filter(c => c.id !== id))
    } catch (e) {
      console.error('Failed to delete contact:', e)
      alert('Failed to delete contact')
    }
  }

  const handleSave = async (contact: Contact) => {
    setSaving(true)
    try {
      const client = getApiClient()
      
      if (editingContact) {
        // Update existing
        const updated = await client.updateContact(contact.id, {
          name: contact.name,
          email: contact.email,
          phone: contact.phone || undefined,
          company: contact.company || undefined,
        })
        setContacts(contacts.map(c => c.id === updated.id ? updated : c))
      } else {
        // Create new
        const created = await client.createContact({
          name: contact.name,
          email: contact.email,
          phone: contact.phone || undefined,
          company: contact.company || undefined,
        })
        setContacts([...contacts, created])
      }
      
      setShowModal(false)
      setEditingContact(null)
    } catch (e) {
      console.error('Failed to save contact:', e)
      alert('Failed to save contact')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[#6366f1] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-[#a0a0b0]">Loading contacts...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 animate-slide-up">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">Contacts</h1>
          <p className="text-[#a0a0b0] mt-1">Manage contacts for caller identification.</p>
        </div>
        <button 
          onClick={() => { setEditingContact(null); setShowModal(true) }}
          className="btn-primary flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Contact
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
            placeholder="Search contacts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input pl-10"
          />
        </div>
      </div>

      {/* Contacts Grid */}
      {filteredContacts.length === 0 ? (
        <div className="card p-12 text-center">
          <div className="w-16 h-16 rounded-full bg-[#1a1a24] flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-[#a0a0b0]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <p className="text-[#a0a0b0]">No contacts found</p>
          <p className="text-sm text-[#6a6a7a] mt-1">Add contacts to help Donna identify callers</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredContacts.map((contact) => (
            <div key={contact.id} className="card p-6 group">
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[#6366f1] to-[#8b5cf6] flex items-center justify-center text-white text-lg font-medium">
                  {contact.name.split(' ').map(n => n[0]).join('')}
                </div>
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button 
                    onClick={() => { setEditingContact(contact); setShowModal(true) }}
                    className="p-2 hover:bg-[#1a1a24] rounded-lg transition-colors text-[#a0a0b0] hover:text-white"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                    </svg>
                  </button>
                  <button 
                    onClick={() => handleDelete(contact.id)}
                    className="p-2 hover:bg-red-500/20 rounded-lg transition-colors text-[#a0a0b0] hover:text-red-400"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
              <h3 className="text-lg font-semibold text-white mb-1">{contact.name}</h3>
              {contact.company && (
                <p className="text-sm text-[#8b5cf6] mb-3">{contact.company}</p>
              )}
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2 text-[#a0a0b0]">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  {contact.email}
                </div>
                {contact.phone && (
                  <div className="flex items-center gap-2 text-[#a0a0b0]">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                    </svg>
                    {contact.phone}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <ContactModal 
          contact={editingContact}
          saving={saving}
          onClose={() => { setShowModal(false); setEditingContact(null) }}
          onSave={handleSave}
        />
      )}
    </div>
  )
}

function ContactModal({ contact, saving, onClose, onSave }: { 
  contact: Contact | null
  saving: boolean
  onClose: () => void
  onSave: (contact: Contact) => void 
}) {
  const [form, setForm] = useState({
    name: contact?.name || '',
    email: contact?.email || '',
    phone: contact?.phone || '',
    company: contact?.company || '',
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSave({
      id: contact?.id || '',
      name: form.name,
      email: form.email,
      phone: form.phone || null,
      company: form.company || null,
    })
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="card w-full max-w-md p-6 animate-slide-up">
        <h2 className="text-xl font-bold text-white mb-6">
          {contact ? 'Edit Contact' : 'Add Contact'}
        </h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-[#a0a0b0] mb-2">Name *</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="input"
              required
              disabled={saving}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-[#a0a0b0] mb-2">Email *</label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="input"
              required
              disabled={saving}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-[#a0a0b0] mb-2">Phone</label>
            <input
              type="tel"
              value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
              className="input"
              disabled={saving}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-[#a0a0b0] mb-2">Company</label>
            <input
              type="text"
              value={form.company}
              onChange={(e) => setForm({ ...form, company: e.target.value })}
              className="input"
              disabled={saving}
            />
          </div>
          <div className="flex gap-3 pt-4">
            <button type="button" onClick={onClose} className="btn-secondary flex-1" disabled={saving}>
              Cancel
            </button>
            <button type="submit" className="btn-primary flex-1" disabled={saving}>
              {saving ? 'Saving...' : contact ? 'Save Changes' : 'Add Contact'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
