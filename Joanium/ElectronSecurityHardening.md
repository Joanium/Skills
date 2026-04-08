---
name: Electron Security Hardening
trigger: electron security, context isolation, nodeIntegration, preload script security, electron CSP, content security policy electron, electron sandbox, electron vulnerabilities, secure electron app, electron xss, remote module electron, webview security, electron hardening, electron safe defaults
description: Harden Electron applications against common attack vectors. Covers context isolation, nodeIntegration, CSP, preload best practices, sandbox mode, permission handling, and safe IPC design.
---

# ROLE
You are a security engineer who specializes in Electron desktop apps. You know that Electron apps run Chromium + Node.js together, and that a single XSS vulnerability in a poorly configured Electron app gives an attacker full OS access — not just browser sandbox escape. Your job is to close every attack surface.

# WHY ELECTRON SECURITY IS DIFFERENT
```
In a browser:     XSS → attacker reads cookies, redirects pages, steals session
In Electron:      XSS + nodeIntegration:true → attacker runs arbitrary Node.js
                  → reads filesystem, spawns processes, full OS compromise

The threat model: Electron renders web content (local HTML or remote URLs).
Any content with script access + Node.js access = full system compromise.
```

# THE NON-NEGOTIABLE BASELINE

## BrowserWindow Defaults — Lock These Down
```javascript
// main.js — EVERY BrowserWindow must have these settings

const { BrowserWindow } = require('electron');

const win = new BrowserWindow({
  webPreferences: {
    // CRITICAL — these two together are the most important:
    contextIsolation: true,        // NEVER set to false — isolates preload from renderer
    nodeIntegration: false,        // NEVER set to true for any window loading external content

    // Sandbox renderer processes (Chrome-style sandbox, no Node access at all)
    sandbox: true,

    // Disable remote module (deprecated, dangerous, removed in Electron 14+)
    enableRemoteModule: false,

    // No Node.js in workers either
    nodeIntegrationInWorker: false,
    nodeIntegrationInSubFrames: false,

    // Only load your own preload — never dynamic preload paths
    preload: path.join(__dirname, 'preload.js'),

    // Disable web security ONLY for local dev with specific need — NEVER in production
    webSecurity: true,

    // Control which origins your renderer can navigate to
    // (see navigation validation below)
  }
});

// Load only local files or trusted origins
win.loadFile('index.html');
// OR if loading URL:
win.loadURL('https://your-own-domain.com');
```

## Context Isolation — What It Does
```javascript
// contextIsolation: true means:
// preload.js runs in a SEPARATE JavaScript context from the renderer page
// window, document are shared DOM — but the JavaScript scope is isolated
// renderer cannot access preload's require() or Node.js globals

// WRONG — without contextIsolation this would leak Node to renderer:
// window.nodeRequire = require;  // in preload

// CORRECT — expose ONLY what you intend via contextBridge:
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // Expose only specific, validated functions
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  openFile: (filter) => ipcRenderer.invoke('open-file', filter),
  onUpdate: (callback) => ipcRenderer.on('update-available', (_, info) => callback(info))
});

// renderer.js can now use window.electronAPI.getAppVersion()
// but cannot access require, process, __dirname, or any Node.js API
```

# PRELOAD SCRIPT SECURITY

## Never Expose Raw IPC
```javascript
// BAD — renderer gets full IPC access, can call ANY channel
contextBridge.exposeInMainWorld('ipc', {
  send: (channel, ...args) => ipcRenderer.send(channel, ...args),
  invoke: (channel, ...args) => ipcRenderer.invoke(channel, ...args)
});
// Attacker XSS in renderer → calls ipcRenderer.invoke('exec-shell', 'rm -rf /')

// GOOD — allowlist only the channels you actually need
const ALLOWED_INVOKE_CHANNELS = ['get-version', 'open-file', 'read-settings'];
const ALLOWED_SEND_CHANNELS = ['log-event', 'resize-window'];

contextBridge.exposeInMainWorld('electronAPI', {
  invoke: (channel, data) => {
    if (!ALLOWED_INVOKE_CHANNELS.includes(channel)) {
      throw new Error(`Channel not permitted: ${channel}`);
    }
    return ipcRenderer.invoke(channel, data);
  },
  send: (channel, data) => {
    if (!ALLOWED_SEND_CHANNELS.includes(channel)) {
      throw new Error(`Channel not permitted: ${channel}`);
    }
    ipcRenderer.send(channel, data);
  }
});
```

## Validate and Sanitize IPC Data in Main Process
```javascript
// main.js — NEVER trust data from renderer
const { ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');

ipcMain.handle('read-file', async (event, filePath) => {
  // Validate sender
  if (!event.senderFrame.url.startsWith('file://')) {
    throw new Error('Unauthorized sender');
  }

  // Validate input type
  if (typeof filePath !== 'string') {
    throw new Error('Invalid filePath type');
  }

  // Prevent path traversal — only allow reads within user data dir
  const resolved = path.resolve(filePath);
  const allowed = path.resolve(app.getPath('userData'));
  if (!resolved.startsWith(allowed)) {
    throw new Error(`Path traversal attempt: ${filePath}`);
  }

  return fs.promises.readFile(resolved, 'utf8');
});

ipcMain.handle('open-file', async (event) => {
  // Use dialog — let the OS handle path selection, no user-provided path
  const { filePaths } = await dialog.showOpenDialog({ properties: ['openFile'] });
  return filePaths[0] ?? null;
  // No path traversal possible — user selected via OS dialog
});
```

# CONTENT SECURITY POLICY (CSP)

## Set CSP in Meta Tag (Local HTML)
```html
<!-- index.html — restrictive CSP -->
<meta http-equiv="Content-Security-Policy"
  content="
    default-src 'self';
    script-src 'self';
    style-src 'self' 'unsafe-inline';
    img-src 'self' data: https:;
    connect-src 'self' https://api.yourdomain.com;
    font-src 'self';
    object-src 'none';
    base-uri 'self';
    form-action 'self';
  "
>

<!-- No 'unsafe-eval' → blocks eval(), Function() constructor, setTimeout(string) -->
<!-- No 'unsafe-inline' scripts → blocks inline <script> tags, onclick= attributes -->
<!-- object-src 'none' → blocks <object>, <embed>, <applet> -->
```

## Set CSP via Session Headers (More Secure)
```javascript
// main.js — CSP via response headers, harder to override
const { session } = require('electron');

app.whenReady().then(() => {
  session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        'Content-Security-Policy': [
          "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; object-src 'none'"
        ]
      }
    });
  });
});
```

# NAVIGATION AND NEW WINDOW RESTRICTIONS

## Block Navigation to Unexpected Origins
```javascript
// main.js — prevent renderer from navigating to arbitrary URLs
app.on('web-contents-created', (event, contents) => {

  // Block all navigation — renderer should not navigate itself
  contents.on('will-navigate', (event, navigationUrl) => {
    const parsedUrl = new URL(navigationUrl);
    const allowed = ['file:', 'app:'];

    if (!allowed.includes(parsedUrl.protocol)) {
      event.preventDefault();
      // Open in default browser instead
      shell.openExternal(navigationUrl);
    }
  });

  // Block ALL new window creation from renderer
  contents.setWindowOpenHandler(({ url }) => {
    // If it's a trusted URL, open in browser — NEVER create new Electron windows from renderer
    if (url.startsWith('https://yourdomain.com')) {
      shell.openExternal(url);
    }
    return { action: 'deny' };  // deny new window creation
  });
});
```

# SAFE EXTERNAL URL HANDLING
```javascript
const { shell } = require('electron');

// ALWAYS validate before opening external URLs
function safeOpenExternal(url) {
  try {
    const parsed = new URL(url);
    // Only allow http/https — block file://, javascript:, data:
    if (!['http:', 'https:'].includes(parsed.protocol)) {
      throw new Error(`Blocked protocol: ${parsed.protocol}`);
    }
    shell.openExternal(url);
  } catch (err) {
    console.error('Blocked unsafe URL:', url, err.message);
  }
}

// In renderer (via contextBridge):
contextBridge.exposeInMainWorld('electronAPI', {
  openExternal: (url) => ipcRenderer.invoke('open-external', url)
});

// In main:
ipcMain.handle('open-external', (event, url) => safeOpenExternal(url));
```

# PERMISSION HANDLING
```javascript
// main.js — explicitly deny permissions you don't need
session.defaultSession.setPermissionRequestHandler((webContents, permission, callback) => {
  const allowedPermissions = ['notifications'];  // only what your app needs
  callback(allowedPermissions.includes(permission));
});

session.defaultSession.setPermissionCheckHandler((webContents, permission) => {
  const allowedPermissions = ['notifications'];
  return allowedPermissions.includes(permission);
});
```

# DEPENDENCY SECURITY
```bash
# Audit npm dependencies regularly
npm audit
npm audit fix

# Check for known vulnerable Electron versions
npx electronegativity  # scans for Electron misconfigurations

# Pin Electron version — don't use ranges
# package.json:
# "electron": "28.1.0"  ← exact, not "^28.0.0"

# Keep Electron updated — security patches are released frequently
```

# DEVTOOLS IN PRODUCTION
```javascript
// Disable DevTools in production builds
app.whenReady().then(() => {
  if (app.isPackaged) {
    // Remove keyboard shortcuts to open DevTools
    const { Menu } = require('electron');
    Menu.setApplicationMenu(null);  // or build menu without dev tools item
  }
});

// In BrowserWindow creation:
const win = new BrowserWindow({ ... });
if (app.isPackaged) {
  win.webContents.on('devtools-opened', () => {
    win.webContents.closeDevTools();
  });
}
```

# SECURE UPDATE MECHANISM
```javascript
// Only accept updates from your own server, verify signatures
const { autoUpdater } = require('electron-updater');

autoUpdater.setFeedURL({
  provider: 'generic',
  url: 'https://updates.yourdomain.com'
  // electron-updater verifies code signature automatically for production builds
});

// Never accept update URLs from renderer
// Never load update zips from arbitrary URLs
```

# SECURITY AUDIT CHECKLIST
```
[ ] contextIsolation: true on ALL BrowserWindows
[ ] nodeIntegration: false on ALL BrowserWindows
[ ] sandbox: true where no preload native access needed
[ ] contextBridge used — no raw IPC exposed to renderer
[ ] IPC channels allowlisted in both preload and main
[ ] All IPC input validated and sanitized in main process
[ ] Path traversal prevented for any file system operations
[ ] CSP header set and blocks unsafe-eval, unsafe-inline scripts
[ ] Navigation locked down — will-navigate and setWindowOpenHandler
[ ] External URLs validated before shell.openExternal()
[ ] Permission handler denies all non-required permissions
[ ] DevTools disabled or inaccessible in production
[ ] Electron version up to date — check security advisories
[ ] npm audit clean or all issues reviewed
[ ] No sensitive data stored in renderer localStorage (accessible to any script)
[ ] Auto-updater using code-signed packages from your own infrastructure
```
