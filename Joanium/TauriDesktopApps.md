---
name: Tauri Desktop Apps
trigger: tauri, tauri app, tauri v2, tauri vs electron, tauri rust, tauri commands, tauri events, tauri frontend, tauri updater, tauri permissions, tauri plugins, tauri bundling, lightweight desktop app, rust desktop
description: Build lightweight, secure desktop apps with Tauri v2. Covers project setup, Rust commands, frontend integration, event system, file system access, auto-updater, permissions model, and comparison with Electron.
---

# ROLE
You are a senior Tauri/Rust developer. Your job is to build desktop apps that are dramatically smaller and more efficient than Electron equivalents. Tauri's main complexity is the Rust backend — you handle it with clear patterns that frontend developers can follow without deep Rust knowledge.

# TAURI VS ELECTRON
```
                    Tauri v2        Electron
Bundle size:        ~5–10MB         ~120–200MB
Memory (idle):      ~15–30MB        ~80–150MB
CPU (idle):         ~0%             ~1–3%
Startup time:       ~200ms          ~1–3s
Language:           Rust + JS/TS    Node.js + JS/TS
Security model:     Capability-based Permission: all
Webview:            OS native       Bundled Chromium
IPC overhead:       Very low        Low

Choose Tauri when:
  - App size and memory matter
  - You want a modern security model
  - You're building a performance-critical tool
  - Team has or can learn basic Rust

Choose Electron when:
  - Maximum Node.js ecosystem compatibility needed
  - Team has no Rust experience
  - App needs consistent cross-platform browser behavior
  - Rapid prototyping is priority
```

# SETUP

## Prerequisites
```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env
rustup update

# Linux only
sudo apt-get install libwebkit2gtk-4.1-dev libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev

# Install Tauri CLI
npm install -D @tauri-apps/cli
```

## Create New Project
```bash
# With Vite + React (recommended)
npm create tauri-app@latest my-app -- --template react-ts

# Or add to existing frontend
npm install -D @tauri-apps/cli
npm install @tauri-apps/api
npx tauri init

# Project structure:
# src/           → frontend (React/Vue/Svelte)
# src-tauri/     → Rust backend
#   src/
#     main.rs    → app entry point
#     lib.rs     → command handlers
#   Cargo.toml   → Rust dependencies
#   tauri.conf.json → app config

# Dev mode
npm run tauri dev

# Build
npm run tauri build
```

# CONFIGURATION (tauri.conf.json)
```json
{
  "$schema": "https://schema.tauri.app/config/2",
  "productName": "My App",
  "version": "1.0.0",
  "identifier": "com.yourcompany.myapp",
  "build": {
    "frontendDist": "../dist",
    "devUrl": "http://localhost:5173",
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build"
  },
  "app": {
    "withGlobalTauri": true,
    "windows": [
      {
        "title": "My App",
        "width": 1200,
        "height": 800,
        "minWidth": 800,
        "minHeight": 600,
        "resizable": true,
        "fullscreen": false,
        "decorations": true,
        "transparent": false
      }
    ]
  },
  "bundle": {
    "active": true,
    "targets": "all",
    "icon": ["icons/32x32.png", "icons/128x128.png", "icons/icon.icns", "icons/icon.ico"],
    "macOS": { "minimumSystemVersion": "10.13" },
    "windows": { "wix": { "language": "en-US" } }
  },
  "plugins": {
    "updater": {
      "pubkey": "YOUR_PUBLIC_KEY",
      "endpoints": ["https://releases.yourapp.com/{{target}}/{{arch}}/{{current_version}}"]
    }
  }
}
```

# RUST COMMANDS (Backend)

## src-tauri/src/lib.rs
```rust
use tauri::Manager;
use std::fs;
use std::path::PathBuf;
use serde::{Serialize, Deserialize};

// Data types — must implement Serialize + Deserialize for IPC
#[derive(Debug, Serialize, Deserialize)]
pub struct FileEntry {
    name: String,
    path: String,
    is_dir: bool,
    size: u64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CommandError {
    message: String,
    code: String,
}

// Tauri commands — annotated functions callable from frontend
#[tauri::command]
async fn read_file(path: String) -> Result<String, String> {
    fs::read_to_string(&path).map_err(|e| e.to_string())
}

#[tauri::command]
async fn write_file(path: String, content: String) -> Result<(), String> {
    // Create parent dirs if needed
    if let Some(parent) = PathBuf::from(&path).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    fs::write(&path, content).map_err(|e| e.to_string())
}

#[tauri::command]
async fn list_dir(path: String) -> Result<Vec<FileEntry>, String> {
    let entries = fs::read_dir(&path).map_err(|e| e.to_string())?;
    
    let mut result = Vec::new();
    for entry in entries.flatten() {
        let metadata = entry.metadata().map_err(|e| e.to_string())?;
        result.push(FileEntry {
            name: entry.file_name().to_string_lossy().into_owned(),
            path: entry.path().to_string_lossy().into_owned(),
            is_dir: metadata.is_dir(),
            size: metadata.len(),
        });
    }
    Ok(result)
}

// Command with app handle (access to window, paths, etc.)
#[tauri::command]
async fn get_app_data_dir(app: tauri::AppHandle) -> Result<String, String> {
    app.path().app_data_dir()
        .map(|p| p.to_string_lossy().into_owned())
        .map_err(|e| e.to_string())
}

// Register commands in main.rs
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            read_file,
            write_file,
            list_dir,
            get_app_data_dir,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

# FRONTEND INTEGRATION (TypeScript)

## Calling Rust Commands
```typescript
import { invoke } from '@tauri-apps/api/core';

// Type-safe wrappers around invoke
async function readFile(path: string): Promise<string> {
  return invoke<string>('read_file', { path });
}

async function writeFile(path: string, content: string): Promise<void> {
  return invoke<void>('write_file', { path, content });
}

async function listDir(path: string) {
  return invoke<Array<{ name: string; path: string; isDir: boolean; size: number }>>('list_dir', { path });
}

// Error handling — commands return Result<T, String> in Rust
try {
  const content = await readFile('/path/to/file.txt');
} catch (error) {
  // error is the String from Err(e.to_string())
  console.error('Failed to read file:', error);
}
```

## Event System
```typescript
import { emit, listen } from '@tauri-apps/api/event';

// Listen to events from Rust or other windows
const unlisten = await listen<{ progress: number }>('download-progress', (event) => {
  console.log('Progress:', event.payload.progress);
  updateProgressBar(event.payload.progress);
});

// Cleanup
onUnmount(() => unlisten());

// Emit from frontend (to all windows or specific window)
await emit('user-action', { type: 'save', data: formData });
```

```rust
// Emit from Rust to frontend
use tauri::Emitter;

#[tauri::command]
async fn start_download(url: String, app: tauri::AppHandle) -> Result<(), String> {
    // Start download in background
    tauri::async_runtime::spawn(async move {
        for progress in download_file(&url).await {
            app.emit("download-progress", serde_json::json!({ "progress": progress }))
                .unwrap();
        }
    });
    Ok(())
}
```

# PLUGINS (COMMON)

## Adding Official Plugins
```bash
# File system
npm install @tauri-apps/plugin-fs
cargo add tauri-plugin-fs

# Dialog (file picker)
npm install @tauri-apps/plugin-dialog
cargo add tauri-plugin-dialog

# Shell (open URLs, run commands)
npm install @tauri-apps/plugin-shell
cargo add tauri-plugin-shell

# Store (persistent key-value)
npm install @tauri-apps/plugin-store
cargo add tauri-plugin-store

# HTTP (fetch from Rust)
npm install @tauri-apps/plugin-http
cargo add tauri-plugin-http

# Updater
npm install @tauri-apps/plugin-updater
cargo add tauri-plugin-updater

# Clipboard
npm install @tauri-apps/plugin-clipboard-manager
cargo add tauri-plugin-clipboard-manager
```

## Using fs Plugin
```typescript
import { readTextFile, writeTextFile, readDir, exists } from '@tauri-apps/plugin-fs';
import { appDataDir, join } from '@tauri-apps/api/path';

const dataDir = await appDataDir();
const filePath = await join(dataDir, 'settings.json');

// Read
const content = await readTextFile(filePath);
const settings = JSON.parse(content);

// Write
await writeTextFile(filePath, JSON.stringify(settings, null, 2));

// List directory
const entries = await readDir(dataDir);
```

# PERMISSIONS MODEL (tauri.conf.json)
```json
{
  "app": {
    "security": {
      "capabilities": [
        {
          "identifier": "default",
          "description": "Default app permissions",
          "windows": ["main"],
          "permissions": [
            "core:default",
            "fs:allow-read-text-file",
            "fs:allow-write-text-file",
            "fs:allow-read-dir",
            "dialog:allow-open",
            "dialog:allow-save",
            "shell:allow-open"
          ]
        }
      ]
    }
  }
}
```

# AUTO-UPDATER
```typescript
import { check } from '@tauri-apps/plugin-updater';
import { relaunch } from '@tauri-apps/plugin-process';

async function checkForUpdates() {
  const update = await check();
  if (!update) return;

  console.log(`Update available: ${update.version}`);

  // Download and install
  await update.downloadAndInstall((event) => {
    if (event.event === 'Progress') {
      updateProgressUI(event.data.chunkLength, event.data.contentLength);
    }
  });

  // Restart app
  await relaunch();
}
```

# TROUBLESHOOTING
```
"command not found" after invoke:
  → Command not registered in generate_handler![]
  → Function name must match exactly (snake_case in Rust → camelCase in JS is auto-converted)

Rust build fails:
  → Run: cargo build in src-tauri/ to see detailed errors
  → Missing system libraries on Linux: install libwebkit2gtk-4.1-dev

Permission denied on file access:
  → Add required fs permission in capabilities config
  → Path must be within allowed directories

WebSocket/fetch blocked:
  → Add to CSP in tauri.conf.json: "contentSecurityPolicy": "..."
  → For external API calls, use Rust http plugin instead of frontend fetch
```
