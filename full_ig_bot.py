"""
=====================================================================
 Anime Style IG Auto-Poster — Full Integrated Script
=====================================================================
 - Image generation: Hugging Face Inference API (free tier)
 - Posting: Instagram Graph API
 - Deployment: Railway-ready (reads config from environment variables)
 - Prompts: built-in, SFW, vibe-based (no copyrighted characters)

 GUARDRAILS (do not remove):
 - Every prompt must stay SFW — modest/fully-covered clothing, no
   suggestive framing. NEGATIVE_PROMPT enforces this at generation time.
 - No copyrighted character/series names in prompts or hashtags.
 - Keep posting frequency reasonable (few posts/day) to avoid spam flags.
=====================================================================
"""

import os
import io
import time
import random
import requests
from datetime import datetime, timezone

# ============================================================
# 0. CONFIG — set these as environment variables on Railway
#    (Railway dashboard -> Project -> Variables)
# ============================================================
HF_API_TOKEN = os.environ["HF_API_TOKEN"]          # Hugging Face token
HF_MODEL = os.environ.get(
    "HF_MODEL", "cagliostrolab/animagine-xl-3.1"
)  # anime-style model on HF

IG_USER_ID = os.environ["IG_USER_ID"]               # Instagram business account ID
IG_ACCESS_TOKEN = os.environ["IG_ACCESS_TOKEN"]      # long-lived Graph API token
GRAPH_API_VERSION = "v19.0"

# Where generated images get uploaded so Instagram can fetch a public URL.
# Instagram's API needs a PUBLIC image URL — it cannot accept raw bytes.
# Easiest free option: a Railway-hosted static file route, or an S3/
# Cloudinary bucket. Set this to whatever public base URL you use.
PUBLIC_UPLOAD_BASE_URL = os.environ.get(
    "PUBLIC_UPLOAD_BASE_URL", "https://your-public-host.example.com/images"
)

POST_INTERVAL_HOURS = float(os.environ.get("POST_INTERVAL_HOURS", "6"))

# ============================================================
# 1. PROMPTS — SFW, vibe-based, no copyrighted characters
#    Edit / add to this list any time.
# ============================================================
FULL_PROMPTS = [
    "masterpiece, best quality, ultra detailed, anime style illustration, "
    "1girl, short black hair with soft bangs, warm brown eyes, gentle "
    "smile, wearing a traditional red kimono with floral embroidery, "
    "standing under a blooming cherry blossom tree, night setting with "
    "soft moonlight, cinematic lighting, full body shot, calm peaceful "
    "mood, modest fully-covered clothing, clean background, high detail "
    "linework, soft color palette",

    "masterpiece, best quality, ultra detailed, anime style illustration, "
    "1girl, blonde bob haircut, blue eyes, relaxed expression, wearing an "
    "oversized cream sweater and long pleated skirt, sitting by a cafe "
    "window with a cup of coffee, warm golden afternoon light streaming "
    "in, medium shot, cozy indoor atmosphere, modest fully-covered "
    "clothing, soft shadows, warm color grading",

    "masterpiece, best quality, ultra detailed, anime style illustration, "
    "1girl, long silver hair tied loosely, sharp green eyes, cheerful "
    "expression, wearing a school uniform blazer with pleated skirt and "
    "knee-high socks, walking through an autumn park with falling maple "
    "leaves, golden hour lighting, full body shot, dynamic wind motion in "
    "hair and leaves, modest fully-covered clothing",

    "masterpiece, best quality, ultra detailed, anime style illustration, "
    "1girl, short orange hair, amber eyes, soft smile, wearing a long "
    "maid-style dress with white apron, fully covered long sleeves and "
    "high collar, standing near a stone fireplace in a rustic wooden "
    "cottage, warm firelight glow, medium shot, cozy rustic atmosphere, "
    "modest fully-covered clothing, detailed wood textures",

    "masterpiece, best quality, ultra detailed, anime style illustration, "
    "1girl, brown hair in a high ponytail, energetic expression, wearing "
    "a zip-up hoodie and jogger pants, running pose in a city park at "
    "sunrise, soft morning mist, dynamic action pose, full body shot, "
    "sporty modest outfit, warm sunrise color palette",

    "masterpiece, best quality, ultra detailed, anime style illustration, "
    "1girl, teal shoulder-length hair, calm expression, wearing a long "
    "wool winter coat with a scarf and gloves, standing on a snow-covered "
    "street at night with warm cafe lights in the background, soft "
    "falling snow, medium shot, modest fully-covered clothing, cool blue "
    "and warm light contrast",

    "masterpiece, best quality, ultra detailed, anime style illustration, "
    "1girl, pink twin tails, playful expression, wearing a casual hoodie "
    "dress with leggings, sitting on a rooftop ledge overlooking a city "
    "skyline at sunset, relaxed pose, wide shot, warm orange and purple "
    "sky gradient, modest fully-covered clothing",

    "masterpiece, best quality, ultra detailed, anime style illustration, "
    "1girl, dark green hair in a loose braid, joyful expression, wearing "
    "a traditional summer yukata with obi sash, standing near glowing "
    "paper lanterns at a night festival, warm lantern light reflections, "
    "full body shot, modest fully-covered clothing, festive atmosphere, "
    "detailed background crowd bokeh",

    "masterpiece, best quality, ultra detailed, anime style illustration, "
    "1girl, wavy auburn hair, thoughtful expression, wearing a cozy "
    "oversized cardigan over a turtleneck and long skirt, sitting cross-"
    "legged reading a book in a quiet library, warm indoor lamp lighting, "
    "medium shot, modest fully-covered clothing, soft bokeh bookshelves "
    "in background",

    "masterpiece, best quality, ultra detailed, anime style illustration, "
    "1girl, short lavender hair, serene expression, wearing a long "
    "raincoat over a sweater with rain boots, holding an umbrella, "
    "walking down a rainy neon-lit street at night, reflections on wet "
    "pavement, full body shot, modest fully-covered clothing, moody cool "
    "color palette with neon accents",

    "masterpiece, best quality, ultra detailed, anime style illustration, "
    "1girl, long black hair in twin braids, warm friendly expression, "
    "wearing farmer-style overalls over a long-sleeve shirt, standing in "
    "a golden sunflower field under a clear blue sky, daytime lighting, "
    "full body shot, modest fully-covered clothing, vibrant natural "
    "colors",

    "masterpiece, best quality, ultra detailed, anime style illustration, "
    "1girl, short white hair, cozy relaxed expression, wearing a thick "
    "winter sweater with a long skirt and tights, sitting by a fireplace "
    "holding a mug of hot cocoa, warm ambient firelight, medium shot, "
    "modest fully-covered clothing, soft cozy color grading",
]

NEGATIVE_PROMPT = (
    "nsfw, nude, naked, sexual, suggestive, revealing clothes, exposed "
    "skin, underwear, swimsuit, bad anatomy, bad hands, extra limbs, "
    "deformed, low quality, blurry, watermark, signature, text, logo"
)

CAPTION_TEMPLATES = [
    "Just vibes ✨🍁",
    "A quiet moment in an anime world 🌸",
    "Slice of life aesthetic 🎐",
    "Soft colors, soft mood 🌙",
    "Another day, another scene 🎨",
]

HASHTAG_POOL = [
    "#anime", "#animeart", "#animegirl", "#animeaesthetic", "#aiart",
    "#digitalart", "#animestyle", "#artwork", "#conceptart", "#illustration",
    "#fanart", "#aiartcommunity", "#animelover", "#otaku", "#mangaart",
]


def build_caption() -> str:
    caption = random.choice(CAPTION_TEMPLATES)
    hashtags = " ".join(random.sample(HASHTAG_POOL, k=8))
    return f"{caption}\n\n{hashtags}"


# ============================================================
# 2. IMAGE GENERATION — Hugging Face Inference API
# ============================================================
def generate_image(prompt: str, save_path: str) -> str:
    url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "negative_prompt": NEGATIVE_PROMPT,
            "num_inference_steps": 30,
            "guidance_scale": 7,
        },
    }

    # HF free tier can "cold start" the model — retry a few times.
    for attempt in range(5):
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image"):
            with open(save_path, "wb") as f:
                f.write(resp.content)
            return save_path
        elif resp.status_code == 503:
            # model loading — wait and retry
            wait = resp.json().get("estimated_time", 20)
            print(f"[i] Model loading, waiting {wait}s...")
            time.sleep(wait)
        else:
            resp.raise_for_status()

    raise RuntimeError("Failed to generate image after retries")


# ============================================================
# 3. UPLOAD IMAGE SOMEWHERE PUBLIC
#    Instagram needs a public URL. This example assumes you're
#    serving files from a `public/` folder on your Railway app
#    (e.g. via a simple Flask/FastAPI static route). Adjust to
#    match whatever public host you actually use.
# ============================================================
def save_for_public_access(local_path: str, public_dir: str = "public") -> str:
    os.makedirs(public_dir, exist_ok=True)
    filename = os.path.basename(local_path)
    dest = os.path.join(public_dir, filename)
    if local_path != dest:
        with open(local_path, "rb") as src, open(dest, "wb") as dst:
            dst.write(src.read())
    return f"{PUBLIC_UPLOAD_BASE_URL}/{filename}"


# ============================================================
# 4. INSTAGRAM GRAPH API POSTING
# ============================================================
def post_to_instagram(image_url: str, caption: str) -> dict:
    base = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{IG_USER_ID}"

    container_resp = requests.post(
        f"{base}/media",
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": IG_ACCESS_TOKEN,
        },
    )
    container_resp.raise_for_status()
    creation_id = container_resp.json()["id"]

    publish_resp = requests.post(
        f"{base}/media_publish",
        data={
            "creation_id": creation_id,
            "access_token": IG_ACCESS_TOKEN,
        },
    )
    publish_resp.raise_for_status()
    return publish_resp.json()


# ============================================================
# 5. ONE FULL POST CYCLE
# ============================================================
def run_once():
    prompt = random.choice(FULL_PROMPTS)
    caption = build_caption()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    local_path = f"post_{timestamp}.jpg"

    print(f"[+] Generating image for prompt: {prompt[:60]}...")
    generate_image(prompt, local_path)

    public_url = save_for_public_access(local_path)
    print(f"[+] Public URL: {public_url}")

    result = post_to_instagram(public_url, caption)
    print(f"[+] Posted to Instagram: {result}")


# ============================================================
# 6. MAIN LOOP — Railway will run this as a long-lived process
# ============================================================
if __name__ == "__main__":
    print("[i] Anime IG Auto-Poster starting...")
    print(f"[i] Posting every {POST_INTERVAL_HOURS} hours")

    while True:
        try:
            run_once()
        except Exception as e:
            print(f"[!] Error during post cycle: {e}")

        time.sleep(POST_INTERVAL_HOURS * 60 * 60)
