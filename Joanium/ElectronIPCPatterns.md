---
name: Electron IPC Patterns
trigger: electron ipc, ipcMain, ipcRenderer, electron main process, electron renderer process, preload script, contextBridge, electron communication, electron api, invoke, handle, electron security, electron channels
description: Design secure, type-safe IPC communication between Electron's main and renderer processes. Covers contextBridge, invoke/handle patterns, event channels, file system access, and security best practices.
---

# ROLE
You are a senior Electron developer. Your job is to design IPC systems that are secure, predictable, and easy to maintain. The most common Electron security mistakes (nodeIntegration: true, no contextIsolation) happen at the IPC layer — you prevent them.

# CORE PRINCIPLES
```
NO nodeIntegration:  Never enable nodeIntegration in renderer — use contextBridge
CONTEXTBRIDGE:       Only expose specific APIs through contextBridge, not entire modules
VALIDATE INPUTS:     Main process validates all renderer inputs — renderer is untrusted
INVOKE/HANDLE:       Use ipcMain.handle + ipcRenderer.invoke for request-response
ONE-WAY EVENTS:      Use ipcMain.on + webContents.send for push notifications
WHITELIST CHANNELS:  Never use dynamic channel names — enumerate allowed channels
```

# ARCHITECTURE

## Process Model
```
┌─────────────────────────────────────────────────────┐
│  RENDERER PROCESS (web content — untrusted)         │
│  React/HTML/CSS + your UI code                      │
│  No direct Node.js access                           │
│                          │                          │
│              window.electronAPI (exposed API)        │
└──────────────────────────│──────────────────────────┘
                           │ contextBridge
┌──────────────────────────│──────────────────────────┐
│  PRELOAD SCRIPT (bridge — partial trust)             │
│  Runs in renderer context but has Node access        │
│  Exposes safe subset via contextBridge              │
└──────────────────────────│──────────────────────────┘
                           │ IPC
┌──────────────────────────│──────────────────────────┐
│  MAIN PROCESS (Node.js — full trust)                │
│  File system, OS APIs, child processes              │
│  All privileged operations run here                 │
└─────────────────────────────────────────────────────┘
```

# IMPLEMENTATION

## Main Process Setup (main.js)
```javascript
const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const fs = require('fs/promises');

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,   // ✓ REQUIRED
      nodeIntegration: false,   // ✓ REQUIRED
      sandbox: true,            // ✓ Recommended
    },
  });

  win.loadFile('dist/index.html');  // or loadURL for dev
}

app.whenReady().then(createWindow);
```

## Preload Script (preload.js)
```javascript
const { contextBridge, ipcRenderer } = require('electron');

// Whitelist of allowed channels
const INVOKE_CHANNELS = [
  'fs:readFile', 'fs:writeFile', 'fs:listDir', 'fs:deleteFile',
  'dialog:openFile', 'dialog:saveFile',
  'app:getVersion', 'app:openExternal',
  'llm:chat', 'llm:abort',
  'settings:get', 'settings:set',
];

const EVENT_CHANNELS = [
  'llm:token', 'llm:done', 'llm:error',
  'download:progress', 'download:complete',
  'app:updateAvailable',
];

contextBridge.exposeInMainWorld('electronAPI', {
  // Request-response pattern
  invoke: (channel, ...args) => {
    if (!INVOKE_CHANNELS.includes(channel)) {
      throw new Error(`Unauthorized IPC channel: ${channel}`);
    }
    return ipcRenderer.invoke(channel, ...args);
  },

  // Subscribe to events from main
  on: (channel, callback) => {
    if (!EVENT_CHANNELS.includes(channel)) {
      throw new Error(`Unauthorized event channel: ${channel}`);
    }
    const handler = (_, ...args) => callback(...args);
    ipcRenderer.on(channel, handler);
    return () => ipcRenderer.removeListener(channel, handler);  // returns unsubscribe fn
  },

  // One-time listener
  once: (channel, callback) => {
    if (!EVENT_CHANNELS.includes(channel)) throw new Error(`Unauthorized: ${channel}`);
    ipcRenderer.once(channel, (_, ...args) => callback(...args));
  },
});
```

## IPC Handlers (main process)
```javascript
// File system handlers
ipcMain.handle('fs:readFile', async (event, filePath) => {
  // Validate: sanitize path, check allowed directories
  const resolved = path.resolve(filePath);
  const allowedDirs = [app.getPath('userData'), app.getPath('documents')];
  const isAllowed = allowedDirs.some(dir => resolved.startsWith(dir));
  
  if (!isAllowed) throw new Error(`Access denied: ${filePath}`);
  
  const content = await fs.readFile(resolved, 'utf-8');
  return content;
});

ipcMain.handle('fs:writeFile', async (event, filePath, content) => {
  if (typeof content !== 'string') throw new Error('Content must be a string');
  const resolved = path.resolve(filePath);
  await fs.mkdir(path.dirname(resolved), { recursive: true });
  await fs.writeFile(resolved, content, 'utf-8');
  return { success: true };
});

ipcMain.handle('fs:listDir', async (event, dirPath) => {
  const resolved = path.resolve(dirPath);
  const entries = await fs.readdir(resolved, { withFileTypes: true });
  return entries.map(e => ({
    name: e.name,
    path: path.join(resolved, e.name),
    isDirectory: e.isDirectory(),
    isFile: e.isFile(),
  }));
});

// Dialog handlers
ipcMain.handle('dialog:openFile', async (event, options = {}) => {
  const result = await dialog.showOpenDialog({
    properties: ['openFile'],
    filters: options.filters || [{ name: 'All Files', extensions: ['*'] }],
  });
  return result;  // { canceled: bool, filePaths: string[] }
});

ipcMain.handle('dialog:saveFile', async (event, options = {}) => {
  const result = await dialog.showSaveDialog({
    defaultPath: options.defaultPath,
    filters: options.filters,
  });
  return result;  // { canceled: bool, filePath: string }
});

// Open URL in system browser
ipcMain.handle('app:openExternal', async (event, url) => {
  // Whitelist protocols
  if (!url.startsWith('https://') && !url.startsWith('http://')) {
    throw new Error('Only HTTP/HTTPS URLs allowed');
  }
  await shell.openExternal(url);
});

ipcMain.handle('app:getVersion', () => app.getVersion());
```

## Pushing Events from Main to Renderer
```javascript
// Get reference to window
let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({ ... });
}

// Push token events during LLM streaming
async function streamLLMResponse(prompt, webContents) {
  try {
    for await (const token of llm.stream(prompt)) {
      webContents.send('llm:token', { token });
    }
    webContents.send('llm:done', {});
  } catch (err) {
    webContents.send('llm:error', { message: err.message });
  }
}

ipcMain.handle('llm:chat', async (event, messages) => {
  // Start streaming — don't await, let events flow
  streamLLMResponse(messages, event.sender);
  return { started: true };
});
```

## Type-Safe IPC (TypeScript)
```typescript
// ipc-types.ts — shared between preload and renderer
export interface IpcChannels {
  invoke: {
    'fs:readFile': { args: [string]; return: string };
    'fs:writeFile': { args: [string, string]; return: { success: boolean } };
    'dialog:openFile': { args: [{ filters?: any[] }?]; return: Electron.OpenDialogReturnValue };
    'llm:chat': { args: [Message[]]; return: { started: boolean } };
    'settings:get': { args: [string]; return: unknown };
    'settings:set': { args: [string, unknown]; return: void };
  };
  events: {
    'llm:token': { token: string };
    'llm:done': Record<string, never>;
    'llm:error': { message: string };
    'download:progress': { percent: number; bytesReceived: number };
  };
}

// Typed wrapper in renderer
const api = window.electronAPI as ElectronAPI;
```

# RENDERER USAGE PATTERNS

## React Integration
```javascript
// hooks/useIPC.js
import { useEffect, useCallback } from 'react';

export function useIPCEvent(channel, handler) {
  useEffect(() => {
    const unsubscribe = window.electronAPI.on(channel, handler);
    return unsubscribe;  // cleanup on unmount
  }, [channel, handler]);
}

// hooks/useLLMStream.js
export function useLLMStream() {
  const [output, setOutput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);

  useIPCEvent('llm:token', useCallback(({ token }) => {
    setOutput(prev => prev + token);
  }, []));

  useIPCEvent('llm:done', useCallback(() => {
    setIsStreaming(false);
  }, []));

  useIPCEvent('llm:error', useCallback(({ message }) => {
    console.error('LLM error:', message);
    setIsStreaming(false);
  }, []));

  const sendMessage = useCallback(async (messages) => {
    setOutput('');
    setIsStreaming(true);
    await window.electronAPI.invoke('llm:chat', messages);
  }, []);

  return { output, isStreaming, sendMessage };
}

// Usage in component
function ChatWindow() {
  const { output, isStreaming, sendMessage } = useLLMStream();
  return (
    <div>
      <pre>{output}</pre>
      <button onClick={() => sendMessage(messages)} disabled={isStreaming}>
        {isStreaming ? 'Streaming...' : 'Send'}
      </button>
    </div>
  );
}
```

# COMMON PATTERNS

## Settings Store
```javascript
// main: simple JSON settings
const settingsPath = path.join(app.getPath('userData'), 'settings.json');

ipcMain.handle('settings:get', async (_, key) => {
  try {
    const data = JSON.parse(await fs.readFile(settingsPath, 'utf-8'));
    return key ? data[key] : data;
  } catch { return key ? undefined : {}; }
});

ipcMain.handle('settings:set', async (_, key, value) => {
  let data = {};
  try { data = JSON.parse(await fs.readFile(settingsPath, 'utf-8')); } catch {}
  data[key] = value;
  await fs.writeFile(settingsPath, JSON.stringify(data, null, 2));
});
```

# SECURITY CHECKLIST
```
[ ] contextIsolation: true (default in Electron 12+, but verify)
[ ] nodeIntegration: false
[ ] Channel whitelist enforced in preload (never pass raw channel from renderer)
[ ] Input validation in all ipcMain.handle callbacks
[ ] File paths sanitized and restricted to allowed directories
[ ] External URLs validated before shell.openExternal
[ ] No sensitive data (API keys) stored in renderer state — keep in main
[ ] No eval() or dynamic code execution from renderer input
[ ] CSP configured in renderer: Content-Security-Policy meta tag or HTTP header
```
