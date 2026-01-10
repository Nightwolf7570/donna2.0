import { useConnectionStatus } from '../api'

interface SidebarProps {
  currentView: string
  onViewChange: (view: 'dashboard' | 'calls' | 'contacts' | 'emails' | 'settings') => void
}

const menuItems = [
  { id: 'dashboard', label: 'Dashboard', icon: '📊' },
  { id: 'calls', label: 'Call History', icon: '📞' },
  { id: 'contacts', label: 'Contacts', icon: '👥' },
  { id: 'emails', label: 'Emails', icon: '📧' },
  { id: 'settings', label: 'Settings', icon: '⚙️' },
] as const

export default function Sidebar({ currentView, onViewChange }: SidebarProps) {
  const { connected, checking, error, retry } = useConnectionStatus()

  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <h1 className="text-xl font-bold text-primary-600">AI Receptionist</h1>
        <p className="text-sm text-gray-500">Admin Panel</p>
      </div>
      
      <nav className="flex-1 p-4">
        <ul className="space-y-1">
          {menuItems.map((item) => (
            <li key={item.id}>
              <button
                onClick={() => onViewChange(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors ${
                  currentView === item.id
                    ? 'bg-primary-50 text-primary-700 font-medium'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </button>
            </li>
          ))}
        </ul>
      </nav>
      
      <div className="p-4 border-t border-gray-200">
        {checking ? (
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <span className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></span>
            <span>Checking connection...</span>
          </div>
        ) : connected ? (
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <span className="w-2 h-2 bg-green-500 rounded-full"></span>
            <span>Server Connected</span>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-red-600">
              <span className="w-2 h-2 bg-red-500 rounded-full"></span>
              <span>Disconnected</span>
            </div>
            {error && (
              <p className="text-xs text-gray-500">{error}</p>
            )}
            <button
              onClick={retry}
              className="text-xs text-primary-600 hover:text-primary-700 underline"
            >
              Retry connection
            </button>
          </div>
        )}
      </div>
    </aside>
  )
}
