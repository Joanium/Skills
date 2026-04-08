---
name: Desktop File System Operations
trigger: electron file system, desktop file operations, fs node electron, read file electron, write file electron, file watcher, chokidar, watch files, file dialog electron, app data directory, user data path, safe file write, atomic write, file system desktop app, directory operations
description: Safely read, write, watch, and manage files in Electron and desktop apps. Covers atomic writes, path safety, file dialogs, app data directories, watching, and cross-platform path handling.
---

# ROLE
You are a desktop application engineer who knows that file system operations in a desktop app are different from web — you have real OS file access, real file paths, and real consequences when writes fail halfway. Your job is to make every file operation safe, atomic where it matters, and correct on Windows, macOS, and Linux.

# DIRECTORY STRATEGY

## Use the Right app.getPath() for the Right Data
```javascript
const { app } = require('electron');

// Use these — never hardcode paths or use process.cwd() in production
app.getPath('userData')     // /Users/alice/Library/Application Support/MyApp   (user settings, DB)
app.getPath('documents')    // /Users/alice/Documents                            (user-created files)
app.getPath('downloads')    // /Users/alice/Downloads                            (exported files)
app.getPath('desktop')      // /Users/alice/Desktop
app.getPath('home')         // /Users/alice
app.getPath('temp')         // /tmp                                              (temporary work files)
app.getPath('logs')         // /Users/alice/Library/Logs/MyApp                  (log files)
app.getPath('appData')      // /Users/alice/Library/Application Support         (app data root)
app.getPath('exe')          // path to the app executable (read-only in prod)

// Build paths safely — ALWAYS use path.join, never string concatenation
const path = require('path');
const settingsPath = path.join(app.getPath('userData'), 'settings.json');
const dbPath = path.join(app.getPath('userData'), 'data', 'app.db');
const exportPath = path.join(app.getPath('documents'), 'MyApp Exports');
```

# SAFE FILE READING

## Read JSON Config / Settings
```javascript
const fs = require('fs');
const path = require('path');

async function readJsonFile(filePath, defaultValue = null) {
  try {
    const raw = await fs.promises.readFile(filePath, 'utf8');
    return JSON.parse(raw);
  } catch (err) {
    if (err.code === 'ENOENT') {
      // File does not exist — return default, do not throw
      return defaultValue;
    }
    if (err instanceof SyntaxError) {
      console.error(`Corrupt JSON at ${filePath}:`, err.message);
      return defaultValue;
    }
    throw err;  // unexpected error — propagate
  }
}

// Usage:
const settings = await readJsonFile(settingsPath, { theme: 'dark', lang: 'en' });
```

# ATOMIC FILE WRITES (Critical for Settings/DB Files)

## Why Atomic Writes Matter
```
Problem:  app writes 10KB settings file, crashes after 5KB written
Result:   corrupt settings file — app breaks on next launch

Solution: write to temp file first, then rename over the target
          rename() is atomic on most OS — either old or new, never partial
```

## Atomic Write Pattern
```javascript
const fs = require('fs');
const path = require('path');
const os = require('os');

async function atomicWriteFile(targetPath, content) {
  // Write to temp file in same directory (same partition = rename is atomic)
  const dir = path.dirname(targetPath);
  const tmpPath = path.join(dir, `.${path.basename(targetPath)}.tmp`);

  try {
    // Ensure directory exists
    await fs.promises.mkdir(dir, { recursive: true });

    // Write to temp file
    await fs.promises.writeFile(tmpPath, content, 'utf8');

    // Sync to disk before rename (extra safety for power loss scenarios)
    const fd = await fs.promises.open(tmpPath, 'r+');
    await fd.sync();
    await fd.close();

    // Atomic rename — replaces target if it exists
    await fs.promises.rename(tmpPath, targetPath);
  } catch (err) {
    // Clean up temp file on failure
    try { await fs.promises.unlink(tmpPath); } catch {}
    throw err;
  }
}

async function writeJsonFile(filePath, data) {
  const content = JSON.stringify(data, null, 2);
  await atomicWriteFile(filePath, content);
}

// Usage:
await writeJsonFile(settingsPath, { theme: 'dark', lang: 'en', version: 2 });
```

## Write with Backup (Settings Files)
```javascript
async function writeWithBackup(filePath, data) {
  const backupPath = filePath + '.bak';

  // Rotate old file to backup before overwriting
  try {
    await fs.promises.copyFile(filePath, backupPath);
  } catch (err) {
    if (err.code !== 'ENOENT') throw err;
    // No existing file to back up — that is fine
  }

  try {
    await writeJsonFile(filePath, data);
  } catch (err) {
    // Write failed — restore from backup
    console.error('Write failed, restoring backup:', err);
    try { await fs.promises.rename(backupPath, filePath); } catch {}
    throw err;
  }
}
```

# FILE DIALOGS

## Open File Dialog
```javascript
// main.js
const { ipcMain, dialog } = require('electron');

ipcMain.handle('dialog:openFile', async (event, options = {}) => {
  const { filePaths, canceled } = await dialog.showOpenDialog({
    title: options.title ?? 'Open File',
    defaultPath: options.defaultPath ?? app.getPath('documents'),
    filters: options.filters ?? [
      { name: 'All Files', extensions: ['*'] }
    ],
    properties: ['openFile', ...(options.multiSelect ? ['multiSelections'] : [])]
  });

  return canceled ? null : (options.multiSelect ? filePaths : filePaths[0]);
});

ipcMain.handle('dialog:openDirectory', async () => {
  const { filePaths, canceled } = await dialog.showOpenDialog({
    properties: ['openDirectory', 'createDirectory']
  });
  return canceled ? null : filePaths[0];
});

ipcMain.handle('dialog:saveFile', async (event, options = {}) => {
  const { filePath, canceled } = await dialog.showSaveDialog({
    title: options.title ?? 'Save File',
    defaultPath: options.defaultPath ?? path.join(app.getPath('documents'), options.filename ?? 'export'),
    filters: options.filters ?? [{ name: 'All Files', extensions: ['*'] }]
  });
  return canceled ? null : filePath;
});
```

```javascript
// preload.js
contextBridge.exposeInMainWorld('fileSystem', {
  openFile: (options) => ipcRenderer.invoke('dialog:openFile', options),
  openDirectory: () => ipcRenderer.invoke('dialog:openDirectory'),
  saveFile: (options) => ipcRenderer.invoke('dialog:saveFile', options)
});
```

# DIRECTORY OPERATIONS
```javascript
// Create directory tree
async function ensureDir(dirPath) {
  await fs.promises.mkdir(dirPath, { recursive: true });
  // recursive: true — does not throw if directory already exists
}

// List directory contents with metadata
async function listDirectory(dirPath) {
  const entries = await fs.promises.readdir(dirPath, { withFileTypes: true });
  return Promise.all(entries.map(async entry => {
    const fullPath = path.join(dirPath, entry.name);
    const stat = await fs.promises.stat(fullPath);
    return {
      name: entry.name,
      path: fullPath,
      isDirectory: entry.isDirectory(),
      isFile: entry.isFile(),
      size: stat.size,
      modifiedAt: stat.mtime,
      createdAt: stat.birthtime
    };
  }));
}

// Recursive delete (like rm -rf)
async function removeDir(dirPath) {
  await fs.promises.rm(dirPath, { recursive: true, force: true });
  // Node 14.14+ — force: true does not throw if path does not exist
}

// Copy file, creating destination directory if needed
async function copyFileSafe(src, dest) {
  await ensureDir(path.dirname(dest));
  await fs.promises.copyFile(src, dest);
}
```

# FILE WATCHING WITH CHOKIDAR

## Watch for Changes
```javascript
// npm install chokidar
const chokidar = require('chokidar');

class FileWatcher {
  constructor() {
    this.watchers = new Map();
  }

  watch(targetPath, callbacks = {}) {
    if (this.watchers.has(targetPath)) return;

    const watcher = chokidar.watch(targetPath, {
      persistent: true,
      ignoreInitial: true,          // do not fire for existing files on start
      awaitWriteFinish: {
        stabilityThreshold: 500,    // wait 500ms after last write event
        pollInterval: 100
      },
      ignored: [
        /(^|[\/\\])\../,            // hidden files/directories
        '**/node_modules/**',
        '**/*.tmp'
      ]
    });

    if (callbacks.onChange) watcher.on('change', callbacks.onChange);
    if (callbacks.onAdd)    watcher.on('add',    callbacks.onAdd);
    if (callbacks.onDelete) watcher.on('unlink', callbacks.onDelete);
    watcher.on('error', err => console.error('File watcher error:', err));

    this.watchers.set(targetPath, watcher);
    return watcher;
  }

  unwatch(targetPath) {
    const watcher = this.watchers.get(targetPath);
    if (watcher) {
      watcher.close();
      this.watchers.delete(targetPath);
    }
  }

  unwatchAll() {
    for (const watcher of this.watchers.values()) watcher.close();
    this.watchers.clear();
  }
}

// Usage — watch settings file for external changes
const watcher = new FileWatcher();
watcher.watch(settingsPath, {
  onChange: async (filePath) => {
    const newSettings = await readJsonFile(filePath);
    mainWindow.webContents.send('settings:changed', newSettings);
  }
});

// Clean up on app quit
app.on('before-quit', () => watcher.unwatchAll());
```

# PATH SAFETY ACROSS PLATFORMS
```javascript
// ALWAYS use path.join — slash direction differs on Windows vs Unix
const filePath = path.join(baseDir, 'subdir', 'file.txt');
// Windows: C:\Users\alice\AppData\Roaming\MyApp\subdir\file.txt
// macOS:   /Users/alice/Library/Application Support/MyApp/subdir/file.txt

// Normalize paths from external sources (drag and drop, CLI args)
function normalizePath(inputPath) {
  return path.normalize(inputPath);
}

// Prevent path traversal in IPC handlers
function safePath(baseDir, userInput) {
  const resolved = path.resolve(baseDir, userInput);
  if (!resolved.startsWith(path.resolve(baseDir))) {
    throw new Error(`Path traversal attempt blocked: ${userInput}`);
  }
  return resolved;
}

// Check if path is inside allowed directory
function isPathAllowed(filePath, allowedDir) {
  const resolvedFile = path.resolve(filePath);
  const resolvedAllowed = path.resolve(allowedDir);
  return resolvedFile.startsWith(resolvedAllowed + path.sep) ||
         resolvedFile === resolvedAllowed;
}
```

# LARGE FILE OPERATIONS

## Stream Large Files (Do Not Load Into Memory)
```javascript
const { pipeline } = require('stream/promises');
const zlib = require('zlib');

// Read large file as stream
async function processLargeFile(filePath, processLine) {
  const { createInterface } = require('readline');
  const stream = fs.createReadStream(filePath, { encoding: 'utf8' });
  const rl = createInterface({ input: stream, crlfDelay: Infinity });

  for await (const line of rl) {
    await processLine(line);
  }
}

// Copy large file with progress
async function copyWithProgress(src, dest, onProgress) {
  const { size } = await fs.promises.stat(src);
  let transferred = 0;

  const readStream = fs.createReadStream(src);
  const writeStream = fs.createWriteStream(dest);

  readStream.on('data', chunk => {
    transferred += chunk.length;
    onProgress({ transferred, total: size, pct: Math.round(transferred / size * 100) });
  });

  await pipeline(readStream, writeStream);
}

// Compress file
async function compressFile(srcPath, destPath) {
  await pipeline(
    fs.createReadStream(srcPath),
    zlib.createGzip(),
    fs.createWriteStream(destPath)
  );
}
```

# CHECKLIST
```
[ ] Use app.getPath() for all app directories — never hardcode OS paths
[ ] path.join() for ALL path construction — never string concatenation
[ ] Atomic writes for any file that must not be left in partial state
[ ] Read errors handled: ENOENT (no file) and SyntaxError (corrupt) both caught
[ ] Directory created before writing (mkdir recursive)
[ ] Path traversal prevented in any IPC handler accepting file paths
[ ] File dialogs used for user-chosen paths — never accept arbitrary paths from renderer
[ ] Chokidar watchers closed on app quit — prevent orphaned processes
[ ] Large files streamed, not fully loaded into memory
[ ] Temp files cleaned up on write failure