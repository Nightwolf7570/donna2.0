import { contextBridge, ipcRenderer } from 'electron'

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  checkServerConnection: (baseUrl: string) => 
    ipcRenderer.invoke('check-server-connection', baseUrl)
})

// Type definitions for the exposed API
declare global {
  interface Window {
    electronAPI: {
      checkServerConnection: (baseUrl: string) => Promise<boolean>
    }
  }
}
