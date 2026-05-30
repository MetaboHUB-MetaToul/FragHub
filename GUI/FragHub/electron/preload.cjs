const { contextBridge, ipcRenderer } = require('electron')

// On expose une API globale nommée "electronAPI" à ton code Vue
contextBridge.exposeInMainWorld('electronAPI', {
    selectFiles: () => ipcRenderer.invoke('dialog:openFiles'),
    selectFolder: () => ipcRenderer.invoke('dialog:openFolder')
})