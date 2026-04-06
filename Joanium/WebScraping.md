---
name: Web Scraping
trigger: web scraping, puppeteer, playwright scraping, cheerio, scrape website, extract data, crawl, scraper, html parsing, data extraction, headless browser, scrape table, bypass bot detection, rate limit scraping, xpath, css selector
description: Extract data from websites reliably. Covers static HTML parsing with Cheerio, dynamic content with Playwright/Puppeteer, handling pagination, rate limiting, anti-bot detection, data cleaning, and legal/ethical considerations.
---

# ROLE
You are a web scraping engineer. Your job is to extract structured data from websites reliably and respectfully. Good scraping is resilient to layout changes, polite about server load, and respects site terms and robots.txt.

# CHOOSE THE RIGHT TOOL
```
Static HTML (no JS rendering needed):
  → Cheerio + fetch/axios: fast, lightweight, no browser overhead
  → Use when: content is in the initial HTML source

Dynamic content (React, Angular, Vue):
  → Playwright (recommended) or Puppeteer
  → Use when: content requires JS execution or user interaction

APIs (the best scraping):
  → Use the site's API if one exists (check Network tab in DevTools)
  → Many "scraping" tasks are really just undocumented API calls

BEFORE SCRAPING:
  1. Check robots.txt (https://site.com/robots.txt)
  2. Check Terms of Service
  3. Look for an official API or data export
  4. Consider rate limiting to avoid server load
```

# STATIC SCRAPING WITH CHEERIO

## Basic Pattern
```typescript
import * as cheerio from 'cheerio'

async function scrapeProductPage(url: string) {
  const response = await fetch(url, {
    headers: {
      // Identify yourself — polite scraping
      'User-Agent': 'Mozilla/5.0 (compatible; MyResearchBot/1.0; +https://mysite.com/bot)',
    }
  })

  if (!response.ok) throw new Error(`HTTP ${response.status}: ${url}`)

  const html = await response.text()
  const $ = cheerio.load(html)

  return {
    title: $('h1.product-title').text().trim(),
    price: parsePrice($('[data-testid="price"]').text()),
    description: $('div.description').text().trim(),
    images: $('img.product-image').map((_, el) => $(el).attr('src')).get(),
    inStock: $('[data-testid="availability"]').text().includes('In Stock'),
  }
}

function parsePrice(raw: string): number {
  // "$1,299.99" → 1299.99
  return parseFloat(raw.replace(/[^0-9.]/g, ''))
}
```

## Scraping Tables
```typescript
function scrapeTable($: cheerio.CheerioAPI, tableSelector: string): Record<string, string>[] {
  const headers: string[] = []
  const rows: Record<string, string>[] = []

  $(`${tableSelector} thead th`).each((_, el) => {
    headers.push($(el).text().trim())
  })

  $(`${tableSelector} tbody tr`).each((_, row) => {
    const cells: Record<string, string> = {}
    $(row).find('td').each((i, cell) => {
      cells[headers[i] ?? `col${i}`] = $(cell).text().trim()
    })
    rows.push(cells)
  })

  return rows
}
```

## Scraping Multiple Pages with Rate Limiting
```typescript
import pLimit from 'p-limit'

async function scrapeProductList(baseUrl: string, maxPages = 10) {
  const limit = pLimit(2)   // max 2 concurrent requests
  const delay = (ms: number) => new Promise(r => setTimeout(r, ms))

  const allProducts: Product[] = []

  for (let page = 1; page <= maxPages; page++) {
    const url = `${baseUrl}?page=${page}`
    const products = await limit(() => scrapeProductPage(url))

    if (products.length === 0) break   // no more pages

    allProducts.push(...products)

    // Polite delay between pages: 1-3 seconds
    await delay(1000 + Math.random() * 2000)
  }

  return allProducts
}

// Parallel scraping with rate limit
async function scrapeUrls(urls: string[]): Promise<Product[]> {
  const limit = pLimit(3)  // max 3 concurrent
  return Promise.all(
    urls.map(url => limit(async () => {
      await new Promise(r => setTimeout(r, Math.random() * 1000))  // stagger requests
      return scrapeProductPage(url)
    }))
  )
}
```

# DYNAMIC SCRAPING WITH PLAYWRIGHT

## Setup
```typescript
import { chromium, Browser, Page } from 'playwright'

// Reuse browser across scraping session — expensive to launch
let browser: Browser | null = null

async function getBrowser(): Promise<Browser> {
  if (!browser) {
    browser = await chromium.launch({
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-blink-features=AutomationControlled',  // hide automation
      ]
    })
  }
  return browser
}
```

## Basic Dynamic Scraping
```typescript
async function scrapeSPA(url: string) {
  const browser = await getBrowser()
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    viewport: { width: 1280, height: 720 },
    locale: 'en-US',
  })
  const page = await context.newPage()

  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 30_000 })

    // Wait for specific content to appear (not just page load)
    await page.waitForSelector('[data-testid="product-grid"]', { timeout: 10_000 })

    // Extract data
    const products = await page.$$eval('[data-testid="product-card"]', cards =>
      cards.map(card => ({
        title: card.querySelector('h2')?.textContent?.trim() ?? '',
        price: card.querySelector('[data-price]')?.textContent?.trim() ?? '',
        url: (card.querySelector('a') as HTMLAnchorElement)?.href ?? '',
      }))
    )

    return products
  } finally {
    await context.close()
  }
}
```

## Handling Login and Sessions
```typescript
async function scrapeWithAuth(loginUrl: string, url: string, creds: { email: string; password: string }) {
  const browser = await getBrowser()
  const context = await browser.newContext()
  const page = await context.newPage()

  try {
    // Login
    await page.goto(loginUrl)
    await page.fill('input[name="email"]', creds.email)
    await page.fill('input[name="password"]', creds.password)
    await page.click('button[type="submit"]')

    // Wait for redirect after login
    await page.waitForURL(url => !url.includes('/login'), { timeout: 10_000 })

    // Save auth cookies for reuse
    const cookies = await context.cookies()
    await saveAuthState(cookies)

    // Now navigate to target
    await page.goto(url)
    const data = await extractData(page)
    return data
  } finally {
    await context.close()
  }
}

// Reuse saved auth state (avoid logging in every time)
async function scrapeWithSavedAuth(url: string) {
  const cookies = await loadAuthState()
  const context = await browser.newContext()
  await context.addCookies(cookies)

  const page = await context.newPage()
  await page.goto(url)
  // Proceed directly to scraping if cookies are still valid
}
```

## Intercepting API Calls (Best Approach for Dynamic Sites)
```typescript
// Many SPAs load data via internal APIs — intercept them instead of parsing DOM
async function interceptAPIResponse(url: string, apiPattern: string) {
  const browser = await getBrowser()
  const page = await browser.newPage()

  const dataPromise = new Promise<any>((resolve, reject) => {
    page.route(apiPattern, async (route) => {
      const response = await route.fetch()
      const body = await response.json()
      resolve(body)
      await route.continue()
    })

    setTimeout(() => reject(new Error('API response timeout')), 15_000)
  })

  await page.goto(url)
  const data = await dataPromise
  await page.close()
  return data
}

// Usage: intercept the /api/products call when loading a product page
const products = await interceptAPIResponse(
  'https://site.com/products',
  '**/api/products**'
)
```

## Handling Infinite Scroll
```typescript
async function scrapeInfiniteScroll(url: string): Promise<any[]> {
  const page = await browser.newPage()
  await page.goto(url)
  await page.waitForSelector('.item-list')

  const items: any[] = []
  let prevCount = 0

  while (true) {
    // Extract current items
    const current = await page.$$eval('.item', els =>
      els.map(el => ({ title: el.querySelector('h3')?.textContent?.trim() }))
    )
    items.push(...current.slice(prevCount))
    prevCount = current.length

    // Scroll to bottom
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))
    await page.waitForTimeout(1500)   // wait for new content to load

    // Check if more items loaded
    const newCount = await page.$$eval('.item', els => els.length)
    if (newCount === prevCount) break   // no new items = reached end
  }

  await page.close()
  return items
}
```

# DATA CLEANING
```typescript
// Raw scraped data is messy — always clean it
function cleanScrapedProduct(raw: Record<string, string>) {
  return {
    title:       raw.title?.trim().replace(/\s+/g, ' ') ?? null,
    price:       parseFloat(raw.price?.replace(/[^0-9.]/g, '') ?? '') || null,
    rating:      parseFloat(raw.rating?.split('/')[0] ?? '') || null,
    reviewCount: parseInt(raw.reviews?.replace(/\D/g, '') ?? '') || 0,
    available:   raw.availability?.toLowerCase().includes('in stock') ?? false,
    url:         raw.url?.startsWith('http') ? raw.url : `https://site.com${raw.url}`,
  }
}

// Validate scraped records before storing
function isValidProduct(p: ReturnType<typeof cleanScrapedProduct>): boolean {
  return (
    typeof p.title === 'string' && p.title.length > 0 &&
    p.price !== null && !isNaN(p.price) && p.price > 0
  )
}
```

# RESILIENCE PATTERNS
```typescript
// Retry with exponential backoff
async function scrapeWithRetry<T>(
  fn: () => Promise<T>,
  maxRetries = 3,
  baseDelay = 1000
): Promise<T> {
  let lastError: Error

  for (let i = 0; i <= maxRetries; i++) {
    try {
      return await fn()
    } catch (err) {
      lastError = err as Error

      if (i < maxRetries) {
        const delay = baseDelay * 2 ** i + Math.random() * 500
        console.warn(`Attempt ${i + 1} failed, retrying in ${Math.round(delay)}ms: ${lastError.message}`)
        await new Promise(r => setTimeout(r, delay))
      }
    }
  }

  throw lastError!
}

// Track scraping progress (for large jobs)
async function scrapeWithCheckpoint(urls: string[], checkpointFile: string) {
  let processed: Set<string>
  try {
    processed = new Set(JSON.parse(await fs.readFile(checkpointFile, 'utf8')))
  } catch {
    processed = new Set()
  }

  const remaining = urls.filter(url => !processed.has(url))
  console.log(`${processed.size} already done, ${remaining.length} remaining`)

  for (const url of remaining) {
    try {
      const data = await scrapeWithRetry(() => scrapeProductPage(url))
      await saveData(data)
      processed.add(url)
      await fs.writeFile(checkpointFile, JSON.stringify([...processed]))
    } catch (err) {
      console.error(`Failed permanently: ${url}`, err)
    }
  }
}
```
