// Call Record Types
export interface CallRecord {
  callSid: string
  callerNumber: string
  identifiedName: string | null
  callPurpose: string | null
  outcome: 'connected' | 'voicemail' | 'rejected' | 'missed'
  timestamp: Date
  duration: number
  transcript: string[]
}

// Contact Types
export interface Contact {
  id: string
  name: string
  email: string
  phone: string | null
  company: string | null
}

export interface ContactInput {
  name: string
  email: string
  phone?: string
  company?: string
}

// Email Types
export interface Email {
  id: string
  sender: string
  subject: string
  body: string
  timestamp: Date
}

export interface EmailInput {
  sender: string
  subject: string
  body: string
  timestamp?: Date
}

// System Config Types
export interface SystemConfig {
  twilioAccountSid: string
  twilioAuthToken: string
  deepgramApiKey: string
  fireworksApiKey: string
  voyageApiKey: string
  mongodbUri: string
  serverPort: number
}

// API Response Types
export interface ApiResponse<T> {
  data: T
  success: boolean
  error?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}
