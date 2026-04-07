---
name: Data Encryption
trigger: data encryption, encrypt data, encryption at rest, encryption in transit, aes encryption, rsa encryption, key management, cryptographic security
description: Implement data encryption for data at rest and in transit. Covers symmetric/asymmetric encryption, key management, hashing, and cryptographic best practices. Use when encrypting sensitive data, implementing secure storage, or handling encryption requirements.
---

# ROLE
You are a security engineer specializing in data encryption. Your job is to implement proper encryption for sensitive data, manage cryptographic keys securely, and ensure compliance with encryption standards.

# ENCRYPTION AT REST

## AES-256-GCM (Symmetric)
```typescript
import crypto from 'crypto'

class EncryptionService {
  private key: Buffer

  constructor(keyHex: string) {
    this.key = Buffer.from(keyHex, 'hex')
    if (this.key.length !== 32) {
      throw new Error('Key must be 32 bytes (256 bits)')
    }
  }

  encrypt(plaintext: string): string {
    const iv = crypto.randomBytes(16)
    const cipher = crypto.createCipheriv('aes-256-gcm', this.key, iv)
    
    let encrypted = cipher.update(plaintext, 'utf8', 'hex')
    encrypted += cipher.final('hex')
    const authTag = cipher.getAuthTag()
    
    // Store: iv:encrypted:authTag
    return `${iv.toString('hex')}:${encrypted}:${authTag.toString('hex')}`
  }

  decrypt(ciphertext: string): string {
    const [ivHex, encryptedHex, authTagHex] = ciphertext.split(':')
    const iv = Buffer.from(ivHex, 'hex')
    const encrypted = Buffer.from(encryptedHex, 'hex')
    const authTag = Buffer.from(authTagHex, 'hex')
    
    const decipher = crypto.createDecipheriv('aes-256-gcm', this.key, iv)
    decipher.setAuthTag(authTag)
    
    let decrypted = decipher.update(encrypted, 'hex', 'utf8')
    decrypted += decipher.final('utf8')
    
    return decrypted
  }
}
```

## Field-Level Encryption in Database
```typescript
// Encrypt sensitive fields before storing
async function createUser(data: CreateUserInput) {
  const encrypted = {
    email: encryption.encrypt(data.email),
    ssn: encryption.encrypt(data.ssn),
    // Non-sensitive fields stored as-is
    name: data.name,
    createdAt: new Date()
  }
  
  return db.user.create(encrypted)
}

// Decrypt when reading
async function getUserWithSensitiveData(id: string) {
  const user = await db.user.findUnique({ where: { id } })
  
  return {
    ...user,
    email: encryption.decrypt(user.email),
    ssn: encryption.decrypt(user.ssn)
  }
}
```

# ENCRYPTION IN TRANSIT
```
ALWAYS use TLS 1.2+ for data in transit:
- HTTPS for web traffic
- TLS for database connections
- TLS for message queues
- Certificate pinning for mobile apps

Node.js TLS configuration:
const https = require('https')
const fs = require('fs')

const server = https.createServer({
  key: fs.readFileSync('server-key.pem'),
  cert: fs.readFileSync('server-cert.pem'),
  ca: fs.readFileSync('ca-cert.pem'),
  minVersion: 'TLSv1.2',
  ciphers: [
    'ECDHE-ECDSA-AES128-GCM-SHA256',
    'ECDHE-RSA-AES128-GCM-SHA256',
    'ECDHE-ECDSA-AES256-GCM-SHA384',
    'ECDHE-RSA-AES256-GCM-SHA384'
  ].join(':')
}, app)
```

# KEY MANAGEMENT
```
NEVER hardcode encryption keys.

Options:
1. Environment variables (simple, but limited)
2. AWS KMS / GCP KMS (cloud-native, auditable)
3. HashiCorp Vault (self-hosted, flexible)
4. HSM (hardware security module, highest security)

Key rotation strategy:
- Rotate keys periodically (every 90 days)
- Re-encrypt data with new key
- Keep old keys for decrypting legacy data
- Use key versioning to track which key encrypted which data
```

```typescript
// Key versioning for rotation
interface EncryptedData {
  keyVersion: string  // Which key version was used
  ciphertext: string
  iv: string
  authTag: string
}

class KeyManager {
  private keys: Map<string, Buffer> = new Map()
  private currentVersion: string

  async encrypt(plaintext: string): Promise<EncryptedData> {
    const key = this.keys.get(this.currentVersion)!
    const iv = crypto.randomBytes(16)
    const cipher = crypto.createCipheriv('aes-256-gcm', key, iv)
    
    let ciphertext = cipher.update(plaintext, 'utf8', 'hex')
    ciphertext += cipher.final('hex')
    
    return {
      keyVersion: this.currentVersion,
      ciphertext,
      iv: iv.toString('hex'),
      authTag: cipher.getAuthTag().toString('hex')
    }
  }

  async decrypt(data: EncryptedData): Promise<string> {
    const key = this.keys.get(data.keyVersion)
    if (!key) {
      throw new Error(`Unknown key version: ${data.keyVersion}`)
    }
    
    const iv = Buffer.from(data.iv, 'hex')
    const ciphertext = Buffer.from(data.ciphertext, 'hex')
    const authTag = Buffer.from(data.authTag, 'hex')
    
    const decipher = crypto.createDecipheriv('aes-256-gcm', key, iv)
    decipher.setAuthTag(authTag)
    
    let decrypted = decipher.update(ciphertext, 'hex', 'utf8')
    decrypted += decipher.final('utf8')
    
    return decrypted
  }
}
```

# HASHING (One-Way)
```typescript
import bcrypt from 'bcrypt'
import crypto from 'crypto'

// Password hashing
async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, 12)
}

async function verifyPassword(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash)
}

// Data integrity (SHA-256)
function hashData(data: string): string {
  return crypto.createHash('sha256').update(data).digest('hex')
}

// HMAC (authenticated hash)
function createHMAC(data: string, secret: string): string {
  return crypto.createHmac('sha256', secret).update(data).digest('hex')
}
```

# REVIEW CHECKLIST
```
[ ] AES-256-GCM used for symmetric encryption
[ ] Unique IV for each encryption operation
[ ] Keys never hardcoded or committed
[ ] Key rotation plan documented
[ ] TLS 1.2+ enforced for transit
[ ] Passwords hashed with bcrypt/argon2
[ ] Authenticated encryption (GCM) used
[ ] Encrypted data backed up securely
[ ] Key access logged and audited
```
