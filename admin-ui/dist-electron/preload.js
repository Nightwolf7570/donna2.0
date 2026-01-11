"use strict";
const electron = require("electron");
electron.contextBridge.exposeInMainWorld("electronAPI", {
  checkServerConnection: (baseUrl) => electron.ipcRenderer.invoke("check-server-connection", baseUrl)
});
