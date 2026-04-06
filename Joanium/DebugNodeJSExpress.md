---
name: Debug — Node.js / Express
trigger: node error, express bug, express not working, middleware not running, route not found, 404 express, 500 express, req.body undefined, cors error, express error handler, node crash, event loop, node memory leak, node slow
description: Hyper-specific debugging guide for Node.js and Express. Real errors, real causes, real fixes. Covers middleware order, request parsing, CORS, error handling, event loop blocking, memory leaks, and cluster issues.
---

# Debug — Node.js / Express

## First Move

```bash
# Run with full stack traces
NODE_ENV=development node --stack-trace-limit=30 app.js

# Run with Node.js inspector (Chrome DevTools debugger)
node --inspect app.js
# Open chrome://inspect → click your target

# Nodemon with debugging
nodemon --inspect app.js

# Check what's actually running (port conflicts)
lsof -i :3000  # what's on port 3000?
kill -9 $(lsof -ti:3000)  # kill it

# Check Node version
node -v
cat .nvmrc 2>/dev/null

# Memory and CPU at a glance
node -e "const os=require('os'); console.log({freeMem: os.freemem()/1e6+'MB', cpus: os.cpus().length})"
```

---

## Middleware Order (Express #1 bug source)

Express executes middleware in **registration order**. Order is everything.

```javascript
// WRONG: body parser registered AFTER routes — req.body is always undefined
app.get('/api/data', (req, res) => {
  console.log(req.body)  // undefined!
  res.json(req.body)
})
app.use(express.json())  // too late

// CORRECT: global middleware BEFORE routes
app.use(express.json())           // parse JSON bodies
app.use(express.urlencoded({ extended: true }))  // parse form bodies
app.use(cors())                   // CORS headers
app.use(cookieParser())           // cookie parsing
app.use(helmet())                 // security headers
// THEN register routes:
app.use('/api', apiRouter)
app.use('/auth', authRouter)
// THEN error handler (must be last, must have 4 params):
app.use((err, req, res, next) => {
  console.error(err.stack)
  res.status(err.status || 500).json({ error: err.message })
})
```

---

## `req.body` is `undefined`

```javascript
// Check 1: Is body-parser / express.json() registered BEFORE this route?
app.use(express.json())  // must come first

// Check 2: Is the Content-Type header correct?
// Request must have: Content-Type: application/json
// Debug:
app.use((req, res, next) => {
  console.log('Content-Type:', req.headers['content-type'])
  next()
})

// Check 3: Payload size limit — default is 100kb
app.use(express.json({ limit: '10mb' }))

// Check 4: Are you using a router with its own middleware?
const router = express.Router()
// Middleware on app doesn't automatically apply to router — add it:
router.use(express.json())
// Or mount router after global middleware so it inherits it:
app.use(express.json())
app.use('/api', router)  // router inherits app middleware
```

---

## CORS Errors

```javascript
// Browser console shows:
// Access to fetch at 'X' from origin 'Y' has been blocked by CORS policy

// Fix: configure cors middleware properly
const cors = require('cors')

// Allow specific origin
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:3000',
  credentials: true,  // required if sending cookies
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}))

// Dynamic origin (multiple allowed origins)
const allowedOrigins = ['https://app.example.com', 'https://admin.example.com']
app.use(cors({
  origin: (origin, callback) => {
    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true)
    } else {
      callback(new Error(`CORS blocked: ${origin}`))
    }
  },
  credentials: true
}))

// Preflight OPTIONS must be handled — cors() does this automatically
// But if you have auth middleware that runs before CORS:
app.options('*', cors())  // handle preflight before auth middleware
app.use(authMiddleware)

// Debug: log CORS headers being sent
app.use((req, res, next) => {
  console.log('origin:', req.headers.origin)
  console.log('method:', req.method)
  next()
})
```

---

## Route Not Found / 404

```javascript
// Debug: log every incoming request to see what's actually hitting the server
app.use((req, res, next) => {
  console.log(`${req.method} ${req.path}`)  // use req.path not req.url (excludes query string)
  next()
})

// Common cause 1: router mounted at wrong path
app.use('/api/v1', userRouter)
// Route inside: router.get('/users', ...)
// Correct URL: GET /api/v1/users
// Wrong URL:   GET /api/users  ← 404

// Common cause 2: route defined after a catch-all
app.get('*', (req, res) => res.send('404'))  // catches everything!
app.get('/api/users', handler)  // never reached!
// Fix: specific routes BEFORE catch-all

// Common cause 3: HTTP method mismatch
app.post('/api/login', handler)  // POST only
// Calling with GET → 404 (or 405 if you handle it)

// Add a catch-all 404 handler at the very end
app.use((req, res) => {
  res.status(404).json({
    error: 'Not found',
    method: req.method,
    path: req.path
  })
})
```

---

## Error Handling in Express

```javascript
// Express error handler: MUST have 4 parameters — (err, req, res, next)
// Even if you don't use next — the signature is how Express identifies it

// WRONG: missing next param
app.use((err, req, res) => {
  res.status(500).send(err.message)  // Express won't call this
})

// CORRECT:
app.use((err, req, res, next) => {
  console.error('Unhandled error:', err)
  res.status(err.statusCode || 500).json({
    error: process.env.NODE_ENV === 'production' ? 'Internal server error' : err.message,
    ...(process.env.NODE_ENV !== 'production' && { stack: err.stack })
  })
})

// Async route handlers — errors NOT automatically forwarded to error handler
// WRONG: thrown errors in async routes are unhandled
app.get('/users', async (req, res) => {
  const users = await db.getUsers()  // if this throws, Express doesn't catch it
  res.json(users)
})

// FIX 1: try/catch with next(err)
app.get('/users', async (req, res, next) => {
  try {
    const users = await db.getUsers()
    res.json(users)
  } catch (err) {
    next(err)  // forwards to error handler
  }
})

// FIX 2: wrapper utility (cleaner)
const asyncHandler = fn => (req, res, next) =>
  Promise.resolve(fn(req, res, next)).catch(next)

app.get('/users', asyncHandler(async (req, res) => {
  const users = await db.getUsers()
  res.json(users)
}))

// FIX 3: express-async-errors package (simplest — wraps all async routes automatically)
require('express-async-errors')
// Now thrown errors in async routes automatically go to error handler
```

---

## Event Loop Blocking

```javascript
// Symptom: server hangs, high latency, requests timeout
// Node.js is single-threaded — one blocking call freezes EVERYTHING

// Find the blocker — profile the event loop
const { monitorEventLoopDelay } = require('perf_hooks')
const h = monitorEventLoopDelay({ resolution: 20 })
h.enable()
setInterval(() => {
  console.log('event loop delay:', h.mean / 1e6, 'ms')
  h.reset()
}, 5000)

// Common blockers and fixes:

// 1. Synchronous file operations
const data = fs.readFileSync('file.txt')  // BLOCKS
const data = await fs.promises.readFile('file.txt')  // OK

// 2. JSON.parse/stringify on huge payloads — blocks proportionally to size
// Fix: stream large JSON, or process in chunks, or use a worker thread

// 3. Crypto operations
const hash = crypto.createHash('sha256').update(largeData).digest()  // blocks
// Fix: use worker_threads for CPU-heavy work
const { Worker } = require('worker_threads')

// 4. bcrypt — computationally heavy by design
// Use bcrypt.hash() async form, never bcrypt.hashSync()
const hash = await bcrypt.hash(password, 12)  // async OK
const hash = bcrypt.hashSync(password, 12)    // BLOCKS

// 5. Complex regex on user input — ReDoS vulnerability + blocking
// Avoid exponential regex patterns on untrusted input
```

---

## Memory Leaks

```javascript
// Detect: watch memory over time
setInterval(() => {
  const used = process.memoryUsage()
  console.log({
    heapUsed: Math.round(used.heapUsed / 1e6) + 'MB',
    heapTotal: Math.round(used.heapTotal / 1e6) + 'MB',
    rss: Math.round(used.rss / 1e6) + 'MB'
  })
}, 10000)

// Profile with Chrome DevTools:
node --inspect app.js
// Chrome DevTools → Memory → Take heap snapshot
// Compare snapshots before/after suspected leak area

// Common leak sources:

// 1. Event listeners never removed
emitter.on('data', handler)  // added on every request
// Fix: emitter.removeListener('data', handler) or emitter.once()

// 2. Global caches that grow forever
const cache = {}
// Every unique key gets added and never removed
cache[userId] = userData  // grows unbounded
// Fix: use a proper TTL cache
const LRU = require('lru-cache')
const cache = new LRU({ max: 500, ttl: 1000 * 60 * 5 })

// 3. Closures capturing large data
function createHandler(largeData) {
  return function handler(req, res) {
    // handler holds reference to largeData — never GC'd while handler lives
    res.json({ result: processSmall(largeData) })
  }
}
// Fix: extract only what you need
function createHandler(smallExtract) {
  return function handler(req, res) {
    res.json({ result: smallExtract })
  }
}

// 4. Unresolved Promises keeping request objects alive
// Fix: ensure every async path resolves or rejects
```

---

## Common Errors

```javascript
// EADDRINUSE — port already in use
// Error: listen EADDRINUSE :::3000
lsof -ti:3000 | xargs kill -9  // kill whatever is on that port

// ECONNREFUSED — connecting to something not running
// Check if the target service (DB, Redis, etc.) is actually running
// Check the port and host are correct

// ETIMEDOUT — connection timed out
// Firewall, wrong host, service down, or no timeout set

// UnhandledPromiseRejectionWarning (Node < 15) / crash (Node 15+)
// You have a Promise that rejected with no .catch() or try/catch
// Find it: add global handler during debugging
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled rejection:', reason)
  console.error('At promise:', promise)
})

// Cannot set headers after they are sent to the client
// You called res.json() or res.send() twice — add return statements
app.get('/route', (req, res) => {
  if (!valid) {
    res.status(400).json({ error: 'bad' })
    return  // ← must return here!
  }
  res.json({ ok: true })
})
```
