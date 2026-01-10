import type {
  CallRecord,
  Contact,
  ContactInput,
  Email,
  EmailInput,
  SystemConfig,
} from '../types'

interface ApiClientConfig {
  baseUrl: string
  maxRetries?: number
  retryDelay?: number
  timeout?: number
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  body?: unknown
  skipRetry?: boolean
}

export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public isRetryable: boolean = false
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export class ConnectionError extends Error {
  constructor(message: string = 'Unable to connect to server') {
    super(message)
    this.name = 'ConnectionError'
  }
}

export class ApiClient {
  private baseUrl: string
  private maxRetries: number
  private retryDelay: number
  private timeout: number

  constructor(config: ApiClientConfig) {
    this.baseUrl = config.baseUrl.replace(/\/$/, '')
    this.maxRetries = config.maxRetries ?? 3
    this.retryDelay = config.retryDelay ?? 1000
    this.timeout = config.timeout ?? 10000
  }

  private async sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms))
  }

  private async request<T>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const { method = 'GET', body, skipRetry = false } = options
    const url = `${this.baseUrl}${endpoint}`

    let lastError: Error | null = null
    const attempts = skipRetry ? 1 : this.maxRetries

    for (let attempt = 1; attempt <= attempts; attempt++) {
      try {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), this.timeout)

        const response = await fetch(url, {
          method,
          headers: {
            'Content-Type': 'application/json',
          },
          body: body ? JSON.stringify(body) : undefined,
          signal: controller.signal,
        })

        clearTimeout(timeoutId)

        if (!response.ok) {
          const isRetryable = response.status >= 500 || response.status === 429
          const errorMessage = await response.text().catch(() => 'Unknown error')
          throw new ApiError(errorMessage, response.status, isRetryable)
        }

        return await response.json()
      } catch (error) {
        lastError = error as Error

        if (error instanceof ApiError && !error.isRetryable) {
          throw error
        }

        if (error instanceof DOMException && error.name === 'AbortError') {
          lastError = new ConnectionError('Request timed out')
        } else if (error instanceof TypeError) {
          lastError = new ConnectionError('Network error - server may be unreachable')
        }

        if (attempt < attempts) {
          const delay = this.retryDelay * Math.pow(2, attempt - 1)
          await this.sleep(delay)
        }
      }
    }

    throw lastError ?? new ConnectionError()
  }

  // Health check
  async checkHealth(): Promise<boolean> {
    try {
      await this.request<{ status: string }>('/health', { skipRetry: true })
      return true
    } catch {
      return false
    }
  }

  // Call History endpoints
  async getCallHistory(limit?: number): Promise<CallRecord[]> {
    const query = limit ? `?limit=${limit}` : ''
    return this.request<CallRecord[]>(`/calls${query}`)
  }

  async getCallDetails(callSid: string): Promise<CallRecord> {
    return this.request<CallRecord>(`/calls/${encodeURIComponent(callSid)}`)
  }

  // Contact endpoints
  async getContacts(): Promise<Contact[]> {
    return this.request<Contact[]>('/contacts')
  }

  async getContact(id: string): Promise<Contact> {
    return this.request<Contact>(`/contacts/${encodeURIComponent(id)}`)
  }

  async createContact(contact: ContactInput): Promise<Contact> {
    return this.request<Contact>('/contacts', {
      method: 'POST',
      body: contact,
    })
  }

  async updateContact(id: string, contact: ContactInput): Promise<Contact> {
    return this.request<Contact>(`/contacts/${encodeURIComponent(id)}`, {
      method: 'PUT',
      body: contact,
    })
  }

  async deleteContact(id: string): Promise<void> {
    await this.request<void>(`/contacts/${encodeURIComponent(id)}`, {
      method: 'DELETE',
    })
  }

  // Email endpoints
  async getEmails(limit?: number): Promise<Email[]> {
    const query = limit ? `?limit=${limit}` : ''
    return this.request<Email[]>(`/emails${query}`)
  }

  async getEmail(id: string): Promise<Email> {
    return this.request<Email>(`/emails/${encodeURIComponent(id)}`)
  }

  async importEmails(emails: EmailInput[]): Promise<number> {
    const result = await this.request<{ imported: number }>('/emails/import', {
      method: 'POST',
      body: { emails },
    })
    return result.imported
  }

  async deleteEmail(id: string): Promise<void> {
    await this.request<void>(`/emails/${encodeURIComponent(id)}`, {
      method: 'DELETE',
    })
  }

  // Config endpoints
  async getConfig(): Promise<SystemConfig> {
    return this.request<SystemConfig>('/config')
  }

  async updateConfig(config: Partial<SystemConfig>): Promise<SystemConfig> {
    return this.request<SystemConfig>('/config', {
      method: 'PUT',
      body: config,
    })
  }

  // Dashboard stats
  async getDashboardStats(): Promise<{
    callsToday: number
    totalContacts: number
    emailsIndexed: number
    avgResponseTime: number
  }> {
    return this.request('/stats')
  }

  // Business config endpoints
  async getBusinessConfig(): Promise<{
    ceoName: string
    companyName: string | null
    companyDescription: string | null
  }> {
    return this.request('/config/business')
  }

  async updateBusinessConfig(config: {
    ceoName: string
    companyName?: string
    companyDescription?: string
  }): Promise<{
    ceoName: string
    companyName: string | null
    companyDescription: string | null
  }> {
    return this.request('/config/business', {
      method: 'PUT',
      body: config,
    })
  }
}

// Default client instance
let defaultClient: ApiClient | null = null

export function getApiClient(): ApiClient {
  if (!defaultClient) {
    defaultClient = new ApiClient({
      baseUrl: 'http://localhost:8000',
    })
  }
  return defaultClient
}

export function setApiClient(config: ApiClientConfig): ApiClient {
  defaultClient = new ApiClient(config)
  return defaultClient
}
