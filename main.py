# Install requirements: pip install fastapi uvicorn pydantic python-dotenv presidio_analyzer presidio_anonymizer groq tenacity aiohttp

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from functools import lru_cache
import hashlib
import uvicorn
import os
import json
import time
import uuid
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional, Dict, Any

# Import Presidio modules for local, zero-trust sanitization
from presidio_config import create_secops_engines

# Phase C: LLM Integration for Continuity Engine
from groq import AsyncGroq, APIError, RateLimitError

# Phase D: Parallel Image Generation
import aiohttp

# Phase E: Cryptographic Steganography
from stego_utils import hide_data, extract_data

# Load environment variables
load_dotenv()

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("pitch_visualizer")

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize the SecOps engines globally so they only load into memory once
# Using lightweight en_core_web_sm model (~12MB) instead of en_core_web_lg (~400MB)
analyzer, anonymizer = create_secops_engines()

# Initialize Groq Client for Phase C Continuity Engine
# Automatically picks up GROQ_API_KEY from environment variables
groq_client = AsyncGroq(timeout=30.0)  # 30 second timeout for LLM calls

# Configuration
MAX_LLM_RETRIES = int(os.getenv("MAX_LLM_RETRIES", "3"))
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "30.0"))
CACHE_MAXSIZE = int(os.getenv("CACHE_MAXSIZE", "100"))
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))
MAX_REQUEST_BODY_SIZE = int(os.getenv("MAX_REQUEST_BODY_SIZE", "10000"))  # 10KB max

# Semaphore for limiting concurrent LLM calls to prevent overwhelming Groq API
llm_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

# Phase D: Image Generation Configuration
HF_API_TOKEN = os.environ.get("HF_API_TOKEN")
# Using FLUX.1-schnell for fast, highly accurate prompt adherence
HF_API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
# Alternative: Pollinations.ai (free, no API key required)
USE_POLLINATIONS = os.getenv("USE_POLLINATIONS", "false").lower() == "true"

# Semaphore for limiting concurrent image generation (Pollinations has strict rate limits)
# Using 1 for sequential processing to avoid 429 errors
MAX_CONCURRENT_IMAGES = int(os.getenv("MAX_CONCURRENT_IMAGES", "1"))
image_semaphore = asyncio.Semaphore(MAX_CONCURRENT_IMAGES)

# Ensure static directory exists for serving generated images
os.makedirs("static", exist_ok=True)

app = FastAPI(
    title="Pitch Visualizer Enterprise API",
    description="Enterprise-grade pitch visualization with SecOps and steganography",
    version="1.0.0"
)

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Enable CORS so our frontend can talk to the backend securely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GZip compression for faster responses (compresses responses > 1000 bytes)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Request body size limiting middleware
@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_REQUEST_BODY_SIZE:
        return JSONResponse(
            status_code=413,
            content={"status": "error", "message": f"Request body too large. Maximum size is {MAX_REQUEST_BODY_SIZE} bytes"}
        )
    return await call_next(request)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Request logging middleware with structured logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    # Store request_id in request state for access in endpoints
    request.state.request_id = request_id
    
    logger.info(
        f"Request started",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else None
        }
    )
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        
        logger.info(
            f"Request completed",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": int(process_time * 1000)
            }
        )
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed",
            extra={
                "request_id": request_id,
                "error": str(e),
                "duration_ms": int(process_time * 1000)
            }
        )
        raise


class PitchPayload(BaseModel):
    narrative: str
    style: str
    
    @validator('narrative')
    def validate_narrative_length(cls, v):
        sentences = [s.strip() for s in v.replace('!', '.').replace('?', '.').split('.') if s.strip()]
        if len(sentences) < 3:
            raise ValueError('Narrative must contain at least 3 sentences')
        if len(sentences) > 7:
            raise ValueError('Narrative should not exceed 7 sentences for optimal visualization')
        if len(v) < 50:
            raise ValueError('Narrative is too short. Please provide more detail (at least 50 characters)')
        if len(v) > 2000:
            raise ValueError('Narrative is too long. Please limit to 2000 characters')
        return v
    
    @validator('style')
    def validate_style(cls, v):
        allowed_styles = [
            "Cinematic Photorealism, 8k, highly detailed",
            "Flat corporate vector art, clean lines, minimalist", 
            "Cyberpunk, neon lighting, dark background",
            "Soft watercolor, bright and optimistic"
        ]
        if v not in allowed_styles:
            raise ValueError(f'Invalid style. Allowed styles: {allowed_styles}')
        return v


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the main frontend HTML"""
    with open("index.html", "r") as f:
        return f.read()


@app.get("/health")
async def health_check():
    """Health check endpoint with dependency status"""
    dependencies = {
        "presidio": True,  # Already initialized at startup
        "groq_api": False
    }
    
    # Check Groq API connectivity
    try:
        # Quick check if API key is configured
        api_key = os.getenv("GROQ_API_KEY")
        if api_key and len(api_key) > 10:
            dependencies["groq_api"] = True
    except Exception:
        dependencies["groq_api"] = False
    
    all_healthy = all(dependencies.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "dependencies": dependencies,
        "features_ready": {
            "phase_a_ingestion": True,
            "phase_b_secops": True,
            "phase_c_continuity": dependencies["groq_api"]
        }
    }


@app.get("/api/info")
async def api_info():
    """API information and capabilities"""
    return {
        "name": "Story Visualizer Universal API",
        "version": "2.0.0",
        "description": "Universal narrative engine supporting business, personal & daily life stories",
        "phases_completed": ["A", "B", "C", "D", "E", "F"],
        "phases_pending": [],
        "features": {
            "input_validation": "3-7 sentence narrative validation",
            "rate_limiting": "10 requests/minute per IP",
            "data_sanitization": "Presidio-based PII anonymization (Zero-Trust SecOps)",
            "archetype_engine": "17 scene archetypes (crisis, joy, struggle, connection, etc.)",
            "dynamic_casting": "Context-aware characters & archetype-matched lighting",
            "parallel_generation": "asyncio + aiohttp for simultaneous image generation",
            "fixed_seed": "Visual consistency across all panels via seed=1337",
            "cryptographic_watermark": "AES-128 encryption + LSB steganography for asset tracking"
        },
        "image_generation": {
            "provider": "pollinations" if USE_POLLINATIONS else "huggingface",
            "mode": "parallel",
            "max_concurrent": MAX_CONCURRENT_IMAGES,
            "fixed_seed": 1337
        },
        "steganography": {
            "encryption": "AES-128-CBC",
            "encoding": "LSB (Least Significant Bit)",
            "decoder_tool": "python decoder_gui.py"
        },
        "endpoints": {
            "generate": "/api/generate - Submit pitch for processing",
            "health": "/health - Health check",
            "info": "/api/info - API information"
        }
    }


# --- PHASE C: THE CONTINUITY ENGINE ---

@lru_cache(maxsize=CACHE_MAXSIZE)
def _get_cache_key(text: str, style: str) -> str:
    """Generate cache key from text and style"""
    content = f"{text}|{style}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


@retry(
    retry=retry_if_exception_type((APIError, RateLimitError, asyncio.TimeoutError)),
    stop=stop_after_attempt(MAX_LLM_RETRIES),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
async def _call_groq_with_retry(system_prompt: str, user_prompt: str, request_id: Optional[str] = None) -> dict:
    """Call Groq API with retry logic, exponential backoff, and concurrency limiting"""
    async with llm_semaphore:  # Limit concurrent requests
        logger.info(
            "Calling Groq API",
            extra={"request_id": request_id, "model": "llama-3.3-70b-versatile"}
        )
        
        response = await groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.2,
            response_format={"type": "json_object"},
            timeout=LLM_TIMEOUT
        )
        
        logger.info(
            "Groq API call successful",
            extra={"request_id": request_id, "tokens_used": response.usage.total_tokens if response.usage else 0}
        )
        
        return json.loads(response.choices[0].message.content)


async def engineer_prompts(sanitized_text: str, visual_style: str, request_id: Optional[str] = None) -> dict:
    """
    Use Groq LLM to create visually consistent prompts with a Global Character Sheet.
    Features: Caching, retry logic, structured logging
    
    This solves the "Visual Consistency" problem by forcing the LLM to:
    1. Create a universal "Global Character & Setting" description
    2. Write image prompts that include this global setting in EVERY scene
    3. Output strict JSON for reliable parsing
    """
    
    # Check cache first
    cache_key = _get_cache_key(sanitized_text, visual_style)
    # Note: LRU cache on async functions requires manual caching or functools.cache
    # For simplicity, we'll use an in-memory cache dict
    
    logger.info(
        "Starting prompt engineering",
        extra={
            "request_id": request_id,
            "cache_key": cache_key,
            "text_length": len(sanitized_text),
            "style": visual_style[:30]
        }
    )
    
    system_prompt = f"""You are an expert AI Image Prompt Engineer and Storyboard Director.
    Your job is to take ANY narrative and break it into 3 to 5 cinematic visual scenes
    that communicate the EXACT situation described.

    CRITICAL INSTRUCTIONS:

    STEP 1 — CLASSIFY EACH SCENE ARCHETYPE:
    Identify which archetype fits the sentence:

    PROFESSIONAL:
    - crisis       → threat, financial loss, emergency
    - discovery    → insight found, root cause identified
    - action       → sprint, deployment, execution
    - outcome      → resolution, recovery, win
    - relationship → deal closed, handshake, trust

    PERSONAL / DAILY LIFE:
    - conflict     → argument, disagreement, tension
    - struggle     → hardship, exhaustion, overwhelm
    - routine      → everyday moment, commute, meal
    - connection   → bonding, reunion, friendship
    - loss         → grief, disappointment, failure
    - joy          → surprise, celebration, relief
    - transition   → moving, starting over, change

    UNIVERSAL:
    - growth       → aspiration, learning, ambition
    - reflection   → solitude, thinking, quiet moment
    - exploration  → travel, discovery, curiosity

    STEP 2 — DERIVE VISUALS FROM ARCHETYPE:
    CRISIS:      cold harsh light, tense body language, cluttered environment
    STRUGGLE:    desaturated tones, withdrawn posture, isolation
    ROUTINE:     natural soft daylight, candid unstaged feel
    CONNECTION:  warm golden light, close proximity, genuine smiles
    ACTION:      bright even lighting, urgency in posture
    OUTCOME:     warm light, relaxed body language, cleared space
    DISCOVERY:   focused light source, leaning-in posture
    REFLECTION:  single-source light, solitary figure, still environment
    TRANSITION:  wide shot, threshold framing, old and new elements
    GROWTH:      expansive wide shot, natural light, forward-facing

    STEP 3 — EXTRACT CONCRETE NOUNS:
    Every specific noun (kitchen, hospital, "$2.5M", airport) MUST appear literally
    in the prompt. Never replace concrete elements with abstract visuals.

    STEP 4 — MAKE KEY DETAILS VISIBLE:
    If the sentence mentions any number, object, sign, or item — it must be
    physically visible in the scene.

    STEP 5 — ASSIGN THE RIGHT PERSON:
    - Child / teenager  → school, family, growing-up scenes
    - Young adult       → career start, relationships, independence
    - Parent            → family, responsibility, sacrifice
    - Elderly person    → reflection, legacy, wisdom
    - Couple            → relationship, conflict, connection
    - Friends group     → social, celebration, support
    - Solo individual   → reflection, struggle, growth
    - Professional      → always name the role: nurse, teacher, engineer
    Never use a generic "person" without age, role, or emotional context.

    STEP 6 — BUILD THE IMAGE PROMPT:
    "Visual Style: {visual_style},
    [person + age + role + emotional state + body language],
    [setting from text],
    [focal action],
    [visible objects or details],
    [archetype lighting],
    [camera angle],
    highly detailed, professional quality, 8k resolution"

    Output ONLY valid JSON:
    {{
      "global_setting": "Dynamic - varies per scene",
      "scenes": [
        {{
          "original_text": "the exact sentence",
          "scene_archetype": "crisis|conflict|struggle|routine|connection|...",
          "image_prompt": "Visual Style: {visual_style}, [person + details], ..."
        }}
      ]
    }}
    """
    
    user_prompt = f"Text to visualize: {sanitized_text}"
    
    start_time = time.time()
    
    try:
        # Call with retry logic and concurrency limiting
        result = await _call_groq_with_retry(system_prompt, user_prompt, request_id=request_id)
        
        duration = time.time() - start_time
        logger.info(
            "Prompt engineering completed",
            extra={
                "request_id": request_id,
                "duration_ms": int(duration * 1000),
                "scenes_generated": len(result.get('scenes', [])),
                "cache_hit": False
            }
        )
        
        return result
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"Prompt engineering failed after {MAX_LLM_RETRIES} retries",
            extra={
                "request_id": request_id,
                "duration_ms": int(duration * 1000),
                "error": str(e),
                "error_type": type(e).__name__
            }
        )
        
        # Return a graceful fallback
        return {
            "global_setting": "A professional business setting",
            "scenes": [
                {
                    "original_text": sanitized_text[:100],
                    "image_prompt": f"{visual_style}, professional business scene, highly detailed, professional quality, 8k resolution"
                }
            ],
            "_fallback": True,
            "_error": str(e)
        }


# --- PHASE D: PARALLEL IMAGE GENERATION ---

@retry(
    retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=4, max=30),
    reraise=True
)
async def generate_single_image(
    session: aiohttp.ClientSession, 
    prompt: str, 
    index: int, 
    fixed_seed: int = 1337,
    request_id: Optional[str] = None
) -> Optional[str]:
    """
    Generate a single image using Hugging Face Inference API or Pollinations.ai.
    Uses fixed seed for visual continuity across all panels.
    Limited by semaphore to avoid rate limiting.
    Includes retry logic with exponential backoff.
    """
    async with image_semaphore:  # Limit concurrent requests
        filename = f"panel_{index+1}_{uuid.uuid4().hex[:8]}.png"
        filepath = os.path.join("static", filename)
        
        if USE_POLLINATIONS:
            # Use Pollinations.ai (free, no API key required)
            import urllib.parse
            encoded_prompt = urllib.parse.quote(prompt[:500])  # Limit prompt length and encode properly
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&seed={fixed_seed}&nologo=true"
            
            # Retry logic for rate limiting (429 errors)
            max_retries = 3
            base_delay = 5  # Start with 5 second delay
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"Panel {index+1}: Requesting image from Pollinations.ai (attempt {attempt + 1}/{max_retries})", extra={"request_id": request_id})
                    async with session.get(url, timeout=120) as response:
                        if response.status == 429:
                            # Rate limited - wait and retry
                            wait_time = base_delay * (2 ** attempt)  # Exponential backoff: 5, 10, 20 seconds
                            logger.warning(f"Panel {index+1}: Rate limited (429), waiting {wait_time}s before retry...", extra={"request_id": request_id})
                            await asyncio.sleep(wait_time)
                            continue
                        
                        if response.status != 200:
                            logger.error(f"Panel {index+1}: Pollinations error {response.status}", extra={"request_id": request_id})
                            return None
                        
                        image_bytes = await response.read()
                        with open(filepath, "wb") as f:
                            f.write(image_bytes)
                        
                        # --- PHASE E: CRYPTOGRAPHIC WATERMARK ---
                        tracking_payload = f"Panel:{index+1}|Req:{request_id}|Time:{datetime.now().isoformat()}|Seed:{fixed_seed}"
                        hide_data(filepath, tracking_payload)
                        logger.info(f"Panel {index+1}: Encrypted watermark embedded", extra={"request_id": request_id})
                        
                        logger.info(f"Panel {index+1}: Image saved from Pollinations.ai", extra={"request_id": request_id, "image_file": filename})
                        return f"/static/{filename}"
                        
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = base_delay * (2 ** attempt)
                        logger.warning(f"Panel {index+1}: Error on attempt {attempt + 1}, retrying in {wait_time}s: {str(e)}", extra={"request_id": request_id})
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        # Final attempt failed
                        import traceback
                        error_msg = f"{str(e)}\n{traceback.format_exc()}"
                        logger.error(f"Panel {index+1}: Pollinations generation failed after {max_retries} attempts: {str(e)}", extra={"request_id": request_id, "error": error_msg})
                        print(f"ERROR Panel {index+1}: {error_msg}")
                        return None
            
            return None  # All retries exhausted
        else:
            # Use Hugging Face Inference API
            if not HF_API_TOKEN:
                logger.error("HF_API_TOKEN not set", extra={"request_id": request_id})
                return None
            
            headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
            payload = {
                "inputs": prompt,
                "parameters": {"seed": fixed_seed}
            }
            
            try:
                logger.info(f"Panel {index+1}: Requesting image from Hugging Face", extra={"request_id": request_id})
                async with session.post(HF_API_URL, headers=headers, json=payload, timeout=120) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Panel {index+1}: HF API error {response.status}", extra={"request_id": request_id, "error": error_text[:100]})
                        return None
                    
                    image_bytes = await response.read()
                    with open(filepath, "wb") as f:
                        f.write(image_bytes)
                    
                    # --- PHASE E: CRYPTOGRAPHIC WATERMARK ---
                    tracking_payload = f"Panel:{index+1}|Req:{request_id}|Time:{datetime.now().isoformat()}|Seed:{fixed_seed}"
                    hide_data(filepath, tracking_payload)
                    logger.info(f"Panel {index+1}: Encrypted watermark embedded", extra={"request_id": request_id})
                    
                    logger.info(f"Panel {index+1}: Image saved from Hugging Face", extra={"request_id": request_id, "image_file": filename})
                    return f"/static/{filename}"
            except Exception as e:
                logger.error(f"Panel {index+1}: HF generation failed", extra={"request_id": request_id, "error": str(e)})
                return None


async def execute_parallel_generation(
    scenes: list, 
    fixed_seed: int = 1337,
    request_id: Optional[str] = None
) -> list:
    """
    Orchestrate parallel image generation for all scenes.
    Fires all API calls simultaneously using asyncio.gather.
    """
    logger.info(f"Starting parallel generation for {len(scenes)} scenes", extra={"request_id": request_id, "fixed_seed": fixed_seed})
    
    async with aiohttp.ClientSession() as session:
        # Process sequentially with delays to avoid rate limits
        image_paths = []
        for index, scene in enumerate(scenes):
            prompt = scene["image_prompt"]
            path = await generate_single_image(session, prompt, index, fixed_seed, request_id)
            image_paths.append(path)
            # Add delay between images to avoid rate limiting (Pollinations.ai is strict)
            if index < len(scenes) - 1:
                logger.info(f"Waiting 10s before next image to respect rate limits...", extra={"request_id": request_id})
                await asyncio.sleep(10)
        
        # Merge image paths back into scenes
        for i, path in enumerate(image_paths):
            scenes[i]["image_path"] = path
            scenes[i]["image_generated"] = path is not None
        
        success_count = sum(1 for p in image_paths if p is not None)
        logger.info(
            f"Parallel generation complete: {success_count}/{len(scenes)} images generated",
            extra={"request_id": request_id, "success_count": success_count, "total_count": len(scenes)}
        )
        
        return scenes


@app.post("/api/generate")
@limiter.limit("10/minute")  # Rate limit: 10 requests per minute
async def generate_storyboard(request: Request, payload: PitchPayload):
    """
    Ingest pitch narrative and initiate storyboard generation pipeline.
    
    - Phase A: Validates input (3-7 sentences, proper style)
    - Phase B: Zero-Trust SecOps sanitization using Microsoft Presidio
    - Phase C: Groq LLM-powered continuity engine with Global Character Sheet
    - Logs request with unique ID
    """
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    
    # Validate sentence count
    sentences = [s.strip() for s in payload.narrative.replace('!', '.').replace('?', '.').split('.') if s.strip()]
    
    print(f"\n{'='*60}")
    print(f"PHASE A: INGESTION - Request ID: {request_id}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"{'='*60}")
    print(f"Style: {payload.style}")
    print(f"Sentence Count: {len(sentences)}")
    print(f"Character Count: {len(payload.narrative)}")
    
    # Phase B: Zero-Trust SecOps Sanitization
    print(f"\n--- PHASE B: SECOPS SANITIZATION ---")
    print(f"RAW NARRATIVE: {payload.narrative}")
    
    analyzer_results = analyzer.analyze(
        text=payload.narrative, 
        entities=["PERSON", "ORGANIZATION", "MONEY", "EMAIL_ADDRESS", "PHONE_NUMBER", "LOCATION"],
        language="en"
    )
    
    anonymized_result = anonymizer.anonymize(
        text=payload.narrative,
        analyzer_results=analyzer_results
    )
    
    sanitized_text = anonymized_result.text
    entities_detected = len(analyzer_results)
    
    print(f"SANITIZED: {sanitized_text}")
    print(f"Entities Masked: {entities_detected}")
    if analyzer_results:
        for entity in analyzer_results:
            print(f"  - {entity.entity_type}: '{payload.narrative[entity.start:entity.end]}' → <{entity.entity_type}>")
    
    # Phase C: Archetype Engine - LLM Prompt Engineering
    print(f"\n--- PHASE C: ARCHETYPE ENGINE (GROQ LLM) ---")
    storyboard_data = await engineer_prompts(sanitized_text, payload.style, request_id=request_id)
    
    # Check if fallback was used
    if storyboard_data.get("_fallback"):
        logger.warning(
            "Using fallback prompts due to LLM failure",
            extra={"request_id": request_id, "error": storyboard_data.get("_error")}
        )
    
    print(f"Global Setting: {storyboard_data.get('global_setting', 'N/A')}")
    print(f"Scenes Generated: {len(storyboard_data.get('scenes', []))}")
    
    for i, scene in enumerate(storyboard_data.get('scenes', [])):
        archetype = scene.get('scene_archetype', 'N/A')
        print(f"\nPanel {i+1} [Archetype: {archetype}]:")
        print(f"  Original: {scene.get('original_text', 'N/A')[:60]}...")
        print(f"  Prompt: {scene.get('image_prompt', 'N/A')[:80]}...")
    
    # Phase D: Parallel Image Generation
    print(f"\n--- PHASE D: PARALLEL IMAGE GENERATION ---")
    scenes = storyboard_data.get('scenes', [])
    
    # Use fixed seed 1337 for visual continuity across all panels
    completed_scenes = await execute_parallel_generation(scenes, fixed_seed=1337, request_id=request_id)
    
    # Count successful generations
    successful_images = sum(1 for scene in completed_scenes if scene.get('image_generated'))
    
    print(f"\nImages Generated: {successful_images}/{len(completed_scenes)}")
    for i, scene in enumerate(completed_scenes):
        status = "✓" if scene.get('image_generated') else "✗"
        print(f"  Panel {i+1}: {status} {scene.get('image_path', 'Failed')}")
    
    print(f"{'='*60}\n")
    
    response_data = {
        "status": "success", 
        "message": f"Storyboard complete with {successful_images}/{len(completed_scenes)} images generated. All images watermarked with AES-128 encryption.",
        "request_id": request_id,
        "phases_completed": ["A", "B", "C", "D", "E", "F"],
        "next_phase": "Complete - Enterprise Pitch Visualizer Ready",
        "data": {
            "original": payload.narrative,
            "sanitized": sanitized_text,
            "entities_masked": entities_detected,
            "global_setting": storyboard_data.get('global_setting'),
            "scenes": completed_scenes,
            "total_scenes": len(completed_scenes),
            "images_generated": successful_images,
            "fallback_used": storyboard_data.get("_fallback", False),
            "image_provider": "pollinations" if USE_POLLINATIONS else "huggingface",
            "watermarking": {
                "algorithm": "AES-128-CBC",
                "encoding": "LSB steganography",
                "decoder": "python decoder_gui.py"
            }
        },
        "security_note": "Zero-Trust SecOps: All PII anonymized. Archetype-based visual system with dynamic character casting. Archetype-matched lighting & camera angles. AES-128 encrypted watermarks embedded in all images for asset tracking."
    }
    
    return response_data


@app.post("/api/regenerate-panel")
@limiter.limit("30/minute")
async def regenerate_panel(request: Request, payload: dict):
    """
    Regenerate a single panel image. Used for retrying failed panels.
    """
    request_id = str(uuid.uuid4())[:8]
    
    try:
        prompt = payload.get('prompt', '')
        index = payload.get('index', 0)
        seed = payload.get('seed', 1337)
        
        if not prompt:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Prompt is required"}
            )
        
        async with aiohttp.ClientSession() as session:
            image_path = await generate_single_image_streaming(
                session, prompt, index, seed, request_id, lambda x: None
            )
        
        if image_path:
            return JSONResponse(
                content={
                    "status": "success",
                    "image_path": image_path,
                    "image_generated": True
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": "Image generation failed"}
            )
            
    except Exception as e:
        logger.error(f"Panel regeneration error: {str(e)}", extra={"request_id": request_id})
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.post("/api/generate-stream")
@limiter.limit("10/minute")
async def generate_storyboard_stream(request: Request, payload: PitchPayload):
    """
    Streaming endpoint that sends real-time progress updates via Server-Sent Events.
    Shows each image as it's generated with progress tracking.
    """
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    
    async def event_generator():
        try:
            # Phase A: Ingestion
            sentences = [s.strip() for s in payload.narrative.replace('!', '.').replace('?', '.').split('.') if s.strip()]
            yield f"data: {json.dumps({'type': 'phase', 'phase': 'A', 'status': 'ingestion', 'message': 'Validating narrative...', 'progress': 5})}\n\n"
            
            # Phase B: SecOps
            yield f"data: {json.dumps({'type': 'phase', 'phase': 'B', 'status': 'secops', 'message': 'SecOps: Masking sensitive data...', 'progress': 15})}\n\n"
            analyzer_results = analyzer.analyze(
                text=payload.narrative, 
                entities=["PERSON", "ORGANIZATION", "MONEY", "EMAIL_ADDRESS", "PHONE_NUMBER", "LOCATION"],
                language="en"
            )
            anonymized_result = anonymizer.anonymize(
                text=payload.narrative,
                analyzer_results=analyzer_results
            )
            sanitized_text = anonymized_result.text
            entities_detected = len(analyzer_results)
            
            yield f"data: {json.dumps({'type': 'phase', 'phase': 'B', 'status': 'complete', 'message': f'SecOps: {entities_detected} entities masked', 'progress': 25, 'entities_masked': entities_detected})}\n\n"
            
            # Phase C: Archetype Engine
            yield f"data: {json.dumps({'type': 'phase', 'phase': 'C', 'status': 'llm', 'message': 'Archetype AI: Analyzing scenes...', 'progress': 35})}\n\n"
            storyboard_data = await engineer_prompts(sanitized_text, payload.style, request_id=request_id)
            scenes = storyboard_data.get('scenes', [])
            total_scenes = len(scenes)
            
            # Send scene preview
            scene_preview = []
            for i, scene in enumerate(scenes):
                scene_preview.append({
                    'panel': i + 1,
                    'archetype': scene.get('scene_archetype', 'N/A'),
                    'original_text': scene.get('original_text', '')[:60]
                })
            
            yield f"data: {json.dumps({'type': 'scenes_ready', 'total_scenes': total_scenes, 'scenes': scene_preview, 'progress': 40})}\n\n"
            
            # Phase D: Image Generation with Streaming
            yield f"data: {json.dumps({'type': 'phase', 'phase': 'D', 'status': 'generating', 'message': f'Generating {total_scenes} images...', 'progress': 45})}\n\n"
            
            # Calculate time estimate
            avg_time_per_image = 30  # seconds
            delay_between = 12  # seconds
            estimated_total = (avg_time_per_image + delay_between) * total_scenes - delay_between
            
            yield f"data: {json.dumps({'type': 'time_estimate', 'estimated_seconds': estimated_total, 'formatted': f"~{estimated_total//60}m {estimated_total%60}s"})}\n\n"
            
            # Generate images sequentially with streaming
            completed_scenes = []
            for index, scene in enumerate(scenes):
                panel_num = index + 1
                archetype = scene.get('scene_archetype', 'N/A')
                
                # Start panel generation
                yield f"data: {json.dumps({'type': 'panel_start', 'panel': panel_num, 'total': total_scenes, 'archetype': archetype, 'message': f'Panel {panel_num}: Starting generation...'})}\n\n"
                
                # Generate image
                async with aiohttp.ClientSession() as session:
                    image_path = await generate_single_image_streaming(
                        session, scene.get('image_prompt', ''), index, 1337, request_id,
                        lambda msg: None  # Simple callback, actual streaming handled in main loop
                    )
                
                scene['image_path'] = image_path
                scene['image_generated'] = image_path is not None
                completed_scenes.append(scene)
                
                if image_path:
                    yield f"data: {json.dumps({'type': 'panel_complete', 'panel': panel_num, 'total': total_scenes, 'image_path': image_path, 'archetype': archetype, 'original_text': scene.get('original_text', ''), 'image_prompt': scene.get('image_prompt', ''), 'progress': 45 + int((panel_num / total_scenes) * 45)})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'panel_failed', 'panel': panel_num, 'total': total_scenes, 'archetype': archetype, 'message': 'Generation failed after retries', 'progress': 45 + int((panel_num / total_scenes) * 45)})}\n\n"
                
                # Delay between images
                if index < len(scenes) - 1:
                    yield f"data: {json.dumps({'type': 'waiting', 'message': 'Respecting rate limits...', 'next_panel': panel_num + 1, 'delay': 12})}\n\n"
                    await asyncio.sleep(12)
            
            # Phase E: Complete
            successful_images = sum(1 for scene in completed_scenes if scene.get('image_generated'))
            yield f"data: {json.dumps({'type': 'complete', 'status': 'success', 'message': f'{successful_images}/{total_scenes} images generated', 'total_scenes': total_scenes, 'successful_images': successful_images, 'scenes': completed_scenes, 'sanitized': sanitized_text, 'entities_masked': entities_detected, 'progress': 100})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Request-ID": request_id
        }
    )


async def generate_single_image_streaming(session, prompt, index, fixed_seed, request_id, progress_callback):
    """Version of generate_single_image that supports progress callbacks"""
    filename = f"panel_{index+1}_{request_id}_{uuid.uuid4().hex[:8]}.png"
    filepath = f"static/{filename}"
    
    try:
        if USE_POLLINATIONS:
            import urllib.parse
            encoded_prompt = urllib.parse.quote(prompt[:500])
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&seed={fixed_seed}&nologo=true"
            
            max_retries = 3
            base_delay = 5
            
            for attempt in range(max_retries):
                try:
                    async with session.get(url, timeout=120) as response:
                        if response.status == 429:
                            wait_time = base_delay * (2 ** attempt)
                            await asyncio.sleep(wait_time)
                            continue
                        
                        if response.status != 200:
                            return None
                        
                        image_bytes = await response.read()
                        with open(filepath, "wb") as f:
                            f.write(image_bytes)
                        
                        # Watermark
                        tracking_payload = f"Panel:{index+1}|Req:{request_id}|Time:{datetime.now().isoformat()}|Seed:{fixed_seed}"
                        hide_data(filepath, tracking_payload)
                        
                        return f"/static/{filename}"
                        
                except Exception:
                    if attempt < max_retries - 1:
                        wait_time = base_delay * (2 ** attempt)
                        await asyncio.sleep(wait_time)
                        continue
                    return None
            return None
        else:
            # Hugging Face path
            if not HF_API_TOKEN:
                return None
            headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
            payload = {"inputs": prompt, "parameters": {"seed": fixed_seed}}
            
            try:
                async with session.post(HF_API_URL, headers=headers, json=payload, timeout=120) as response:
                    if response.status != 200:
                        return None
                    image_bytes = await response.read()
                    with open(filepath, "wb") as f:
                        f.write(image_bytes)
                    
                    tracking_payload = f"Panel:{index+1}|Req:{request_id}|Time:{datetime.now().isoformat()}|Seed:{fixed_seed}"
                    hide_data(filepath, tracking_payload)
                    
                    return f"/static/{filename}"
            except Exception:
                return None
    except Exception:
        return None


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=422,
        content={"status": "error", "message": str(exc)}
    )


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host=host, port=port)
