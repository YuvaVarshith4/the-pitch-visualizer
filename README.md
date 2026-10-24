# Pitch Visualizer

**Transform Any Narrative Into Visual Stories**

The Pitch Visualizer is an AI-powered cinematic storyboarding service that ingests narrative text (business pitches, personal stories, or daily life moments), deconstructs it into logical scenes, and programmatically generates a multi-panel visual storyboard. It combines intelligent prompt engineering, visual consistency techniques, and enterprise-grade security features including cryptographic watermarking.

📸 **[View Website Screenshots](https://drive.google.com/drive/folders/1qHs_3JhRxox-nIs8j8wgevLSIkqIpcAw?usp=sharing)** — See the UI, storyboard outputs, and security features in action.

![Tech Stack](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Docker Setup](#docker-setup)
- [Vercel Deployment](#vercel-deployment)
- [Manual Setup](#manual-setup)
- [API Key Management](#api-key-management)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Design Choices](#design-choices)
- [Security Features](#security-features)
- [Project Structure](#project-structure)

---

## Overview

A powerful narrative is the cornerstone of any effective sales pitch. Storytelling transforms abstract features into tangible benefits. However, translating a well-crafted narrative into a compelling visual aid is a significant creative and logistical bottleneck.

**The Pitch Visualizer** automates this creative process. Paste a customer success story and instantly receive a visual storyboard that brings it to life, complete with:

- **17 Scene Archetypes**: Crisis, joy, struggle, connection, and more with context-appropriate lighting
- **Zero-Trust SecOps**: Automatic PII detection and masking before external API calls
- **Visual Consistency**: Fixed seed parameter ensures coherent style across all panels
- **Cryptographic Watermarking**: AES-128 encrypted tracking data embedded in every image
- **Configurable Panel Count**: Choose 1-7 images per storyboard

---

## Key Features

### Core Requirements (Must-Haves)

| Feature | Description |
|---------|-------------|
| **Text Input** | Accepts 3-7 sentence narratives (business, personal, daily life) |
| **Narrative Segmentation** | Algorithmically breaks input into logical scenes using LLM |
| **Intelligent Prompt Engineering** | LLM-powered transformation of text into highly detailed, artistic prompts |
| **Image Generation** | Async generation using Pollinations.ai (free) or Hugging Face FLUX.1-schnell |
| **Storyboard Presentation** | Beautiful HTML interface displaying panels with captions |
| **Configurable Image Count** | Select 1-7 panels per storyboard via dropdown |

### Bonus Objectives (Implemented)

| Feature | Implementation |
|---------|----------------|
| **Visual Consistency** | Fixed seed (1337) across all panels + style keywords appended to every prompt |
| **User-Selectable Styles** | 4 visual styles: Cinematic Photorealism, Corporate Vector, Cyberpunk, Watercolor |
| **LLM-Powered Prompt Refinement** | Groq API for archetype detection and prompt enhancement |
| **Dynamic UI** | Modern Tailwind CSS interface with real-time streaming progress |
| **Enterprise Security** | Microsoft Presidio PII anonymization + AES-128 steganographic watermarks |
| **Docker Support** | One-command deployment with Docker Compose |
| **Vercel Deployment** | Serverless deployment with base64 image delivery |

---

## Architecture

The system follows a 6-phase pipeline architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PHASE A       │ -> │   PHASE B       │ -> │   PHASE C       │
│  Ingestion      │    │  Zero-Trust     │    │  Continuity     │
│  (Validation)   │    │  SecOps         │    │  Engine (LLM)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                    |
┌─────────────────┐    ┌─────────────────┐         |
│   PHASE F       │ <- │   PHASE E       │ <-      v
│  Assembly       │    │  Steganography  │    ┌─────────────────┐
│  (HTML Output)  │    │  (Watermark)    │ <- │   PHASE D       │
└─────────────────┘    └─────────────────┘    │  Parallel Gen   │
                                             └─────────────────┘
```

### Phase Details

**Phase A: Ingestion & Dynamic UI**
- Input validation (3-7 sentences, 50-2000 characters)
- Rate limiting (10 requests/minute per IP)
- Modern web interface with Tailwind CSS

**Phase B: Zero-Trust SecOps Layer**
- Local NLP processing via Microsoft Presidio
- Entity detection: PERSON, ORGANIZATION, MONEY, EMAIL, PHONE, LOCATION
- Auto-masking: "Acme Corp's $5M deficit" → `<ORGANIZATION>'s <MONEY> deficit`

**Phase C: The Continuity Engine**
- Groq API for prompt engineering
- 17 scene archetypes with matched lighting and camera angles
- Dynamic character casting based on scene context
- Retry logic with exponential backoff

**Phase D: High-Speed Image Generation**
- Python asyncio for concurrent image generation
- Fixed seed (1337) for visual continuity
- Pollinations.ai (free, no API key) or Hugging Face FLUX.1-schnell
- In-memory processing with base64 delivery (serverless compatible)

**Phase E: Cryptographic Deal Tracking**
- AES-128-CBC encryption for payload
- LSB (Least Significant Bit) steganography encoding
- Embedded metadata: panel ID, request ID, timestamp, seed

**Phase F: Dynamic Assembly & Rendering**
- Server-Sent Events (SSE) for real-time progress streaming
- Direct DOM manipulation with JavaScript
- Gallery feature for previous storyboards

---

### Narrative Chunking & Emotional Continuity

**How We Divide Content into Chunks:**

The system uses an **LLM-powered semantic segmentation engine** (Phase C: Continuity Engine) to break narratives into meaningful scenes rather than simple sentence splits:

1. **Sentence Boundary Analysis**: Input is first tokenized at natural sentence boundaries
2. **Archetype Classification**: Each sentence is classified into one of **17 scene archetypes** (crisis, discovery, action, outcome, connection, struggle, joy, etc.) using Groq LLM
3. **Logical Grouping**: Adjacent sentences with complementary archetypes are grouped into a natural progression
4. **Contextual Boundaries**: The LLM identifies natural transition points in the narrative flow, ensuring each chunk represents a complete emotional beat
5. **Configurable Count**: Users select 1-7 panels; the LLM splits or merges sentences into the requested number of distinct visual beats

**How We Maintain Connection & Emotion Between Chunks:**

| Mechanism | Implementation |
|-----------|----------------|
| **Fixed Seed Consistency** | All images use `seed=1337` ensuring visually coherent style across every panel |
| **Archetype-Matched Visual Language** | Each archetype triggers specific lighting, camera angles, and emotional framing |
| **Dynamic Character Casting** | The LLM extracts character details and maintains them across all scenes |
| **Global Style Prefix** | The user-selected visual style is prepended to every prompt, ensuring artistic uniformity |

## Tech Stack

| Category | Technology | Purpose |
|----------|------------|---------|
| **Backend** | FastAPI | High-performance async web framework |
| **Security** | Microsoft Presidio | Local PII detection and anonymization |
| **LLM** | Groq API | Prompt engineering and scene segmentation |
| **Image Gen** | Pollinations.ai / Hugging Face | Text-to-image generation |
| **Steganography** | PyCryptodome + Pillow | AES-128 encryption and LSB encoding |
| **Frontend** | Tailwind CSS + Vanilla JS | Modern responsive UI |
| **Decoder** | Tkinter | Standalone GUI for watermark extraction |
| **Deployment** | Docker + Vercel | Containerized and serverless deployment |

---

## Quick Start

### Option 1: Docker (Recommended)

```bash
git clone https://github.com/YuvaVarshith4/the-pitch-visualizer.git
cd the-pitch-visualizer
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
docker compose up --build
```

Open `http://localhost:8000` in your browser.

### Option 2: Local Python

```bash
git clone https://github.com/YuvaVarshith4/the-pitch-visualizer.git
cd the-pitch-visualizer
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
python main.py
```

Open `http://localhost:8000` in your browser.

---

## Docker Setup

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose installed
- A Groq API key ([get one free](https://console.groq.com))

### Running with Docker

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YuvaVarshith4/the-pitch-visualizer.git
   cd the-pitch-visualizer
   ```

2. **Create your environment file:**
   ```bash
   cp .env.example .env
   ```

3. **Add your API key** — edit `.env` and set `GROQ_API_KEY`:
   ```
   GROQ_API_KEY=gsk_your_key_here
   USE_POLLINATIONS=true
   ```

4. **Start the container:**
   ```bash
   docker compose up --build
   ```

5. **Open** `http://localhost:8000` in your browser.

### Stopping

```bash
docker compose down
```

### Health Check

The container includes a built-in health check. Verify with:
```bash
curl http://localhost:8000/health
```

---

## Vercel Deployment

The app is deployed as a serverless function on Vercel. Images are delivered as base64 data URIs — no storage required.

### Deploy Your Own

1. **Fork or clone this repo**
2. **Install Vercel CLI:**
   ```bash
   npm i -g vercel
   ```
3. **Deploy:**
   ```bash
   vercel --prod
   ```
4. **Set environment variables** in the Vercel dashboard:
   - `GROQ_API_KEY` — your Groq API key
   - `USE_POLLINATIONS` — set to `true`

### How It Works on Vercel

- `api/index.py` imports the FastAPI app from `main.py`
- `vercel.json` routes all requests to the serverless function or static `index.html`
- Images are generated in-memory, watermarked, and returned as base64 data URIs
- No file system writes (compatible with read-only serverless environments)

---

## Manual Setup

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Step-by-Step Installation

1. **Clone the project:**
   ```bash
   git clone https://github.com/YuvaVarshith4/the-pitch-visualizer.git
   cd the-pitch-visualizer
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download spaCy model for Presidio:**
   ```bash
   python -m spacy download en_core_web_sm
   ```

5. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

6. **Configure API keys** (see [API Key Management](#api-key-management))

7. **Run the server:**
   ```bash
   python main.py
   ```

8. **Open** `http://localhost:8000` in your browser.

---

## API Key Management

### Required Keys

| Variable | Service | Purpose | Free Tier |
|----------|---------|---------|-----------|
| `GROQ_API_KEY` | [Groq](https://console.groq.com) | LLM for prompt engineering | Yes (generous limits) |

### Optional Keys

| Variable | Purpose | Default |
|----------|---------|---------|
| `HF_API_TOKEN` | Hugging Face image generation (alternative to Pollinations) | Not required |
| `USE_POLLINATIONS` | Use free Pollinations.ai for images | `true` |
| `ENCRYPTION_KEY` | AES-128 encryption key | `16ByteSecretKey!` |
| `ENCRYPTION_IV` | AES-128 initialization vector | `16ByteInitVector` |

### Environment File Example (`.env`)

```bash
# Required
GROQ_API_KEY=gsk_your_groq_api_key_here

# Image generation (Pollinations is free, no key needed)
USE_POLLINATIONS=true

# Optional: Hugging Face (alternative image source)
HF_API_TOKEN=hf_your_huggingface_token_here

# Optional: Encryption keys for steganography
ENCRYPTION_KEY=MySecretKey123!!
ENCRYPTION_IV=MyInitVector123!!
```

### Security Notes

- Never commit `.env` files to version control
- Use different encryption keys for production deployments
- The decoder GUI (`decoder_gui.py`) must use the same encryption keys to extract watermarks

---

## Usage

### Web Interface

1. Navigate to `http://localhost:8000` (or your Vercel URL)
2. Select a **visual style** from the dropdown
3. Choose the **number of images** (1-7)
4. Paste your narrative (3-7 sentences) in the text area
5. Click **"Generate Storyboard"**
6. Watch real-time progress as panels generate
7. View your completed storyboard with captions and AI prompts

### Example Narratives

**Business Pitch:**
```
CFO Victoria Chen discovered a $12M inventory discrepancy that threatened Q3 earnings. 
Our team deployed blockchain verification across 47 distribution centers within 48 hours. 
We recovered the full inventory value and implemented real-time tracking. 
Victoria presented the solution to the board, securing a 3-year enterprise contract.
```

**Personal Story:**
```
Sarah, a 28-year-old nurse, felt overwhelmed during her first night shift in the ICU. 
An elderly patient shared stories about resilience that changed her perspective. 
She found the courage to advocate for better staffing ratios. 
Six months later, she led the hospital's first nurse wellness program.
```

### Using the Decoder Tool

Extract hidden watermarks from generated images:

```bash
python decoder_gui.py
```

1. Click **"Select Image to Decrypt"**
2. Choose a storyboard PNG file
3. View the extracted metadata (panel ID, timestamp, request ID)

---

## API Endpoints

| Endpoint | Method | Description | Rate Limit |
|----------|--------|-------------|------------|
| `/` | GET | Serve the main frontend HTML | - |
| `/api/generate` | POST | Generate complete storyboard | 10/minute |
| `/api/generate-stream` | POST | Streaming generation with progress | 10/minute |
| `/api/regenerate-panel` | POST | Retry a single failed panel | 30/minute |
| `/api/info` | GET | API information and capabilities | - |
| `/health` | GET | Health check with dependency status | - |

### Example API Call

```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "narrative": "Our startup struggled to find product-market fit for 18 months. We pivoted to focus on enterprise customers. Within 6 months, we landed three Fortune 500 clients.",
    "style": "Cinematic Photorealism, 8k, highly detailed",
    "num_images": 3
  }'
```

---

## Design Choices

### Prompt Engineering Methodology

The system uses a **two-tier prompt engineering approach**:

**Tier 1: Archetype Classification**
The LLM classifies each sentence into one of 17 archetypes:
- **Professional**: crisis, discovery, action, outcome, relationship
- **Personal**: conflict, struggle, routine, connection, loss, joy, transition
- **Universal**: growth, reflection, exploration

**Tier 2: Archetype-to-Visual Mapping**
Each archetype maps to specific visual parameters:
```
CRISIS      → cold harsh light, tense body language, cluttered environment
CONNECTION  → warm golden light, close proximity, genuine smiles
GROWTH      → expansive wide shot, natural light, forward-facing posture
```

**Tier 3: Dynamic Character Casting**
Characters are contextually appropriate based on the scene:
- School settings → child/teenager
- Career scenes → young adult/professional with named role
- Family moments → parent/couple
- Wisdom scenes → elderly person

### Visual Consistency Strategy

1. **Fixed Seed**: All images use `seed=1337` for coherent style
2. **Global Style Prefix**: Selected style prepended to every prompt
3. **Scene-Archetype Matching**: Lighting and angles aligned to emotional tone

### Rate Limiting & Resilience

- **Request Rate**: 10/minute per IP (slowapi)
- **Concurrent LLM**: Semaphore-limited to 5 requests
- **Image Generation**: Sequential with 15s delays between panels (respects Pollinations limits)
- **Retry Logic**: Exponential backoff (5 attempts, 15s base) for 402/503/500/429 errors

---

## Security Features

### Zero-Trust SecOps Pipeline

1. **Local Processing**: PII detection happens on-device via Presidio
2. **Entity Masking**: Sensitive data replaced with tags before LLM/image APIs
3. **No Data Logging**: Request IDs are ephemeral, images delivered as base64

### Cryptographic Watermarking

| Aspect | Implementation |
|--------|----------------|
| Encryption | AES-128-CBC with PKCS7 padding |
| Encoding | LSB (Least Significant Bit) in Red channel |
| Delimiter | 16-bit pattern `1111111111111110` |
| Payload | Panel ID, Request ID, Timestamp, Seed |
| Extraction | 100% data recovery without visual quality loss |

### Decoder Verification

Run `python decoder_gui.py` to:
- Verify image authenticity
- Track asset distribution
- Prove 100% data recovery

---

## Project Structure

```
pitch-visualizer/
├── main.py                 # FastAPI application (core backend)
├── index.html              # Frontend UI (Tailwind CSS + JS)
├── decoder_gui.py          # Tkinter watermark decoder tool
├── stego_utils.py          # AES-128 + LSB steganography utilities
├── presidio_config.py      # SecOps engine configuration
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Docker Compose configuration
├── build.sh                # Vercel build script
├── vercel.json             # Vercel deployment config
├── api/
│   └── index.py            # Vercel serverless entry point
├── static/                 # Generated storyboard images (local only)
└── .dockerignore           # Docker build exclusions
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'spacy'` | Run `pip install -r requirements.txt` and `python -m spacy download en_core_web_sm` |
| `429 Too Many Requests` | Wait a moment — rate limiting is in effect. Pollinations has per-IP limits. |
| `Images not generating` | Check `GROQ_API_KEY` in `.env`. Ensure `USE_POLLINATIONS=true` is set. |
| `Decoder fails to extract` | Ensure same `ENCRYPTION_KEY` and `ENCRYPTION_IV` used for generation |
| `Docker container unhealthy` | Run `docker compose logs` to check for missing env vars |
| `Vercel build fails` | Ensure `build.sh` is executable and `requirements.txt` includes spaCy wheel URL |

---

## License

MIT License - Feel free to use, modify, and distribute for personal or commercial projects.

---

## Acknowledgments

- **Groq** for high-speed LLM inference
- **Pollinations.ai** for free image generation
- **Hugging Face** for FLUX.1-schnell model hosting
- **Microsoft Presidio** for local PII detection
- **FastAPI** for the excellent web framework
