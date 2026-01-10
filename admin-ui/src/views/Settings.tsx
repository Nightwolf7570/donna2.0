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

  const [apiKeys, setApiKeys] = useState({
    deepgram: '••••••••••••••••',
    fireworks: '••••••••••••••••',
    voyage: '••••••••••••••••',
    twilio_sid: '••••••••••••••••',
    twilio_token: '••••••••••••••••',
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

  const [voiceSettings, setVoiceSettings] = useState({
    ttsProvider: 'twilio',
    voice: 'Polly.Joanna',
    speed: 1.0,
    pitch: 1.0,
  })

  // Fetch business config on mount
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const client = getApiClient()
        const config = await client.getBusinessConfig()
        setGeneralSettings(prev => ({
          ...prev,
          ceoName: config.ceoName || '',
          companyName: config.companyName || '',
          companyDescription: config.companyDescription || '',
        }))
      } catch (e) {
        console.warn('Failed to fetch business config:', e)
      }
    }
    fetchConfig()
  }, [])

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
      id: 'voice',
      title: 'Voice & Speech',
      description: 'TTS and voice configuration',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
        </svg>
      ),
    },
  ]

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    try {
      const client = getApiClient()
      await client.updateBusinessConfig({
        ceoName: generalSettings.ceoName,
        companyName: generalSettings.companyName || undefined,
        companyDescription: generalSettings.companyDescription || undefined,
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
                <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 mb-6">
                  <p className="text-sm text-amber-400">
                    ⚠️ API keys are managed via environment variables (.env file) and cannot be changed here.
                  </p>
                </div>
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

          {activeSection === 'voice' && (
            <div className="card p-6 space-y-6">
              <div>
                <h2 className="text-lg font-semibold text-white mb-4">Voice & Speech Settings</h2>
                <p className="text-sm text-[#a0a0b0] mb-6">
                  Configure text-to-speech provider and voice characteristics.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-[#a0a0b0] mb-2">TTS Provider</label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { id: 'twilio', name: 'Twilio (Polly)', desc: 'Low latency' },
                    { id: 'deepgram', name: 'Deepgram', desc: 'Fast & natural' },
                    { id: 'elevenlabs', name: 'ElevenLabs', desc: 'Premium quality' },
                  ].map((provider) => (
                    <button
                      key={provider.id}
                      onClick={() => setVoiceSettings({ ...voiceSettings, ttsProvider: provider.id })}
                      className={`p-4 rounded-xl border transition-all ${voiceSettings.ttsProvider === provider.id
                        ? 'border-[#6366f1] bg-[#6366f1]/10'
                        : 'border-[#2a2a3a] hover:border-[#3a3a4a]'
                        }`}
                    >
                      <p className="font-medium text-white">{provider.name}</p>
                      <p className="text-xs text-[#a0a0b0] mt-1">{provider.desc}</p>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-[#a0a0b0] mb-2">Voice</label>
                <select
                  value={voiceSettings.voice}
                  onChange={(e) => setVoiceSettings({ ...voiceSettings, voice: e.target.value })}
                  className="input"
                >
                  <optgroup label="Twilio Polly">
                    <option value="Polly.Joanna">Joanna (Female, US)</option>
                    <option value="Polly.Matthew">Matthew (Male, US)</option>
                    <option value="Polly.Amy">Amy (Female, UK)</option>
                  </optgroup>
                  <optgroup label="Deepgram">
                    <option value="aura-asteria-en">Asteria (Female)</option>
                    <option value="aura-luna-en">Luna (Female)</option>
                    <option value="aura-orion-en">Orion (Male)</option>
                  </optgroup>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-[#a0a0b0] mb-2">
                    Speed: {voiceSettings.speed.toFixed(1)}x
                  </label>
                  <input
                    type="range"
                    min="0.5"
                    max="2"
                    step="0.1"
                    value={voiceSettings.speed}
                    onChange={(e) => setVoiceSettings({ ...voiceSettings, speed: parseFloat(e.target.value) })}
                    className="w-full accent-[#6366f1]"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-[#a0a0b0] mb-2">
                    Pitch: {voiceSettings.pitch.toFixed(1)}
                  </label>
                  <input
                    type="range"
                    min="0.5"
                    max="2"
                    step="0.1"
                    value={voiceSettings.pitch}
                    onChange={(e) => setVoiceSettings({ ...voiceSettings, pitch: parseFloat(e.target.value) })}
                    className="w-full accent-[#6366f1]"
                  />
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#1a1a24] border border-[#2a2a3a]">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#6366f1] to-[#8b5cf6] flex items-center justify-center">
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-white">Test Voice</p>
                    <p className="text-xs text-[#a0a0b0]">Click to hear a sample with current settings</p>
                  </div>
                  <button className="btn-secondary text-sm">
                    Play Sample
                  </button>
                </div>
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
