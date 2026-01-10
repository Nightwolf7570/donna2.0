import { useState, useRef, useEffect } from 'react'
import type { StatusMode } from '../App'

interface TopNavProps {
  status: StatusMode
  onStatusChange: (status: StatusMode) => void
}

const statusConfig = {
  'on-duty': { label: 'On duty', dotClass: 'status-on-duty' },
  'quiet-hours': { label: 'Quiet hours', dotClass: 'status-quiet' },
  'do-not-disturb': { label: 'Do not disturb', dotClass: 'status-dnd' },
}

export default function TopNav({ status, onStatusChange }: TopNavProps) {
  const [showDropdown, setShowDropdown] = useState(false)
  const [showStatusMenu, setShowStatusMenu] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const statusRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowDropdown(false)
      }
      if (statusRef.current && !statusRef.current.contains(e.target as Node)) {
        setShowStatusMenu(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <header className="h-16 bg-white border-b border-gray-200 px-6 flex items-center justify-between">
      {/* Left - Logo */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 bg-slate-800 rounded-lg flex items-center justify-center">
          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
        </div>
        <div>
          <h1 className="text-base font-semibold text-gray-900">Front Desk</h1>
          <p className="text-xs text-gray-500">AI Receptionist</p>
        </div>
      </div>

      {/* Right - Status & User */}
      <div className="flex items-center gap-4">
        {/* Status Selector */}
        <div className="relative" ref={statusRef}>
          <button
            onClick={() => setShowStatusMenu(!showStatusMenu)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-gray-200 hover:bg-gray-50 transition-colors"
          >
            <div className={`status-dot ${statusConfig[status].dotClass}`} />
            <span className="text-sm text-gray-700">{statusConfig[status].label}</span>
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {showStatusMenu && (
            <div className="absolute right-0 top-full mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50 animate-fade-in">
              {(Object.keys(statusConfig) as StatusMode[]).map((key) => (
                <button
                  key={key}
                  onClick={() => { onStatusChange(key); setShowStatusMenu(false) }}
                  className={`w-full flex items-center gap-3 px-4 py-2 text-left hover:bg-gray-50 ${status === key ? 'bg-gray-50' : ''}`}
                >
                  <div className={`status-dot ${statusConfig[key].dotClass}`} />
                  <span className="text-sm text-gray-700">{statusConfig[key].label}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* User Avatar & Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setShowDropdown(!showDropdown)}
            className="w-9 h-9 rounded-full bg-slate-600 flex items-center justify-center text-white font-medium text-sm hover:bg-slate-700 transition-colors"
          >
            U
          </button>

          {showDropdown && (
            <div className="absolute right-0 top-full mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50 animate-fade-in">
              <button className="w-full flex items-center gap-3 px-4 py-2 text-left hover:bg-gray-50">
                <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <span className="text-sm text-gray-700">Settings</span>
              </button>
              <div className="border-t border-gray-100 my-1" />
              <button className="w-full flex items-center gap-3 px-4 py-2 text-left hover:bg-gray-50">
                <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                <span className="text-sm text-gray-700">Sign out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
