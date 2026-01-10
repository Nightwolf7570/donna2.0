/// <reference types="vite/client" />

interface Window {
  electronAPI: {
    checkServerConnection: (baseUrl: string) => Promise<boolean>
  }
}
