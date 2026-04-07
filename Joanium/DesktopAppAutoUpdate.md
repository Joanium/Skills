---
name: Desktop App Auto-Update & Distribution
trigger: auto update, electron updater, electron-updater, app update, desktop app distribution, code signing, dmg, exe installer, squirrel, app signing, notarization, release pipeline, electron-builder, tauri updater, publish release
description: Set up auto-update, packaging, code signing, and release pipelines for Electron desktop apps. Covers electron-builder, electron-updater, GitHub Releases publishing, code signing for macOS/Windows, and update UX.
---

# ROLE
You are a senior desktop app engineer. Your job is to build release pipelines that ship signed, auto-updating desktop apps reliably. The most common failure modes are unsigned builds blocked by OS security, broken update channels, and delta updates that corrupt app state.

# CORE PRINCIPLES
```
SIGN EVERYTHING:    Unsigned apps are blocked by macOS Gatekeeper and Windows SmartScreen
TEST UPDATES:       Test the update flow, not just the app — updates are the most broken path
STAGED ROLLOUTS:    Release to beta channel first, then stable
VERSION CAREFULLY:  Semver strictly — electron-updater compares versions to decide to update
NOTIFY GRACEFULLY:  Never force-restart mid-work — notify, let user decide when to restart
```

# ELECTRON-BUILDER SETUP

## package.json Configuration
```json
{
  "name": "my-app",
  "version": "1.2.0",
  "main": "dist/main.js",
  "scripts": {
    "build": "electron-builder build --publish never",
    "release": "electron-builder build --publish always",
    "release:mac": "electron-builder build --mac --publish always",
    "release:win": "electron-builder build --win --publish always",
    "release:linux": "electron-builder build --linux --publish always"
  },
  "build": {
    "appId": "com.yourcompany.myapp",
    "productName": "My App",
    "copyright": "Copyright © 2025 Your Name",
    "directories": {
      "buildResources": "assets",
      "output": "release"
    },
    "files": ["dist/**/*", "node_modules/**/*", "package.json"],
    "publish": {
      "provider": "github",
      "owner": "withinjoel",
      "repo": "my-app",
      "private": false
    },
    "mac": {
      "category": "public.app-category.productivity",
      "icon": "assets/icon.icns",
      "target": [
        { "target": "dmg", "arch": ["x64", "arm64"] },
        { "target": "zip", "arch": ["x64", "arm64"] }
      ],
      "hardenedRuntime": true,
      "entitlements": "assets/entitlements.mac.plist",
      "entitlementsInherit": "assets/entitlements.mac.plist",
      "gatekeeperAssess": false,
      "notarize": {
        "teamId": "YOUR_APPLE_TEAM_ID"
      }
    },
    "win": {
      "target": [
        { "target": "nsis", "arch": ["x64", "ia32"] }
      ],
      "icon": "assets/icon.ico",
      "certificateSubjectName": "Your Company Name",
      "signingHashAlgorithms": ["sha256"]
    },
    "linux": {
      "target": ["AppImage", "deb", "rpm"],
      "icon": "assets/icon.png",
      "category": "Utility"
    },
    "nsis": {
      "oneClick": false,
      "allowToChangeInstallationDirectory": true,
      "createDesktopShortcut": true,
      "createStartMenuShortcut": true
    }
  }
}
```

# AUTO-UPDATER (electron-updater)

## Main Process Update Handler
```javascript
// main/updater.js
import { autoUpdater } from 'electron-updater';
import { app, dialog, ipcMain } from 'electron';
import log from 'electron-log';

// Configure logging
autoUpdater.logger = log;
autoUpdater.logger.transports.file.level = 'info';

// Don't auto-download — let user decide
autoUpdater.autoDownload = false;
autoUpdater.autoInstallOnAppQuit = true;

let mainWindow = null;

export function initAutoUpdater(win) {
  mainWindow = win;

  // Check for updates on launch (after a short delay)
  setTimeout(() => checkForUpdates(), 3000);

  // Check again every 4 hours
  setInterval(() => checkForUpdates(), 4 * 60 * 60 * 1000);

  // Update available — ask user
  autoUpdater.on('update-available', (info) => {
    mainWindow?.webContents.send('update:available', {
      version: info.version,
      releaseNotes: info.releaseNotes,
      releaseDate: info.releaseDate,
    });
  });

  autoUpdater.on('update-not-available', () => {
    mainWindow?.webContents.send('update:not-available');
  });

  autoUpdater.on('download-progress', (progress) => {
    mainWindow?.webContents.send('update:progress', {
      percent: Math.round(progress.percent),
      transferred: progress.transferred,
      total: progress.total,
      bytesPerSecond: progress.bytesPerSecond,
    });
  });

  autoUpdater.on('update-downloaded', (info) => {
    mainWindow?.webContents.send('update:downloaded', { version: info.version });
  });

  autoUpdater.on('error', (err) => {
    log.error('Update error:', err);
    mainWindow?.webContents.send('update:error', { message: err.message });
  });

  // IPC: renderer can trigger download
  ipcMain.handle('update:download', () => autoUpdater.downloadUpdate());

  // IPC: renderer can trigger install and restart
  ipcMain.handle('update:install', () => {
    autoUpdater.quitAndInstall(false, true);
  });
}

async function checkForUpdates() {
  try {
    await autoUpdater.checkForUpdates();
  } catch (err) {
    log.error('Failed to check for updates:', err);
  }
}
```

## Renderer — Update Notification UI (React)
```javascript
// hooks/useAutoUpdate.js
import { useState, useEffect } from 'react';

export function useAutoUpdate() {
  const [updateState, setUpdateState] = useState({
    available: false,
    downloading: false,
    downloaded: false,
    progress: 0,
    version: null,
    error: null,
  });

  useEffect(() => {
    const unsubs = [
      window.electronAPI.on('update:available', ({ version }) =>
        setUpdateState(s => ({ ...s, available: true, version }))),

      window.electronAPI.on('update:progress', ({ percent }) =>
        setUpdateState(s => ({ ...s, downloading: true, progress: percent }))),

      window.electronAPI.on('update:downloaded', ({ version }) =>
        setUpdateState(s => ({ ...s, downloading: false, downloaded: true, version }))),

      window.electronAPI.on('update:error', ({ message }) =>
        setUpdateState(s => ({ ...s, error: message }))),
    ];

    return () => unsubs.forEach(fn => fn());
  }, []);

  const downloadUpdate = () => window.electronAPI.invoke('update:download');
  const installUpdate = () => window.electronAPI.invoke('update:install');

  return { updateState, downloadUpdate, installUpdate };
}

// UpdateBanner.jsx
function UpdateBanner() {
  const { updateState, downloadUpdate, installUpdate } = useAutoUpdate();

  if (updateState.downloaded) {
    return (
      <div className="update-banner">
        <span>v{updateState.version} downloaded — restart to apply</span>
        <button onClick={installUpdate}>Restart Now</button>
        <button onClick={() => {}}>Later</button>
      </div>
    );
  }

  if (updateState.downloading) {
    return (
      <div className="update-banner">
        <span>Downloading update... {updateState.progress}%</span>
        <progress value={updateState.progress} max={100} />
      </div>
    );
  }

  if (updateState.available) {
    return (
      <div className="update-banner">
        <span>v{updateState.version} available</span>
        <button onClick={downloadUpdate}>Download</button>
        <button onClick={() => {}}>Skip</button>
      </div>
    );
  }

  return null;
}
```

# CODE SIGNING

## macOS Signing Setup
```bash
# Prerequisites:
# 1. Apple Developer account ($99/year)
# 2. "Developer ID Application" certificate in Keychain
# 3. App-specific password for notarization

# Environment variables needed in CI
export CSC_LINK="path/to/certificate.p12"       # or base64 encoded
export CSC_KEY_PASSWORD="certificate_password"
export APPLE_ID="your@apple.id"
export APPLE_APP_SPECIFIC_PASSWORD="xxxx-xxxx-xxxx-xxxx"
export APPLE_TEAM_ID="XXXXXXXXXX"
```

## Windows Signing
```bash
# Prerequisites:
# 1. EV Code Signing Certificate (~$250-400/year from DigiCert, Sectigo)
# 2. USB token or HSM with certificate

# Environment variables
export WIN_CSC_LINK="path/to/certificate.pfx"
export WIN_CSC_KEY_PASSWORD="certificate_password"
# Or using Azure Trusted Signing (cheaper):
export AZURE_TENANT_ID="..."
export AZURE_CLIENT_ID="..."
export AZURE_CLIENT_SECRET="..."
```

## macOS Entitlements
```xml
<!-- assets/entitlements.mac.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "...">
<plist version="1.0">
<dict>
  <!-- Required for Hardened Runtime -->
  <key>com.apple.security.cs.allow-jit</key><true/>
  <key>com.apple.security.cs.allow-unsigned-executable-memory</key><true/>
  <!-- For network access -->
  <key>com.apple.security.network.client</key><true/>
  <!-- For file access -->
  <key>com.apple.security.files.user-selected.read-write</key><true/>
</dict>
</plist>
```

# GITHUB ACTIONS RELEASE PIPELINE
```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags: ['v*']

jobs:
  release:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [macos-latest, windows-latest, ubuntu-latest]

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20

      - run: npm ci

      - name: Build & Release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          # macOS signing
          CSC_LINK: ${{ secrets.MAC_CERT_P12_BASE64 }}
          CSC_KEY_PASSWORD: ${{ secrets.MAC_CERT_PASSWORD }}
          APPLE_ID: ${{ secrets.APPLE_ID }}
          APPLE_APP_SPECIFIC_PASSWORD: ${{ secrets.APPLE_APP_SPECIFIC_PASSWORD }}
          APPLE_TEAM_ID: ${{ secrets.APPLE_TEAM_ID }}
          # Windows signing
          WIN_CSC_LINK: ${{ secrets.WIN_CERT_P12_BASE64 }}
          WIN_CSC_KEY_PASSWORD: ${{ secrets.WIN_CERT_PASSWORD }}
        run: npm run release
```

# VERSIONING WORKFLOW
```
Commit types → version bumps:
  fix:      → patch (1.0.0 → 1.0.1)
  feat:     → minor (1.0.0 → 1.1.0)
  BREAKING: → major (1.0.0 → 2.0.0)

Release channels:
  beta:   electron-builder publish with channel: 'beta'
  stable: electron-builder publish with channel: 'latest'

electron-updater checks:
  Mac:    latest-mac.yml / beta-mac.yml
  Win:    latest.yml / beta.yml
  Linux:  latest-linux.yml

Skip a version:
  autoUpdater.allowPrerelease = false  // won't download beta/alpha
  // User can opt-in to beta via settings
```

# CHECKLIST
```
[ ] electron-builder configured with correct appId and productName
[ ] GitHub Releases set as publish provider with correct repo
[ ] autoDownload: false (user controls when to download)
[ ] Update events forwarded to renderer via IPC
[ ] Renderer shows update banner with download + later options
[ ] macOS: hardened runtime + entitlements configured
[ ] macOS: notarization credentials in CI environment
[ ] Windows: EV certificate or Azure Trusted Signing set up
[ ] GitHub Actions workflow builds all platforms on tag push
[ ] autoInstallOnAppQuit: true (installs on next quit if not manually triggered)
[ ] Version in package.json matches git tag before release
```
