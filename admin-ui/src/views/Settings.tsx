import { useState, useEffect } from 'react'
import { getApiClient } from '../api/client'

interface SettingsSection {
  id: string
  title: string
  description: string
  icon: React.ReactNode
}

export default function Settings() {
  const [activeSection, setActiveSection] = useState('api-keys')
  const [saved, setSaved] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [googleCalendarConnected, setGoogleCalendarConnected] = useState(false)
  const [googleCalendarLoading, setGoogleCalendarLoading] = useState(false)

  const [apiKeys, setApiKeys] = useState({
    deepgram: '',
    fireworks: '',
    voyage: '',
    twilio_sid: '',
    twilio_token: '',
    mongodb: '',
    elevenlabs: '',
  })

  const [generalSettings, setGeneralSettings] = useState({
    ceoName: '',
    companyName: '',
    companyDescription: '',
    assistantName: 'Donna',
    timezone: 'America/Los_Angeles',
    language: 'en-US',
  })

  // Fetch configs on mount
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const client = getApiClient()

        // Fetch Business Config
        const bizConfig = await client.getBusinessConfig()
        setGeneralSettings(prev => ({
          ...prev,
          ceoName: bizConfig.ceoName || '',
          companyName: bizConfig.companyName || '',
          companyDescription: bizConfig.companyDescription || '',
        }))

        // Fetch System Config
        const sysConfig = await client.getConfig()
        setApiKeys({
          deepgram: sysConfig.deepgramApiKey || '',
          fireworks: sysConfig.fireworksApiKey || '',
          voyage: sysConfig.voyageApiKey || '',
          twilio_sid: sysConfig.twilioAccountSid || '',
          twilio_token: sysConfig.twilioAuthToken || '',
          mongodb: sysConfig.mongodbUri || '',
          elevenlabs: '', // Not in SystemConfig type yet, keep as is
        })

      } catch (e) {
        console.warn('Failed to fetch config:', e)
      }
    }
    fetchConfig()
  }, [])

  // Check Google Calendar status
  useEffect(() => {
    const checkGoogleCalendarStatus = async () => {
      try {
        const client = getApiClient()
        const status = await client.getGoogleCalendarStatus()
        setGoogleCalendarConnected(status.connected)
      } catch (e) {
        console.warn('Failed to check Google Calendar status:', e)
      }
    }
    checkGoogleCalendarStatus()
  }, [])

  const handleConnectGoogleCalendar = async () => {
    setGoogleCalendarLoading(true)
    try {
      const client = getApiClient()
      const { auth_url } = await client.getGoogleAuthUrl()
      window.location.href = auth_url
    } catch (e) {
      console.error('Failed to initiate Google Auth:', e)
      setError('Failed to connect to Google Calendar')
    } finally {
      setGoogleCalendarLoading(false)
    }
  }

  const handleDisconnectGoogleCalendar = async () => {
    setGoogleCalendarLoading(true)
    try {
      const client = getApiClient()
      await client.disconnectGoogleCalendar()
      setGoogleCalendarConnected(false)
    } catch (e) {
      console.error('Failed to disconnect Google Calendar:', e)
      setError('Failed to disconnect Google Calendar')
    } finally {
      setGoogleCalendarLoading(false)
    }
  }

  const sections: SettingsSection[] = [
    {
      id: 'api-keys',
      title: 'API Keys',
      description: 'Configure external service credentials',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
        </svg>
      ),
    },
    {
      id: 'general',
      title: 'General',
      description: 'Basic application settings',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      ),
    },
    {
      id: 'integrations',
      title: 'Integrations',
      description: 'Connect external tools (Google Calendar, etc.)',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      ),
    },
  ]

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    try {
      const client = getApiClient()

      // Update Business Config
      await client.updateBusinessConfig({
        ceoName: generalSettings.ceoName,
        companyName: generalSettings.companyName || undefined,
        companyDescription: generalSettings.companyDescription || undefined,
      })

      // Update System Config
      await client.updateConfig({
        deepgramApiKey: apiKeys.deepgram,
        fireworksApiKey: apiKeys.fireworks,
        voyageApiKey: apiKeys.voyage,
        twilioAccountSid: apiKeys.twilio_sid,
        twilioAuthToken: apiKeys.twilio_token,
        mongodbUri: apiKeys.mongodb,
      })

      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (e) {
      console.error('Failed to save settings:', e)
      setError('Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="p-8 animate-slide-up">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">Settings</h1>
          <p className="text-[#a0a0b0] mt-1">Configure Donna's behavior and integrations.</p>
        </div>
        <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center gap-2 disabled:opacity-50">
          {saved ? (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Saved!
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
              </svg>
              Save Changes
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="lg:col-span-1">
          <div className="card p-2">
            {sections.map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`w-full flex items-center gap-3 p-3 rounded-lg transition-all ${activeSection === section.id
                  ? 'bg-[#6366f1]/20 text-[#8b5cf6]'
                  : 'text-[#a0a0b0] hover:bg-[#1a1a24] hover:text-white'
                  }`}
              >
                {section.icon}
                <div className="text-left">
                  <p className="font-medium">{section.title}</p>
                  <p className="text-xs opacity-70">{section.description}</p>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="lg:col-span-3">
          {activeSection === 'api-keys' && (
            <div className="card p-6 space-y-6">
              <div>
                <h2 className="text-lg font-semibold text-white mb-4">API Keys</h2>
                <p className="text-sm text-[#a0a0b0] mb-6">
                  Configure your API keys for external services. Keys are stored securely and never exposed.
                </p>

              </div>

              <ApiKeyInput
                label="Deepgram API Key"
                description="For speech-to-text transcription"
                value={apiKeys.deepgram}
                onChange={(v) => setApiKeys({ ...apiKeys, deepgram: v })}
              />
              <ApiKeyInput
                label="Fireworks AI API Key"
                description="For LLM reasoning and responses"
                value={apiKeys.fireworks}
                onChange={(v) => setApiKeys({ ...apiKeys, fireworks: v })}
              />
              <ApiKeyInput
                label="Voyage AI API Key"
                description="For semantic embeddings"
                value={apiKeys.voyage}
                onChange={(v) => setApiKeys({ ...apiKeys, voyage: v })}
              />
              <ApiKeyInput
                label="MongoDB URI"
                description="Database connection string"
                value={apiKeys.mongodb}
                onChange={(v) => setApiKeys({ ...apiKeys, mongodb: v })}
              />
              <div className="border-t border-[#2a2a3a] pt-6">
                <h3 className="text-sm font-medium text-white mb-4">Twilio Credentials</h3>
                <div className="grid grid-cols-2 gap-4">
                  <ApiKeyInput
                    label="Account SID"
                    value={apiKeys.twilio_sid}
                    onChange={(v) => setApiKeys({ ...apiKeys, twilio_sid: v })}
                  />
                  <ApiKeyInput
                    label="Auth Token"
                    value={apiKeys.twilio_token}
                    onChange={(v) => setApiKeys({ ...apiKeys, twilio_token: v })}
                  />
                </div>
              </div>
              <div className="border-t border-[#2a2a3a] pt-6">
                <h3 className="text-sm font-medium text-white mb-4">Optional Services</h3>
                <ApiKeyInput
                  label="ElevenLabs API Key"
                  description="For premium text-to-speech (optional)"
                  value={apiKeys.elevenlabs}
                  onChange={(v) => setApiKeys({ ...apiKeys, elevenlabs: v })}
                  placeholder="Enter key to enable ElevenLabs TTS"
                />
              </div>
            </div>
          )}

          {activeSection === 'general' && (
            <div className="card p-6 space-y-6">
              <div>
                <h2 className="text-lg font-semibold text-white mb-4">General Settings</h2>
                <p className="text-sm text-[#a0a0b0] mb-6">
                  Configure basic application settings and preferences.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-[#a0a0b0] mb-2">CEO Name *</label>
                <input
                  type="text"
                  value={generalSettings.ceoName}
                  onChange={(e) => setGeneralSettings({ ...generalSettings, ceoName: e.target.value })}
                  className="input"
                  placeholder="Enter CEO name"
                />
                <p className="text-xs text-[#a0a0b0] mt-1">The CEO's name that Donna will recognize</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-[#a0a0b0] mb-2">Company Name</label>
                <input
                  type="text"
                  value={generalSettings.companyName}
                  onChange={(e) => setGeneralSettings({ ...generalSettings, companyName: e.target.value })}
                  className="input"
                  placeholder="Your Company Name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-[#a0a0b0] mb-2">Company Description</label>
                <textarea
                  value={generalSettings.companyDescription}
                  onChange={(e) => setGeneralSettings({ ...generalSettings, companyDescription: e.target.value })}
                  className="input min-h-[80px]"
                  placeholder="Brief description of what your company does"
                />
              </div>

              <div className="border-t border-[#2a2a3a] pt-6">
                <h3 className="text-sm font-medium text-white mb-4">Assistant Settings</h3>
              </div>

              <div>
                <label className="block text-sm font-medium text-[#a0a0b0] mb-2">Assistant Name</label>
                <input
                  type="text"
                  value={generalSettings.assistantName}
                  onChange={(e) => setGeneralSettings({ ...generalSettings, assistantName: e.target.value })}
                  className="input"
                />
                <p className="text-xs text-[#a0a0b0] mt-1">The name your AI assistant will use to identify itself</p>
              </div>



              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-[#a0a0b0] mb-2">Timezone</label>
                  <select
                    value={generalSettings.timezone}
                    onChange={(e) => setGeneralSettings({ ...generalSettings, timezone: e.target.value })}
                    className="input"
                  >
                    <option value="America/Los_Angeles">Pacific Time (PT)</option>
                    <option value="America/Denver">Mountain Time (MT)</option>
                    <option value="America/Chicago">Central Time (CT)</option>
                    <option value="America/New_York">Eastern Time (ET)</option>
                    <option value="UTC">UTC</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-[#a0a0b0] mb-2">Language</label>
                  <select
                    value={generalSettings.language}
                    onChange={(e) => setGeneralSettings({ ...generalSettings, language: e.target.value })}
                    className="input"
                  >
                    <option value="en-US">English (US)</option>
                    <option value="en-GB">English (UK)</option>
                    <option value="es-ES">Spanish</option>
                    <option value="fr-FR">French</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {activeSection === 'integrations' && (
            <div className="card p-6 space-y-6">
              <div>
                <h2 className="text-lg font-semibold text-white mb-4">Integrations</h2>
                <p className="text-sm text-[#a0a0b0] mb-6">
                  Manage connections to external services.
                </p>
              </div>

              <div className="flex items-center justify-between p-4 bg-[#1a1a24] rounded-lg border border-[#2a2a3a]">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center">
                    <img src="https://www.google.com/favicon.ico" alt="Google" className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-medium text-white">Google Calendar</h3>
                    <p className="text-sm text-[#a0a0b0]">Sync events and availability</p>
                  </div>
                </div>

                {googleCalendarConnected ? (
                  <div className="flex items-center gap-4">
                    <span className="flex items-center gap-2 text-green-400 text-sm">
                      <span className="w-2 h-2 rounded-full bg-green-400"></span>
                      Connected
                    </span>
                    <button
                      onClick={handleDisconnectGoogleCalendar}
                      disabled={googleCalendarLoading}
                      className="text-[#a0a0b0] hover:text-white hover:underline text-sm"
                    >
                      Disconnect
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={handleConnectGoogleCalendar}
                    disabled={googleCalendarLoading}
                    className="btn-secondary"
                  >
                    {googleCalendarLoading ? 'Connecting...' : 'Connect'}
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function ApiKeyInput({
  label,
  description,
  value,
  onChange,
  placeholder
}: {
  label: string
  description?: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
}) {
  const [show, setShow] = useState(false)

  return (
    <div>
      <label className="block text-sm font-medium text-[#a0a0b0] mb-2">{label}</label>
      <div className="relative">
        <input
          type={show ? 'text' : 'password'}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="input pr-10"
          placeholder={placeholder}
        />
        <button
          type="button"
          onClick={() => setShow(!show)}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-[#a0a0b0] hover:text-white transition-colors"
        >
          {show ? (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          )}
        </button>
      </div>
      {description && <p className="text-xs text-[#a0a0b0] mt-1">{description}</p>}
    </div>
  )
}
