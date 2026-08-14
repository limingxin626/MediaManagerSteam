const { contextBridge, ipcRenderer, shell } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  openFileDialog: (options) => ipcRenderer.invoke('dialog:openFile', options),
  showItemInFolder: (path) => shell.showItemInFolder(path),
  setTitleBarTheme: (dark) => ipcRenderer.invoke('window:setTitleBarTheme', dark)
});
