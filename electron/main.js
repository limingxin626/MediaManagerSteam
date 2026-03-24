import { app, BrowserWindow } from 'electron';
import path from 'path';
import url from 'url';

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      webSecurity: false, // 必须！允许播放本地绝对路径视频
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true // 启用 remote 模块
    }
  });

  const isDev = !app.isPackaged;
  
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