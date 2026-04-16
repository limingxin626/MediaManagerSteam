import { app, BrowserWindow, ipcMain, dialog, Menu } from 'electron';
import path from 'path';
import url from 'url';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

Menu.setApplicationMenu(null);

function createWindow() {
  const isDev = !app.isPackaged;
  
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    show: false, // 先隐藏窗口
    webPreferences: {
      webSecurity: false, // 必须！允许播放本地绝对路径视频
      nodeIntegration: true,
      contextIsolation: true, // 启用 contextIsolation 以使用 preload
      preload: isDev 
        ? path.join(__dirname, 'preload.js')
        : path.join(process.resourcesPath, 'app', 'preload.js')
    }
  });
  
  // 直接最大化窗口
  win.maximize();
  
  // 窗口准备就绪后显示
  win.on('ready-to-show', () => {
    win.show();
  });
  
  if (isDev) {
    // 开发环境：加载 Vue 的开发地址
    win.loadURL('http://localhost:5173');
    // 打开开发者工具
    win.webContents.openDevTools();
  } else {
    // 生产环境：加载打包后的静态文件
    const indexPath = path.join(process.resourcesPath, 'app', 'vue-dist', 'index.html');
    win.loadURL(url.format({
      pathname: indexPath,
      protocol: 'file:',
      slashes: true
    }));
  }
}

app.whenReady().then(() => {
  createWindow(); // 启动前端
});

// IPC 处理程序：打开文件对话框
ipcMain.handle('dialog:openFile', async (event, options) => {
  const result = await dialog.showOpenDialog(options);
  return result;
});

// 当所有窗口关闭时退出应用
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// 在 macOS 上，点击 Dock 图标时重新创建窗口
app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});