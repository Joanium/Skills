---
name: ElectronDesktopApps
description: Build, architect, and debug Electron desktop applications. Use when the user asks about Electron processes, IPC communication, native OS integration, auto-updaters, app packaging/distribution, performance optimization, security hardening, or building desktop features like system tray, global shortcuts, or native menus.
---

You are an expert Electron developer with deep knowledge of multi-process architecture, IPC patterns, native OS integration, performance optimization, security hardening, and cross-platform desktop app distribution.

The user provides an Electron task: architecting IPC flows, implementing native OS features, fixing memory leaks, packaging and distributing the app, hardening security, debugging renderer crashes, or building specific desktop features.

## Electron Architecture

Electron runs on three distinct process types. Understanding their boundaries is fundamental to everything else:

**Main Process** (`main.js`)

- Single Node.js process; full Node and Electron API access
- Manages all BrowserWindow instances, native menus, tray icons, IPC handlers
- Do: OS integration, file system, native dialogs, app lifecycle
- Don't: Heavy computation on the main thread (blocks the UI)

**Renderer Process** (one per BrowserWindow)

- Chromium context; runs your HTML/CSS/JS frontend
- With `contextIsolation: true` (required for security): no direct Node access
- Communicates with main only through the preload bridge
- Don't: Call `require('fs')` or any Node module directly in the renderer

**Preload Script**

- Runs in a special context with both DOM access and a limited Node context
- The **only** safe bridge between renderer and main
- Expose APIs via `contextBridge.exposeInMainWorld`

```js
// preload.js
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // Renderer → Main (invoke/handle pattern)
  readFile: (path) => ipcRenderer.invoke('read-file', path),
  saveFile: (path, content) => ipcRenderer.invoke('save-file', { path, content }),

  // Main → Renderer (on pattern)
  onUpdateAvailable: (callback) =>
    ipcRenderer.on('update-available', (_event, info) => callback(info)),

  // Clean up listener to prevent leaks
  removeUpdateListener: () => ipcRenderer.removeAllListeners('update-available'),
});
```

## IPC Communication Patterns

**Invoke/Handle — Request-Response (preferred)**

```js
// main.js — register handler
ipcMain.handle('read-file', async (event, filePath) => {
  try {
    const content = await fs.promises.readFile(filePath, 'utf-8');
    return { success: true, content };
  } catch (err) {
    return { success: false, error: err.message };
  }
});

// renderer (via preload bridge)
const result = await window.electronAPI.readFile('/path/to/file.txt');
if (result.success) {
  console.log(result.content);
}
```

**Send/On — Fire and Forget**

```js
// main.js → renderer (push events, no reply expected)
mainWindow.webContents.send('download-progress', { percent: 45, bytesPerSecond: 1024 });

// renderer — listen
window.electronAPI.onDownloadProgress((progress) => {
  updateProgressBar(progress.percent);
});
```

**IPC Security Rules**

- Always validate and sanitize data received via IPC in the main process
- Never pass raw file paths from renderer without validation — check they're within allowed directories
- Never use `ipcRenderer.sendSync` — it blocks the renderer thread
- Validate `event.senderFrame.url` in handlers if you have multiple windows

## Window Management

```js
// main.js
function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    titleBarStyle: 'hiddenInset', // macOS: custom title bar
    vibrancy: 'sidebar', // macOS: frosted glass effect
    backgroundMaterial: 'mica', // Windows 11: Mica effect
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true, // REQUIRED — isolates renderer from Node
      nodeIntegration: false, // REQUIRED — no Node in renderer
      sandbox: true, // Recommended — additional sandboxing
      webSecurity: true, // Never set to false in production
    },
  });

  // Load the frontend
  if (process.env.NODE_ENV === 'development') {
    win.loadURL('http://localhost:5173'); // Vite dev server
    win.webContents.openDevTools();
  } else {
    win.loadFile(path.join(__dirname, 'dist/index.html'));
  }

  return win;
}
```

**State Persistence**

```js
// electron-store for persistent config
import Store from 'electron-store';
const store = new Store({
  schema: {
    windowBounds: { type: 'object', default: { width: 1200, height: 800 } },
    theme: { type: 'string', enum: ['light', 'dark', 'system'], default: 'system' },
  },
});

// Save window position/size on close
win.on('close', () => {
  store.set('windowBounds', win.getBounds());
});

// Restore on open
const bounds = store.get('windowBounds');
win.setBounds(bounds);
```

## Native OS Integration

**System Tray**

```js
const tray = new Tray(path.join(__dirname, 'assets/trayIcon.png'));
// macOS: use @2x suffix for retina; template images auto-adapt to dark/light mode

const contextMenu = Menu.buildFromTemplate([
  { label: 'Open Joanium', click: () => mainWindow.show() },
  { type: 'separator' },
  { label: 'Preferences', click: () => openPreferences() },
  { type: 'separator' },
  { label: 'Quit', role: 'quit' },
]);
tray.setToolTip('Joanium');
tray.setContextMenu(contextMenu);
tray.on('click', () => (mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show()));
```

**Global Shortcuts**

```js
const { globalShortcut } = require('electron');

app.whenReady().then(() => {
  globalShortcut.register('CommandOrControl+Shift+Space', () => {
    if (mainWindow.isVisible()) {
      mainWindow.hide();
    } else {
      mainWindow.show();
      mainWindow.focus();
    }
  });
});

app.on('will-quit', () => globalShortcut.unregisterAll());
```

**Native Dialogs**

```js
// File picker
ipcMain.handle('open-file-dialog', async (event) => {
  const result = await dialog.showOpenDialog({
    properties: ['openFile', 'multiSelections'],
    filters: [
      { name: 'Documents', extensions: ['pdf', 'docx', 'txt'] },
      { name: 'All Files', extensions: ['*'] },
    ],
  });
  return result; // { canceled: bool, filePaths: string[] }
});

// Native notification
new Notification({
  title: 'Joanium',
  body: 'Your task completed successfully',
  icon: path.join(__dirname, 'assets/icon.png'),
}).show();
```

**Protocol Handling (Deep Links)**

```js
// Register custom protocol: joanium://
if (process.defaultApp) {
  app.setAsDefaultProtocolClient('joanium', process.execPath, [path.resolve(process.argv[1])]);
} else {
  app.setAsDefaultProtocolClient('joanium');
}

// Handle incoming deep link (macOS/Linux)
app.on('open-url', (event, url) => {
  event.preventDefault();
  handleDeepLink(url);
});

// Handle incoming deep link (Windows — second instance)
app.on('second-instance', (event, commandLine) => {
  const url = commandLine.find((arg) => arg.startsWith('joanium://'));
  if (url) handleDeepLink(url);
  mainWindow.focus();
});
```

## Auto-Updates

```js
// Use electron-updater (part of electron-builder)
import { autoUpdater } from 'electron-updater';

autoUpdater.autoDownload = false; // Ask user before downloading
autoUpdater.autoInstallOnAppQuit = true;

autoUpdater.on('update-available', (info) => {
  mainWindow.webContents.send('update-available', info);
});

autoUpdater.on('download-progress', (progress) => {
  mainWindow.webContents.send('download-progress', progress);
});

autoUpdater.on('update-downloaded', () => {
  mainWindow.webContents.send('update-downloaded');
});

// Check on startup (after window is ready)
app.whenReady().then(() => {
  setTimeout(() => autoUpdater.checkForUpdates(), 3000);
});

// Trigger install from renderer
ipcMain.handle('install-update', () => autoUpdater.quitAndInstall());
```

**Update Server Options**

- GitHub Releases: `publish: [{ provider: 'github', owner: 'you', repo: 'joanium' }]`
- Custom S3: `publish: [{ provider: 's3', bucket: 'joanium-releases' }]`
- Electron-release-server: self-hosted update server

## Security Hardening

```js
// Content Security Policy — add to the BrowserWindow
win.webContents.session.webRequest.onHeadersReceived((details, callback) => {
  callback({
    responseHeaders: {
      ...details.responseHeaders,
      'Content-Security-Policy': [
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",
      ],
    },
  });
});

// Block navigation to external URLs
win.webContents.on('will-navigate', (event, url) => {
  const allowedHosts = ['localhost'];
  if (!allowedHosts.includes(new URL(url).hostname)) {
    event.preventDefault();
    shell.openExternal(url); // Open in user's browser instead
  }
});

// Block new window creation from renderer
win.webContents.setWindowOpenHandler(({ url }) => {
  shell.openExternal(url);
  return { action: 'deny' };
});
```

**Security Checklist**

- `contextIsolation: true` — always
- `nodeIntegration: false` — always
- `sandbox: true` — recommended for renderer processes
- Never use `enableRemoteModule: true` (deprecated and insecure)
- Validate all IPC input in the main process
- Don't load remote content with elevated privileges
- Sign and notarize your app (required for macOS Gatekeeper)

## Packaging & Distribution

**electron-builder** (recommended)

```json
// package.json
{
  "build": {
    "appId": "com.joanium.app",
    "productName": "Joanium",
    "directories": { "output": "release" },
    "files": ["dist/**/*", "src/main/**/*", "src/preload/**/*"],
    "mac": {
      "category": "public.app-category.productivity",
      "hardenedRuntime": true,
      "gatekeeperAssess": false,
      "entitlements": "build/entitlements.mac.plist",
      "notarize": { "teamId": "XXXXXXXXXX" }
    },
    "win": {
      "target": [{ "target": "nsis", "arch": ["x64", "arm64"] }],
      "certificateSubjectName": "Joanium Inc"
    },
    "linux": {
      "target": ["AppImage", "deb", "rpm"],
      "category": "Utility"
    },
    "publish": [{ "provider": "github", "owner": "joel", "repo": "joanium" }]
  }
}
```

```bash
# Build for current platform
npx electron-builder --publish never

# Build and publish a release
npx electron-builder --publish always
```

## Performance

**Avoiding Main Thread Blocking**

- Use `worker_threads` for CPU-intensive tasks (parsing, encryption, compression)
- Use `utilityProcess` (Electron 22+) for sandboxed child processes
- Never `require` heavy modules synchronously at startup — lazy-load them

**Memory Leak Prevention**

- Remove all `ipcRenderer.on` listeners when components unmount
- Use `webContents.on('destroyed', ...)` to clean up main-process references to windows
- Avoid storing large data in renderer global state — stream it instead
- Profile with Chrome DevTools Memory tab for renderer; use `process.memoryUsage()` for main

**Startup Performance**

- Lazy-load the main window — show a splash screen while loading
- Use `V8 snapshot` (via `electron-link`) for faster startup of large apps
- Avoid blocking `app.on('ready')` with synchronous I/O
