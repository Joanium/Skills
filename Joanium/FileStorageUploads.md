---
name: File Storage & Uploads
trigger: file upload, S3, multipart upload, presigned URL, file storage, cloud storage, multer, image upload, video upload, file validation, storage bucket, stream upload, chunked upload, signed URL, GCS, Azure Blob
description: Handle file uploads and cloud storage end-to-end. Covers multipart uploads with Multer, AWS S3 (presigned URLs, streaming), image validation and processing, CDN setup, and secure file access patterns.
---

# ROLE
You are a backend engineer specializing in file handling. Your job is to build file upload systems that are secure, scalable, and fast. Files are a common attack surface — validate everything, store nothing on your app server, and stream rather than buffer.

# CORE PRINCIPLES
```
NEVER store files on app server disk — use object storage (S3, GCS, R2)
STREAM, don't buffer — don't load entire files into memory
VALIDATE before processing — type, size, content (not just extension)
PRESIGNED URLS — let clients upload directly to S3 (bypasses your server)
SCAN untrusted files — malware, image bombs, malicious content
SEPARATE file serving from file storage — serve via CDN
```

# DIRECT UPLOAD TO S3 (Presigned URLs) — Recommended Architecture

## Flow
```
Client                  Your API              S3
  │                        │                   │
  ├─── POST /upload/init ──►│                   │
  │                        ├── createPresignedPost ──►│
  │    { url, fields } ◄───┤                   │
  │                        │                   │
  ├─── POST directly to S3 ─────────────────────►│
  │                    (file never touches API) │
  │    { key: 'uploads/...' } returned by S3   │
  │                        │                   │
  ├─── POST /upload/confirm { key } ──►│        │
  │                        ├── validate, move to final location
  │    { url: CDN url } ◄──┤
```

## Server — Generate Presigned Upload URL
```typescript
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3'
import { getSignedUrl } from '@aws-sdk/s3-request-presigner'
import { createPresignedPost } from '@aws-sdk/s3-presigned-post'
import crypto from 'crypto'

const s3 = new S3Client({ region: process.env.AWS_REGION! })
const BUCKET = process.env.S3_BUCKET!

// Option A: Presigned POST (best for browser direct upload, enforces conditions)
app.post('/upload/init', requireAuth, async (req, res) => {
  const { filename, contentType, size } = req.body

  // Validate before generating URL
  const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf']
  const MAX_SIZE = 10 * 1024 * 1024  // 10MB

  if (!ALLOWED_TYPES.includes(contentType)) {
    return res.status(400).json({ error: 'File type not allowed' })
  }
  if (size > MAX_SIZE) {
    return res.status(400).json({ error: 'File too large' })
  }

  // Generate a unique key in temporary prefix
  const ext = filename.split('.').pop()?.toLowerCase()
  const key = `uploads/temp/${req.user!.userId}/${crypto.randomUUID()}.${ext}`

  const { url, fields } = await createPresignedPost(s3, {
    Bucket: BUCKET,
    Key: key,
    Conditions: [
      ['content-length-range', 0, MAX_SIZE],
      ['eq', '$Content-Type', contentType],
    ],
    Fields: {
      'Content-Type': contentType,
      'Cache-Control': 'max-age=31536000',
    },
    Expires: 300,  // URL valid for 5 minutes
  })

  res.json({ url, fields, key })
})

// Option B: Presigned PUT (simpler, use for server-side uploads)
async function generatePresignedPut(key: string, contentType: string, ttl = 300) {
  const command = new PutObjectCommand({
    Bucket: BUCKET,
    Key: key,
    ContentType: contentType,
  })
  return getSignedUrl(s3, command, { expiresIn: ttl })
}
```

## Client — Upload Directly to S3
```typescript
async function uploadFile(file: File): Promise<string> {
  // 1. Get presigned URL from your API
  const { url, fields, key } = await fetch('/upload/init', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      filename: file.name,
      contentType: file.type,
      size: file.size,
    }),
  }).then(r => r.json())

  // 2. Upload directly to S3 using the presigned POST fields
  const formData = new FormData()
  Object.entries(fields).forEach(([k, v]) => formData.append(k, v as string))
  formData.append('file', file)   // file MUST be last field

  const uploadRes = await fetch(url, { method: 'POST', body: formData })
  if (!uploadRes.ok) throw new Error('Upload to S3 failed')

  // 3. Confirm with your API (triggers validation/processing)
  const { fileUrl } = await fetch('/upload/confirm', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ key }),
  }).then(r => r.json())

  return fileUrl
}

// With progress tracking
async function uploadWithProgress(file: File, onProgress: (pct: number) => void): Promise<string> {
  const { url, fields, key } = await initUpload(file)

  await new Promise<void>((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    const formData = new FormData()
    Object.entries(fields).forEach(([k, v]) => formData.append(k, v as string))
    formData.append('file', file)

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100))
    }
    xhr.onload = () => xhr.status < 300 ? resolve() : reject(new Error('Upload failed'))
    xhr.onerror = () => reject(new Error('Network error'))

    xhr.open('POST', url)
    xhr.send(formData)
  })

  return confirmUpload(key)
}
```

# MULTER — TRADITIONAL UPLOAD VIA YOUR SERVER

## Setup
```typescript
import multer from 'multer'
import sharp from 'sharp'

// Memory storage — for immediate processing (images)
const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 5 * 1024 * 1024,  // 5MB
    files: 5,
  },
  fileFilter(req, file, cb) {
    const ALLOWED = ['image/jpeg', 'image/png', 'image/webp']
    if (ALLOWED.includes(file.mimetype)) {
      cb(null, true)
    } else {
      cb(new Error(`File type ${file.mimetype} not allowed`))
    }
  }
})

// Disk storage — for large files (stream directly to disk)
const diskUpload = multer({
  storage: multer.diskStorage({
    destination: '/tmp/uploads',
    filename: (req, file, cb) => {
      cb(null, `${crypto.randomUUID()}-${file.originalname}`)
    }
  })
})
```

## Image Upload + Process + S3
```typescript
import { Upload } from '@aws-sdk/lib-storage'

app.post('/profile-picture', requireAuth, upload.single('image'), async (req, res) => {
  if (!req.file) return res.status(400).json({ error: 'No file uploaded' })

  const userId = req.user!.userId
  const results: Record<string, string> = {}

  // Process multiple sizes in parallel
  const sizes = [
    { name: 'thumbnail', width: 100, height: 100 },
    { name: 'small',     width: 300, height: 300 },
    { name: 'large',     width: 800, height: 800 },
  ]

  await Promise.all(sizes.map(async ({ name, width, height }) => {
    const processed = await sharp(req.file!.buffer)
      .resize(width, height, { fit: 'cover', position: 'center' })
      .webp({ quality: 80 })
      .toBuffer()

    const key = `avatars/${userId}/${name}.webp`

    await new Upload({
      client: s3,
      params: {
        Bucket: BUCKET,
        Key: key,
        Body: processed,
        ContentType: 'image/webp',
        CacheControl: 'max-age=31536000',
      }
    }).done()

    results[name] = `https://${CDN_DOMAIN}/${key}`
  }))

  await db.users.update(userId, { avatarUrls: results })

  res.json({ avatarUrls: results })
})
```

# STREAMING LARGE FILE DOWNLOADS
```typescript
import { GetObjectCommand } from '@aws-sdk/client-s3'

app.get('/files/:fileId', requireAuth, async (req, res) => {
  const file = await db.files.findById(req.params.fileId)
  if (!file || file.userId !== req.user!.userId) {
    return res.status(404).json({ error: 'File not found' })
  }

  const command = new GetObjectCommand({ Bucket: BUCKET, Key: file.s3Key })
  const s3Response = await s3.send(command)

  // Stream directly — don't buffer entire file in memory
  res.setHeader('Content-Type', file.contentType)
  res.setHeader('Content-Disposition', `attachment; filename="${file.originalName}"`)
  res.setHeader('Content-Length', s3Response.ContentLength!)

  // Pipe S3 stream to response
  const stream = s3Response.Body as NodeJS.ReadableStream
  stream.pipe(res)

  stream.on('error', (err) => {
    console.error('Stream error:', err)
    res.end()
  })
})
```

# FILE VALIDATION BEYOND MIME TYPE
```typescript
import { fileTypeFromBuffer } from 'file-type'   // reads magic bytes

async function validateFileContent(buffer: Buffer, declaredMime: string): Promise<boolean> {
  // Check actual file type from magic bytes (not just extension or Content-Type header)
  const detected = await fileTypeFromBuffer(buffer)

  if (!detected) return false  // unknown file type

  // Must match declared type
  if (detected.mime !== declaredMime) {
    console.warn(`Mismatch: declared ${declaredMime}, actual ${detected.mime}`)
    return false
  }

  // Image-specific: check for "image bomb" (tiny file that expands to huge dimensions)
  if (detected.mime.startsWith('image/')) {
    const metadata = await sharp(buffer).metadata()
    const MAX_PIXELS = 50_000_000  // 50 megapixels
    if ((metadata.width ?? 0) * (metadata.height ?? 0) > MAX_PIXELS) {
      return false
    }
  }

  return true
}
```

# SIGNED URLS FOR PRIVATE FILE ACCESS
```typescript
import { GetObjectCommand } from '@aws-sdk/client-s3'

// Generate time-limited download URL (don't expose S3 URLs directly)
async function getDownloadUrl(s3Key: string, expiresIn = 3600): Promise<string> {
  const command = new GetObjectCommand({ Bucket: BUCKET, Key: s3Key })
  return getSignedUrl(s3, command, { expiresIn })
}

// API endpoint
app.get('/files/:fileId/download-url', requireAuth, async (req, res) => {
  const file = await db.files.findById(req.params.fileId)
  if (!file || !canAccess(req.user!, file)) {
    return res.status(403).json({ error: 'Access denied' })
  }

  const url = await getDownloadUrl(file.s3Key, 300)  // 5 minute URL
  res.json({ url, expiresAt: new Date(Date.now() + 300_000).toISOString() })
})
```

# CLEANUP — DELETE ORPHANED FILES
```typescript
// S3 lifecycle policy (set in AWS console or IaC):
// - Delete objects in uploads/temp/ after 1 day
// - Move to Glacier after 90 days

// App-level cleanup for files not confirmed
async function cleanupTempUploads() {
  const cutoff = new Date(Date.now() - 24 * 60 * 60 * 1000)
  const orphaned = await db.uploads.findUnconfirmedBefore(cutoff)

  await Promise.allSettled(
    orphaned.map(async file => {
      await s3.send(new DeleteObjectCommand({ Bucket: BUCKET, Key: file.s3Key }))
      await db.uploads.delete(file.id)
    })
  )
}
```
