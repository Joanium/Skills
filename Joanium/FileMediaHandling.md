---
name: File & Media Handling
trigger: file upload, video upload, image upload, S3, presigned URL, multipart upload, video streaming, HLS, transcoding, CDN, media processing, FFmpeg, thumbnail generation, object storage
description: Eighth skill in the build pipeline. Covers secure file uploads (direct-to-S3 with presigned URLs), video transcoding pipeline, HLS streaming, image optimization, thumbnail generation, and CDN integration.
prev_skill: 07-AuthSecurity.md
next_skill: 09-TestingStrategy.md
---

# ROLE
You are a media systems engineer. You know that file uploads are where most apps fail — blocking the server, storing in the wrong place, skipping validation, or creating security vulnerabilities. You build upload pipelines that are fast, safe, and scalable from day one.

# CORE PRINCIPLES
```
NEVER STORE FILES IN YOUR DATABASE — use object storage (S3, R2, GCS)
NEVER UPLOAD THROUGH YOUR APP SERVER — use presigned URLs for direct client-to-S3 upload
VALIDATE FILE TYPE SERVER-SIDE — MIME type from header can be spoofed; check magic bytes
PROCESS ASYNCHRONOUSLY — transcoding takes minutes; don't block the request
SERVE THROUGH CDN — never serve video/image bytes from your app server
STORE ORIGINAL, SERVE DERIVATIVES — keep the raw file, serve processed versions
```

# STEP 1 — UPLOAD ARCHITECTURE

```
WRONG (server as intermediary — blocks, doesn't scale):
  Client → POST /upload with file → App Server → S3
  Problems: Server memory exhausted, request timeout, 10GB video kills your server

RIGHT (presigned URL — direct to S3):
  1. Client → POST /upload/presigned { filename, size, content_type }
  2. Server → validates request, generates S3 presigned PUT URL (expires in 1hr)
  3. Server → returns { upload_url, storage_key }
  4. Client → PUT file directly to S3 using upload_url (no server involved)
  5. Client → notifies server when done: PATCH /videos/:id { storage_key }
  6. Server → enqueues transcoding job
  7. Worker → downloads from S3, transcodes, uploads output back to S3
  8. Worker → updates video status to 'ready', notifies client via WebSocket or polling
```

# STEP 2 — PRESIGNED URL IMPLEMENTATION

```typescript
// lib/storage.ts
import { S3Client, PutObjectCommand, GetObjectCommand, DeleteObjectCommand } from '@aws-sdk/client-s3'
import { getSignedUrl } from '@aws-sdk/s3-request-presigner'
import { env } from '@/config/env'

const s3 = new S3Client({
  region: env.S3_REGION,
  credentials: {
    accessKeyId: env.AWS_ACCESS_KEY,
    secretAccessKey: env.AWS_SECRET_KEY,
  }
})

const ALLOWED_VIDEO_TYPES = new Set(['video/mp4', 'video/webm', 'video/quicktime', 'video/x-msvideo'])
const ALLOWED_IMAGE_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp', 'image/gif'])
const MAX_VIDEO_SIZE = 10 * 1024 * 1024 * 1024  // 10GB
const MAX_IMAGE_SIZE = 10 * 1024 * 1024          // 10MB

export async function generateUploadUrl(opts: {
  userId: string
  filename: string
  contentType: string
  sizeBytes: number
  type: 'video' | 'image' | 'avatar'
}): Promise<{ uploadUrl: string; storageKey: string }> {
  // Validate content type (don't trust client, but use as initial filter)
  const allowed = opts.type === 'video' ? ALLOWED_VIDEO_TYPES : ALLOWED_IMAGE_TYPES
  if (!allowed.has(opts.contentType)) {
    throw new ValidationError([{ field: 'content_type', message: 'File type not allowed' }])
  }

  // Validate size
  const maxSize = opts.type === 'video' ? MAX_VIDEO_SIZE : MAX_IMAGE_SIZE
  if (opts.sizeBytes > maxSize) {
    throw new ValidationError([{ field: 'size_bytes', message: 'File too large' }])
  }

  // Generate unique, non-guessable storage key
  const ext = opts.filename.split('.').pop()?.toLowerCase() ?? 'bin'
  const storageKey = `${opts.type}s/${opts.userId}/${crypto.randomUUID()}.${ext}`

  const command = new PutObjectCommand({
    Bucket:        env.S3_BUCKET,
    Key:           storageKey,
    ContentType:   opts.contentType,
    ContentLength: opts.sizeBytes,
    // IMPORTANT: restrict what can be uploaded with this URL
    Metadata: {
      'uploaded-by': opts.userId,
      'upload-type':  opts.type,
    },
  })

  const uploadUrl = await getSignedUrl(s3, command, { expiresIn: 3600 })  // 1 hour

  return { uploadUrl, storageKey }
}

// Generate signed URL for private files (non-public content)
export async function generateDownloadUrl(storageKey: string, expiresIn = 3600): Promise<string> {
  const command = new GetObjectCommand({ Bucket: env.S3_BUCKET, Key: storageKey })
  return getSignedUrl(s3, command, { expiresIn })
}

// Delete a file
export async function deleteFile(storageKey: string): Promise<void> {
  await s3.send(new DeleteObjectCommand({ Bucket: env.S3_BUCKET, Key: storageKey }))
}
```

# STEP 3 — FILE TYPE VALIDATION (MAGIC BYTES)

```typescript
// Server-side validation AFTER upload — check actual file content, not extension/MIME
// Run this in the transcoding worker before processing

import { fileTypeFromBuffer } from 'file-type'  // npm i file-type

export async function validateFileType(storageKey: string, expectedType: 'video' | 'image') {
  // Download just the first 4KB (enough for magic bytes)
  const response = await s3.send(new GetObjectCommand({
    Bucket: env.S3_BUCKET,
    Key: storageKey,
    Range: 'bytes=0-4096',
  }))

  const buffer = Buffer.from(await response.Body!.transformToByteArray())
  const type = await fileTypeFromBuffer(buffer)

  if (!type) throw new Error('Could not determine file type')

  const VALID_VIDEO_MIMES = ['video/mp4', 'video/webm', 'video/quicktime']
  const VALID_IMAGE_MIMES = ['image/jpeg', 'image/png', 'image/webp']

  const allowed = expectedType === 'video' ? VALID_VIDEO_MIMES : VALID_IMAGE_MIMES
  if (!allowed.includes(type.mime)) {
    await deleteFile(storageKey)  // remove the malicious file
    throw new Error(`Invalid file type: ${type.mime}`)
  }
}
```

# STEP 4 — VIDEO TRANSCODING PIPELINE

```typescript
// jobs/transcode.job.ts
import { Queue, Worker } from 'bullmq'
import ffmpeg from 'fluent-ffmpeg'
import { env } from '@/config/env'

export const transcodeQueue = new Queue('transcode', {
  connection: { url: env.REDIS_URL },
  defaultJobOptions: {
    attempts: 3,
    backoff: { type: 'exponential', delay: 30_000 },  // retry after 30s, 60s, 120s
  }
})

new Worker('transcode', async (job) => {
  const { videoId, storageKey } = job.data
  const tmpDir = `/tmp/transcode-${videoId}`

  try {
    // 1. Update video status to 'processing'
    await videoRepo.update(videoId, { status: 'processing' })
    await job.updateProgress(10)

    // 2. Validate file type (magic bytes)
    await validateFileType(storageKey, 'video')
    await job.updateProgress(20)

    // 3. Download original from S3 to tmp
    await downloadFromS3(storageKey, `${tmpDir}/original.mp4`)
    await job.updateProgress(35)

    // 4. Generate thumbnail at 5s mark
    await generateThumbnail(`${tmpDir}/original.mp4`, `${tmpDir}/thumbnail.jpg`)
    await job.updateProgress(45)

    // 5. Transcode to multiple resolutions (HLS)
    await transcodeToHLS(`${tmpDir}/original.mp4`, tmpDir)
    await job.updateProgress(80)

    // 6. Upload all output files to S3
    const hlsKey = await uploadHLSToS3(tmpDir, videoId)
    const thumbnailKey = await uploadFileToS3(`${tmpDir}/thumbnail.jpg`, `thumbnails/${videoId}.jpg`)
    await job.updateProgress(95)

    // 7. Update video record
    await videoRepo.update(videoId, {
      status: 'ready',
      hls_storage_key: hlsKey,
      thumbnail_url: `${env.CDN_URL}/${thumbnailKey}`,
      duration_secs: await getVideoDuration(`${tmpDir}/original.mp4`),
    })

    // 8. Notify user via WebSocket / notification
    await notificationService.send(video.owner_id, 'video_ready', { videoId })
    await job.updateProgress(100)

  } catch (err) {
    await videoRepo.update(videoId, { status: 'failed' })
    throw err  // BullMQ will retry
  } finally {
    await fs.rm(tmpDir, { recursive: true, force: true })  // cleanup tmp
  }
}, {
  connection: { url: env.REDIS_URL },
  concurrency: 2,  // max 2 videos transcoding simultaneously (CPU bound)
})

// FFmpeg transcoding to HLS (adaptive bitrate streaming)
function transcodeToHLS(inputPath: string, outputDir: string): Promise<void> {
  return new Promise((resolve, reject) => {
    ffmpeg(inputPath)
      .addOptions([
        '-profile:v baseline',
        '-level 3.0',
        '-start_number 0',
        '-hls_time 10',           // 10-second segments
        '-hls_list_size 0',       // all segments in playlist
        '-f hls',
        // Multiple quality renditions:
        '-filter_complex [0:v]split=3[v1][v2][v3]',
        '-map [v3] -s:v:0 1920x1080 -b:v:0 5000k',  // 1080p
        '-map [v2] -s:v:1 1280x720  -b:v:1 2500k',  // 720p
        '-map [v1] -s:v:2 854x480   -b:v:2 1000k',  // 480p
        '-map a:0 -map a:0 -map a:0',               // audio for each
      ])
      .output(`${outputDir}/master.m3u8`)
      .on('end', resolve)
      .on('error', reject)
      .run()
  })
}
```

# STEP 5 — IMAGE HANDLING AND OPTIMIZATION

```typescript
import sharp from 'sharp'

// RESIZE AND OPTIMIZE IMAGES (profile pictures, thumbnails):
export async function processImage(
  inputBuffer: Buffer,
  opts: { width: number; height: number; quality?: number }
): Promise<Buffer> {
  return sharp(inputBuffer)
    .resize(opts.width, opts.height, {
      fit: 'cover',        // crop to exact dimensions
      position: 'center',
    })
    .webp({ quality: opts.quality ?? 80 })  // convert all images to WebP
    .toBuffer()
}

// AVATAR PROCESSING PIPELINE:
export async function processAvatar(storageKey: string, userId: string) {
  const original = await downloadFromS3(storageKey)
  
  const [small, medium, large] = await Promise.all([
    processImage(original, { width: 48,  height: 48 }),   // 48×48 for comments
    processImage(original, { width: 96,  height: 96 }),   // 96×96 for profile
    processImage(original, { width: 192, height: 192 }),  // 192×192 retina
  ])

  const [smallKey, mediumKey, largeKey] = await Promise.all([
    uploadBuffer(small,  `avatars/${userId}/48.webp`),
    uploadBuffer(medium, `avatars/${userId}/96.webp`),
    uploadBuffer(large,  `avatars/${userId}/192.webp`),
  ])

  return { smallKey, mediumKey, largeKey }
}
```

# STEP 6 — CDN AND STREAMING CONFIGURATION

```
CDN SETUP (CloudFront or Cloudflare):
  - Point CDN to your S3 bucket
  - Public content (thumbnails, public videos): serve via CDN, no signed URLs needed
  - Private content: require signed CDN URLs (CloudFront signed cookies)

S3 BUCKET POLICY (least privilege):
  - ONE bucket for uploads (private by default)
  - ONE bucket for served content (public-read for processed outputs)
  - Separate IAM roles for app (upload permission only) vs CDN (download only)

VIDEO STREAMING URLS:
  Public video:  https://cdn.yourapp.com/videos/{videoId}/master.m3u8
  Private video: CloudFront signed URL with 4-hour expiry

RANGE REQUEST SUPPORT (for video seeking):
  - S3 supports Range requests natively
  - HLS player (hls.js) automatically handles segment fetching
  - Ensure your CDN forwards Range headers to origin

HLS.JS INTEGRATION (frontend):
  import Hls from 'hls.js'

  if (Hls.isSupported()) {
    const hls = new Hls()
    hls.loadSource(video.hls_url)
    hls.attachMedia(videoElement)
    hls.on(Hls.Events.MANIFEST_PARSED, () => videoElement.play())
  } else if (videoElement.canPlayType('application/vnd.apple.mpegurl')) {
    // Safari has native HLS support
    videoElement.src = video.hls_url
  }

MULTIPART UPLOAD (for large files > 100MB):
  - Use AWS S3 multipart upload for files over 100MB
  - Client splits file into 10MB chunks, uploads in parallel
  - S3 assembles the parts server-side
  - Presigned URLs work for each part
  - Use the @aws-sdk/client-s3 createMultipartUpload + UploadPart + CompleteMultipartUpload
```

# CHECKLIST — Before Moving to Testing

```
✅ Presigned URL upload flow implemented (no files going through app server)
✅ File type validation with magic bytes (not just extension or MIME header)
✅ File size limits enforced server-side
✅ Transcoding job enqueued after upload notification
✅ FFmpeg transcoding to HLS with multiple quality renditions
✅ Thumbnail generation included in transcode pipeline
✅ Failed transcodes update video status and notify user
✅ CDN configured for serving media (not serving from app server)
✅ Tmp files cleaned up after processing
✅ Sharp for image resizing and WebP conversion
→ NEXT: 09-TestingStrategy.md
```
