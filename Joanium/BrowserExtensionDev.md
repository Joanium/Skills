---
name: Browser Extension Development
trigger: browser extension, chrome extension, manifest v3, content script, background service worker, extension popup, chrome api, browser action, web extension, firefox extension, extension permissions, message passing, extension storage
description: Build Chrome/Firefox browser extensions with Manifest V3. Covers manifest setup, content scripts, background service workers, popup UI, Chrome APIs, message passing, storage, and publishing to the Chrome Web Store.
---

# ROLE
You are a senior browser extension developer. Your job is to build extensions that work reliably across tab navigations, survive service worker restarts, and don't get rejected from the store. Most extension bugs come from misunderstanding the MV3 service worker lifecycle and message passing patterns.

# CORE PRINCIPLES
```
MV3 ONLY:          Manifest V3 is required — MV2 deprecated and blocked on Chrome
SW IS EPHEMERAL:   Background service worker can stop at any time — never assume state
MINIMAL PERMS:     Request only the permissions you actually need — reviewers reject over-reach
CONTENT SCRIPT ISOLATED: CS runs in isolated world — can't access page's JS variables directly
MESSAGE PASSING:   Components communicate only via chrome.runtime.sendMessage
```

# MANIFEST V3 STRUCTURE

## manifest.json
```json
{
  "manifest_version": 3,
  "name": "My Extension",
  "version": "1.0.0",
  "description": "Does something useful on every page",
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  },

  "action": {
    "default_popup": "popup.html",
    "default_icon": "icons/icon48.png",
    "default_title": "My Extension"
  },

  "background": {
    "service_worker": "background.js",
    "type": "module"
  },

  "content_scripts": [
    {
      "matches": ["https://*/*", "http://*/*"],
      "js": ["content.js"],
      "css": ["content.css"],
      "run_at": "document_idle"
    }
  ],

  "permissions": [
    "storage",
    "activeTab",
    "scripting"
  ],

  "host_permissions": [
    "https://api.example.com/*"
  ],

  "options_page": "options.html",

  "web_accessible_resources": [
    {
      "resources": ["images/*.png", "fonts/*.woff2"],
      "matches": ["https://*/*"]
    }
  ]
}
```

# BACKGROUND SERVICE WORKER

## background.js — Key Patterns
```javascript
// Service worker restarts when idle — don't store state in module-level variables
// Use chrome.storage for persistence

// Install / Update handler
chrome.runtime.onInstalled.addListener(async ({ reason }) => {
  if (reason === 'install') {
    await chrome.storage.local.set({ enabled: true, settings: {} });
    chrome.tabs.create({ url: 'onboarding.html' });
  }
  if (reason === 'update') {
    // Run migrations
    await migrateStorage();
  }
});

// Message handler — main communication hub
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // MUST return true if response is async
  if (message.type === 'GET_SETTINGS') {
    chrome.storage.local.get('settings').then(({ settings }) => {
      sendResponse({ settings });
    });
    return true;  // ← critical: keeps message channel open for async response
  }

  if (message.type === 'ANALYZE_PAGE') {
    analyzePageContent(message.content).then(result => sendResponse({ result }));
    return true;
  }
});

// Context menu integration
chrome.contextMenus.create({
  id: 'my-action',
  title: 'Do something with "%s"',  // %s = selected text
  contexts: ['selection'],
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'my-action') {
    chrome.tabs.sendMessage(tab.id, {
      type: 'CONTEXT_MENU_ACTION',
      text: info.selectionText,
    });
  }
});

// Tab events
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url?.startsWith('https://')) {
    chrome.action.setBadgeText({ text: '✓', tabId });
  }
});
```

## Keeping Service Worker Alive (Workaround)
```javascript
// MV3 service workers sleep after 30s idle
// For persistent connections (WebSocket, etc.) use chrome.alarms

chrome.alarms.create('keepalive', { periodInMinutes: 0.4 });  // every 25s

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'keepalive') {
    // Touch storage to reset idle timer
    chrome.storage.session.set({ lastPing: Date.now() });
  }
});
```

# CONTENT SCRIPTS

## content.js — Page Interaction
```javascript
// Content scripts run in an ISOLATED world
// They can: read/modify DOM, listen to DOM events, send messages to background
// They CANNOT: access page's window/JS variables, use most Chrome APIs

// DOM manipulation
function injectUI() {
  const container = document.createElement('div');
  container.id = 'my-extension-container';
  container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 999999;';
  
  // Use web accessible resource for the iframe
  const iframe = document.createElement('iframe');
  iframe.src = chrome.runtime.getURL('sidebar.html');
  iframe.style.cssText = 'width: 320px; height: 480px; border: none;';
  
  container.appendChild(iframe);
  document.body.appendChild(container);
}

// Message passing to background
async function sendToBackground(message) {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(message, (response) => {
      if (chrome.runtime.lastError) reject(chrome.runtime.lastError);
      else resolve(response);
    });
  });
}

// Listen for messages from background or popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'GET_PAGE_CONTENT') {
    sendResponse({
      title: document.title,
      url: location.href,
      text: document.body.innerText.slice(0, 10000),  // limit size
    });
  }
});

// Observe page changes (SPA-friendly)
const observer = new MutationObserver((mutations) => {
  // Handle dynamic content changes
});
observer.observe(document.body, { childList: true, subtree: true });

// Initialize
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', injectUI);
} else {
  injectUI();
}
```

# POPUP UI

## popup.html
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body { width: 320px; min-height: 200px; margin: 0; font-family: system-ui; }
  </style>
</head>
<body>
  <div id="app"></div>
  <script src="popup.js" type="module"></script>
</body>
</html>
```

## popup.js
```javascript
// Popup loses state when closed — restore from storage
document.addEventListener('DOMContentLoaded', async () => {
  const { settings, enabled } = await chrome.storage.local.get(['settings', 'enabled']);
  renderUI({ settings, enabled });

  // Get current tab info
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
  // Query content script on current page
  try {
    const response = await chrome.tabs.sendMessage(tab.id, { type: 'GET_PAGE_CONTENT' });
    displayPageInfo(response);
  } catch {
    displayError('Extension not active on this page');
  }
});

// programmatic script injection (requires activeTab permission)
async function runOnPage() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => {
      // This function runs in the page context
      return document.title;
    },
  });
}
```

# STORAGE PATTERNS
```javascript
// chrome.storage.local — up to 10MB, persists across sessions
await chrome.storage.local.set({ key: value });
const result = await chrome.storage.local.get('key');  // { key: value }
const multi = await chrome.storage.local.get(['key1', 'key2']);

// chrome.storage.sync — syncs across devices, 100KB limit
await chrome.storage.sync.set({ preferences: { theme: 'dark' } });

// chrome.storage.session — session only, cleared on browser restart
// Fastest, good for runtime state

// Listen for changes
chrome.storage.onChanged.addListener((changes, areaName) => {
  if (areaName === 'local' && changes.enabled) {
    console.log('Enabled changed:', changes.enabled.newValue);
  }
});
```

# PERMISSIONS GUIDE
```
Minimal permissions strategy:
  "activeTab"    → access current tab only when user clicks extension (preferred over "tabs")
  "storage"      → read/write extension storage
  "scripting"    → programmatically inject scripts (MV3 replacement for executeScript)
  "contextMenus" → add right-click menu items
  "alarms"       → scheduled tasks

Avoid these unless essential (triggers store review):
  "tabs"         → access all tab URLs/titles (privacy concern)
  "history"      → read browsing history
  "bookmarks"    → access bookmarks
  "<all_urls>"   → matches all URLs (better to use "activeTab")
  "webRequest"   → intercept network requests (very restricted in MV3)
```

# CHROME WEB STORE PUBLISHING
```
Preparation:
  1. Create a ZIP of your extension (not the parent folder)
  2. Test in Chrome: chrome://extensions → Load unpacked
  3. Screenshots: 1280×800 or 640×400 (at least 1 required)
  4. Privacy policy URL (required if you collect any data)

Publishing steps:
  1. Pay $5 one-time developer registration fee
  2. Go to: https://chrome.google.com/webstore/devconsole
  3. New item → upload ZIP
  4. Fill: description, category, screenshots
  5. Submit for review (1-3 business days)

Common rejection reasons:
  - Permissions not justified in description
  - Remote code execution (no eval, no remote scripts)
  - Missing privacy policy for data collection
  - Misleading description or screenshots
  - Unused permissions declared
```

# DEBUGGING
```
Background service worker:
  chrome://extensions → "Inspect views: service worker"

Content scripts:
  DevTools on the page → Console (select content script context from dropdown)

Popup:
  Right-click extension icon → "Inspect Popup"

Check errors:
  chrome://extensions → click "Errors" button on your extension card

Log from background to see in SW console:
  console.log('[BG]', message);
```
