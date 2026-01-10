"use strict";const e=require("electron");e.contextBridge.exposeInMainWorld("electronAPI",{checkServerConnection:n=>e.ipcRenderer.invoke("check-server-connection",n)});
