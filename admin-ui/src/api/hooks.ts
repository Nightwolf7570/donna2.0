import { useState, useEffect, useCallback } from 'react'
import { ApiClient, getApiClient, ConnectionError, ApiError } from './client'

interface UseApiState<T> {
  data: T | null
  loading: boolean
  error: Error | null
  refetch: () => Promise<void>
}

export function useApi<T>(
  fetcher: (client: ApiClient) => Promise<T>,
  deps: unknown[] = []
): UseApiState<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const client = getApiClient()
      const result = await fetcher(client)
      setData(result)
    } catch (err) {
      setError(err as Error)
    } finally {
      setLoading(false)
    }
  }, deps)

  useEffect(() => {
    fetch()
  }, [fetch])

  return { data, loading, error, refetch: fetch }
}

interface ConnectionStatus {
  connected: boolean
  checking: boolean
  error: string | null
  retry: () => Promise<void>
}

export function useConnectionStatus(
  checkInterval: number = 30000
): ConnectionStatus {
  const [connected, setConnected] = useState(false)
  const [checking, setChecking] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const checkConnection = useCallback(async () => {
    setChecking(true)
    try {
      const client = getApiClient()
      const isConnected = await client.checkHealth()
      setConnected(isConnected)
      setError(isConnected ? null : 'Server is not responding')
    } catch (err) {
      setConnected(false)
      if (err instanceof ConnectionError) {
        setError(err.message)
      } else {
        setError('Failed to connect to server')
      }
    } finally {
      setChecking(false)
    }
  }, [])

  useEffect(() => {
    checkConnection()
    const interval = setInterval(checkConnection, checkInterval)
    return () => clearInterval(interval)
  }, [checkConnection, checkInterval])

  return { connected, checking, error, retry: checkConnection }
}

export function isConnectionError(error: Error | null): boolean {
  return error instanceof ConnectionError
}

export function isApiError(error: Error | null): error is ApiError {
  return error instanceof ApiError
}

export function getErrorMessage(error: Error | null): string {
  if (!error) return ''
  if (error instanceof ConnectionError) {
    return 'Unable to connect to server. Please check your connection and try again.'
  }
  if (error instanceof ApiError) {
    if (error.statusCode === 404) return 'Resource not found'
    if (error.statusCode === 401) return 'Unauthorized - please check your credentials'
    if (error.statusCode === 403) return 'Access denied'
    if (error.statusCode >= 500) return 'Server error - please try again later'
    return error.message
  }
  return error.message || 'An unexpected error occurred'
}
