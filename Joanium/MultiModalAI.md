---
name: Multimodal AI (Vision & Files)
trigger: multimodal, vision, image input, analyze image, describe image, ocr, pdf to llm, send image to claude, send image to gpt, base64 image, image url, vision api, screenshot analysis, document understanding, audio transcription, image generation
description: Send images, PDFs, and other media to multimodal LLMs. Covers base64 encoding, URL references, image optimization, PDF document handling, OCR patterns, screenshot analysis, and cost-aware usage.
---

# ROLE
You are a senior AI engineer. Your job is to integrate vision and multimodal capabilities efficiently — sending the right data in the right format without burning tokens on unnecessarily large images or unsupported formats.

# CORE PRINCIPLES
```
RESIZE FIRST:     Images > 1024px long-edge waste tokens — resize before sending
FORMAT MATTERS:   JPEG for photos, PNG for screenshots/diagrams, WebP for web
BASE64 OR URL:    Base64 for local/private files, URL for public web images
COST AWARE:       Each image costs ~1000–2000 tokens — budget accordingly
PROMPT CLEARLY:   Multimodal models need explicit instructions about what to look for
```

# IMAGE FORMATS & COSTS

## Token Cost by Image Size (Anthropic Claude)
```
Image resolution    → Approximate tokens
─────────────────────────────────────────
< 200px             → ~200 tokens
512 × 512           → ~500 tokens
1024 × 1024         → ~1600 tokens
2048 × 2048         → ~5000 tokens
Original 4K photo   → 10,000+ tokens

Recommendation:
  - Screenshots / diagrams: resize to max 1024px wide → ~1000 tokens
  - Photos where detail matters: max 1600px wide → ~2500 tokens
  - Thumbnail recognition: 512px is usually enough → ~500 tokens
```

# SENDING IMAGES

## Anthropic (Claude)
```javascript
import Anthropic from '@anthropic-ai/sdk';
import fs from 'fs';
import sharp from 'sharp';  // npm install sharp

const anthropic = new Anthropic();

// Method 1: Base64 (for local files)
async function analyzeLocalImage(imagePath, prompt) {
  // Resize to save tokens
  const resized = await sharp(imagePath)
    .resize({ width: 1024, height: 1024, fit: 'inside', withoutEnlargement: true })
    .jpeg({ quality: 85 })
    .toBuffer();

  const base64 = resized.toString('base64');

  return anthropic.messages.create({
    model: 'claude-sonnet-4-20250514',
    max_tokens: 1024,
    messages: [{
      role: 'user',
      content: [
        {
          type: 'image',
          source: {
            type: 'base64',
            media_type: 'image/jpeg',
            data: base64,
          },
        },
        { type: 'text', text: prompt },
      ],
    }],
  });
}

// Method 2: URL (for public images)
async function analyzeImageURL(imageUrl, prompt) {
  return anthropic.messages.create({
    model: 'claude-sonnet-4-20250514',
    max_tokens: 1024,
    messages: [{
      role: 'user',
      content: [
        {
          type: 'image',
          source: { type: 'url', url: imageUrl },
        },
        { type: 'text', text: prompt },
      ],
    }],
  });
}

// Multiple images in one request
async function compareImages(imagePaths, question) {
  const imageBlocks = await Promise.all(imagePaths.map(async (imgPath) => {
    const buf = await sharp(imgPath).resize(800, 800, { fit: 'inside' }).jpeg().toBuffer();
    return {
      type: 'image',
      source: { type: 'base64', media_type: 'image/jpeg', data: buf.toString('base64') },
    };
  }));

  return anthropic.messages.create({
    model: 'claude-sonnet-4-20250514',
    max_tokens: 2048,
    messages: [{
      role: 'user',
      content: [...imageBlocks, { type: 'text', text: question }],
    }],
  });
}
```

## OpenAI (GPT-4o)
```javascript
import OpenAI from 'openai';

const openai = new OpenAI();

// Base64
async function analyzeWithGPT4o(imagePath, prompt) {
  const imageData = fs.readFileSync(imagePath).toString('base64');
  const ext = path.extname(imagePath).slice(1);
  const mediaType = ext === 'jpg' ? 'image/jpeg' : `image/${ext}`;

  return openai.chat.completions.create({
    model: 'gpt-4o',
    max_tokens: 1024,
    messages: [{
      role: 'user',
      content: [
        {
          type: 'image_url',
          image_url: {
            url: `data:${mediaType};base64,${imageData}`,
            detail: 'auto',  // 'low' | 'high' | 'auto'
            // 'low' = fixed 85 tokens, fast, good for simple recognition
            // 'high' = full detail, up to 1000+ tokens
          },
        },
        { type: 'text', text: prompt },
      ],
    }],
  });
}
```

# PDF & DOCUMENT HANDLING

## Anthropic PDF Support (Native)
```javascript
// Claude supports PDFs natively as documents
async function analyzePDF(pdfPath, question) {
  const pdfData = fs.readFileSync(pdfPath).toString('base64');

  return anthropic.messages.create({
    model: 'claude-sonnet-4-20250514',
    max_tokens: 4096,
    messages: [{
      role: 'user',
      content: [
        {
          type: 'document',
          source: {
            type: 'base64',
            media_type: 'application/pdf',
            data: pdfData,
          },
        },
        { type: 'text', text: question },
      ],
    }],
  });
}

// From URL
const urlPDFContent = {
  type: 'document',
  source: { type: 'url', url: 'https://example.com/report.pdf' },
};
```

## PDF Text Extraction (Fallback)
```javascript
import pdfParse from 'pdf-parse';

async function extractPDFText(pdfPath) {
  const buffer = fs.readFileSync(pdfPath);
  const data = await pdfParse(buffer);
  return {
    text: data.text,
    pages: data.numpages,
    info: data.info,
  };
}

// Send extracted text instead of image — cheaper, works with all models
async function queryPDFAsText(pdfPath, question) {
  const { text } = await extractPDFText(pdfPath);
  return anthropic.messages.create({
    model: 'claude-haiku-4-5-20251001',  // cheaper for text-only
    max_tokens: 2048,
    messages: [{
      role: 'user',
      content: `Document:\n\n${text}\n\n---\n\n${question}`,
    }],
  });
}
```

# COMMON USE CASES

## Screenshot / UI Analysis
```javascript
async function analyzeScreenshot(screenshotPath) {
  const result = await analyzeLocalImage(screenshotPath, `
    Analyze this UI screenshot. Describe:
    1. What type of interface this is
    2. The main elements visible
    3. Any obvious UX issues or errors
    4. What the user was doing when this was captured
    
    Be specific and technical.
  `);
  return result.content[0].text;
}
```

## OCR (Text Extraction from Image)
```javascript
async function extractTextFromImage(imagePath) {
  const result = await analyzeLocalImage(imagePath, `
    Extract ALL text from this image exactly as it appears.
    Preserve formatting, line breaks, and structure.
    Output only the extracted text — no commentary.
  `);
  return result.content[0].text;
}
```

## Chart / Graph Understanding
```javascript
async function analyzeChart(chartImagePath) {
  const result = await analyzeLocalImage(chartImagePath, `
    Analyze this chart/graph:
    1. Chart type (bar, line, pie, etc.)
    2. Title and axis labels
    3. Key data points and values
    4. Main trend or insight
    5. Any anomalies or notable patterns
    
    Output as structured JSON.
  `);

  const text = result.content[0].text;
  const jsonMatch = text.match(/```json\n([\s\S]+?)\n```/);
  return jsonMatch ? JSON.parse(jsonMatch[1]) : text;
}
```

## Structured Data Extraction from Images
```javascript
async function extractInvoiceData(invoiceImagePath) {
  const result = await analyzeLocalImage(invoiceImagePath, `
    Extract invoice data from this image. Return ONLY valid JSON:
    {
      "invoiceNumber": "string",
      "date": "YYYY-MM-DD",
      "vendor": "string",
      "totalAmount": number,
      "currency": "string",
      "lineItems": [{ "description": "string", "amount": number }]
    }
    If a field is not found, use null.
  `);

  const text = result.content[0].text.replace(/```json|```/g, '').trim();
  return JSON.parse(text);
}
```

# IMAGE GENERATION

## DALL-E 3 (OpenAI)
```javascript
async function generateImage(prompt, options = {}) {
  const response = await openai.images.generate({
    model: 'dall-e-3',
    prompt,
    n: 1,
    size: options.size || '1024x1024',       // '1024x1024' | '1792x1024' | '1024x1792'
    quality: options.quality || 'standard',  // 'standard' | 'hd'
    style: options.style || 'vivid',         // 'vivid' | 'natural'
    response_format: 'url',                  // 'url' | 'b64_json'
  });
  return response.data[0].url;  // URL expires after 1 hour
}
```

# CLIENT-SIDE (BROWSER)
```javascript
// Convert file input to base64
async function fileToBase64(file) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result.split(',')[1]);
    reader.readAsDataURL(file);
  });
}

// Resize image in browser before sending
async function resizeAndEncode(file, maxWidth = 1024) {
  const bitmap = await createImageBitmap(file);
  const canvas = document.createElement('canvas');
  const scale = Math.min(1, maxWidth / bitmap.width);
  canvas.width = bitmap.width * scale;
  canvas.height = bitmap.height * scale;
  canvas.getContext('2d').drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  
  return new Promise(resolve => {
    canvas.toBlob(blob => {
      const reader = new FileReader();
      reader.onload = () => resolve({
        data: reader.result.split(',')[1],
        mediaType: 'image/jpeg',
      });
      reader.readAsDataURL(blob);
    }, 'image/jpeg', 0.85);
  });
}
```

# COST OPTIMIZATION
```
Prefer text extraction over image when:
  - Document is text-heavy PDF → extract text, query as text (10× cheaper)
  - Table/CSV in image → OCR first, then query the text
  - Code in screenshot → extract text, then analyze

Use 'low' detail (OpenAI) when:
  - Just recognizing what's in an image
  - Classifying image type or content
  - Any task where fine text isn't needed

Always resize before sending:
  - 1024px max for most tasks
  - 512px for thumbnails / quick classification
  - Never send original camera photos without resizing
```
