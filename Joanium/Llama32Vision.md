---
name: Llama 3.2 Vision Prompting
trigger: llama vision prompting, llama 3.2 vision, multimodal llama, llama image, llama vision tips
description: Best practices for prompting Meta's Llama 3.2 Vision models (11B, 90B). Use when building multi-modal pipelines with open-source models — image understanding, document analysis, UI screenshot parsing, and visual QA.
---

# ROLE
You are a Llama 3.2 Vision prompt engineer. Your goal is to use Llama's vision-language capabilities effectively for structured image analysis, document understanding, and visual reasoning tasks.

# MODEL PERSONALITY
```
Llama 3.2 Vision:
- 11B and 90B parameter vision-language models (open-source)
- Strong at: image description, document OCR, chart reading, UI analysis
- Multi-modal: text + image input, text output only
- Follows the same Llama 3 chat template with image tokens
- 90B rivals GPT-4V on many vision benchmarks
- Runs locally (11B fits on 12GB VRAM with 4-bit quantization)
- Available on: Ollama, Groq, Together AI, Replicate
```

# CHAT TEMPLATE WITH IMAGES
```
Llama 3.2 Vision uses the standard Llama 3 template + image tokens:

<|begin_of_text|>
<|start_header_id|>system<|end_header_id|>
You are a document analysis assistant.<|eot_id|>

<|start_header_id|>user<|end_header_id|>
<|image|>
Extract all invoice data as JSON. Schema: {vendor, date, items:[{name,qty,price}], total}<|eot_id|>

<|start_header_id|>assistant<|end_header_id|>

// <|image|> is the image placeholder token — frameworks handle actual image injection.
```

## Ollama (Simplest)
```bash
ollama run llama3.2-vision:11b
ollama run llama3.2-vision:90b
```

```python
import ollama

response = ollama.chat(
    model="llama3.2-vision:11b",
    messages=[
        {
            "role": "user",
            "content": "Extract all text and structure from this receipt as JSON.",
            "images": ["path/to/receipt.jpg"]  # or base64 string
        }
    ]
)
```

## Via API (Together AI / Groq)
```python
client = openai.OpenAI(
    base_url="https://api.together.xyz/v1",
    api_key=os.environ["TOGETHER_API_KEY"]
)

response = client.chat.completions.create(
    model="meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": { "url": f"data:image/jpeg;base64,{b64_image}" }
                },
                {
                    "type": "text",
                    "text": "Describe all UI elements and their states."
                }
            ]
        }
    ]
)
```

# EFFECTIVE VISION PROMPTS

## Document / Invoice Extraction
```
"Extract the following from this document image.
Return ONLY valid JSON. No markdown.
Schema:
{
  document_type: string,
  date: string (ISO format),
  parties: [{ name, role }],
  line_items: [{ description, quantity, unit_price, total }],
  grand_total: number,
  currency: string
}"
```

## UI / Screenshot Analysis
```
"Analyze this UI screenshot.
List every visible component as JSON:
{
  components: [
    {
      type: string (button/input/dropdown/label/etc),
      text: string,
      state: string (enabled/disabled/selected/etc),
      position: string (top-left/center/etc)
    }
  ],
  page_title: string,
  primary_action: string
}"
```

## Chart / Graph Data Extraction
```
"Extract all data from this chart.
Identify: chart type, axis labels, all data series and values.
Return as JSON:
{
  chart_type: string,
  x_axis: { label, values: [] },
  y_axis: { label, unit },
  series: [{ name, data_points: [{x, y}] }]
}"
```

## Visual QA Pattern
```
Strong for verification tasks:
- "Does this image show X? Answer yes/no and explain."
- "Count the number of {objects} visible in this image."
- "What text is visible in the {top-left/center/bottom} region?"
- "List any errors, warnings, or alerts visible in this screenshot."
```

# IMAGE INPUT FORMATS
```
Supported formats:
- JPEG, PNG, WebP, GIF (first frame for GIFs)
- Base64 encoded
- URL (if accessible)
- File path (local Ollama)

Size recommendations:
- Resize to max 1024x1024 for most tasks — larger doesn't improve accuracy
- For text-heavy documents: keep high resolution (1500x2000)
- Compress to JPEG quality 85 — reduces tokens with minimal quality loss

Base64 helper:
import base64
with open("image.jpg", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()
```

# SIZE GUIDE
```
model                        → use case
llama3.2-vision:90B          → complex analysis, high accuracy
llama3.2-vision:11B          → fast, good quality, local-friendly
llama3.2-vision:11B-Q4       → 4-bit quantized, ~7GB VRAM
```

# ANTI-PATTERNS
```
AVOID:
- Vague image prompts ("What's in this image?") — get specific
- Sending very large images without resizing — adds tokens, minimal gain
- Expecting perfect OCR on handwritten text — print only
- Multi-image input per call (not natively supported)

FIX:
- Be specific: "Extract X from the top-right section"
- Resize images before sending (max 1024px on longest side)
- Preprocess heavily handwritten docs with a dedicated OCR tool
- Chain calls for multi-image analysis
```

# REVIEW CHECKLIST
```
[ ] Image resized to ≤1024px (or higher for text docs)
[ ] Image converted to base64 or accessible URL
[ ] Prompt is specific about what to extract/analyze
[ ] Output schema provided as JSON for structured tasks
[ ] Ollama / Together / Groq endpoint configured
[ ] 90B selected for high-accuracy tasks, 11B for speed
[ ] Position references used for region-specific tasks
[ ] JPEG quality compressed to 85 for efficiency
```
