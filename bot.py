import os
import random
import time
import requests
from datetime import datetime
from PIL import Image
from huggingface_hub import InferenceClient

# --- CONFIGURATION (Environment Variables from GitHub Secrets) ---
IG_USER_ID = os.getenv("IG_USER_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

# --- STEP 1: RANDOM PROMPT BUILDER COMPONENTS ---
BASE_QUALITY = "masterpiece, best quality, ultra detailed, 8k resolution, 4k wallpaper, sharp focus, aesthetic, anime style illustration, 1girl"

HAIR_STYLES = [
    "short hair with soft bangs", "blonde bob haircut", "long hair tied loosely",
    "high ponytail", "shoulder-length hair", "twin tails", "hair in a loose braid",
    "wavy hair", "twin braids"
]

HAIR_COLORS = [
    "black hair", "blonde hair", "silver hair", "orange hair", "brown hair",
    "teal hair", "pink hair", "dark green hair", "auburn hair", "lavender hair", "white hair"
]

DRESSES = [
    "wearing a traditional red kimono with floral embroidery",
    "wearing an oversized cream sweater and long pleated skirt",
    "wearing a school uniform blazer with pleated skirt",
    "wearing a long maid-style dress with white apron",
    "wearing a zip-up hoodie and jogger pants",
    "wearing a long wool winter coat with a scarf and gloves",
    "wearing a casual hoodie dress with leggings",
    "wearing a traditional summer yukata with obi sash",
    "wearing a cozy oversized cardigan over a turtleneck"
]

POSES_AND_SETTINGS = [
    "standing under a blooming cherry blossom tree at night with soft moonlight, vertical portrait shot",
    "sitting by a cafe window with a cup of coffee, cozy indoor atmosphere, vertical portrait shot",
    "walking through an autumn park with falling maple leaves, golden hour lighting, full body portrait",
    "standing near a stone fireplace in a rustic wooden cottage, warm firelight glow, vertical shot",
    "running pose in a city park at sunrise, soft morning mist, dynamic action pose, full body shot",
    "standing on a snow-covered street at night with warm cafe lights, soft falling snow, vertical shot",
    "sitting on a rooftop ledge overlooking a city skyline at sunset, vertical angle",
    "standing near glowing paper lanterns at a night festival, vertical full body shot"
]

def generate_random_anime_prompt():
    hair_style = random.choice(HAIR_STYLES)
    hair_color = random.choice(HAIR_COLORS)
    dress = random.choice(DRESSES)
    setting = random.choice(POSES_AND_SETTINGS)
    
    final_prompt = (
        f"{BASE_QUALITY}, {hair_color} {hair_style}, "
        f"{dress}, {setting}, "
        "modest fully-covered clothing, clean background, ultra high resolution"
    )
    return final_prompt

# --- STEP 2: GENERATE VIA HUGGING FACE (WITH COLD-START RETRY) ---
def generate_image():
    prompt = generate_random_anime_prompt()
    print(f"[{datetime.now()}] Selected Prompt:\n{prompt}\n")
    
    print("Connecting to Hugging Face Client...")
    client = InferenceClient(token=HF_TOKEN)
    
    max_retries = 3
    image = None
    
    for attempt in range(max_retries):
        try:
            print(f"Generation attempt {attempt + 1}...")
            image = client.text_to_image(
                prompt=prompt,
                model="cagliostrolab/animagine-xl-3.1",
                negative_prompt="nsfw, nude, bad anatomy, bad hands, low resolution, blurry, watermark, signature, text, cropped",
                width=896,
                height=1152
            )
            if image:
                break
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print("Model might be loading (Cold Start). Waiting 15 seconds before retry...")
                time.sleep(15)
            else:
                print("All generation retries failed.")
                return False
                
    if not image:
        return False
        
    local_filename = "generated_anime.jpg"
    image.save(local_filename, quality=95)
    print("Image Generated Successfully!")
    
    img = Image.open(local_filename)
    img_resized = img.resize((1080, 1350), Image.Resampling.LANCZOS)
    img_resized.save("final_ig_post.jpg", quality=100)
    print("Resized to Instagram Fit (1080x1350 Portrait)!")
    return True

# --- STEP 3: UPLOAD TO TEMPORARY PUBLIC HOST ---
def upload_image_for_public_url():
    print("Uploading image to get temporary public link for Instagram...")
    with open("final_ig_post.jpg", "rb") as file:
        response = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": file})
        
    data = response.json()
    if response.status_code == 200 and "data" in data:
        raw_url = data["data"]["url"]
        direct_url = raw_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
        print(f"Public Image URL: {direct_url}")
        return direct_url
    else:
        print("Failed to upload image to host.")
        return None

# --- STEP 4: PUBLISH TO INSTAGRAM ---
def publish_to_instagram():
    if not IG_USER_ID or not ACCESS_TOKEN or not HF_TOKEN:
        print("Error: Missing Secrets!")
        return

    success = generate_image()
    if not success:
        print("Image generation failed.")
        return
    
    image_url = upload_image_for_public_url()
    if not image_url:
        print("Posting cancelled due to image upload error.")
        return

    print("Sending post request to Instagram Graph API...")
    container_url = f"https://graph.facebook.com/v18.0/{IG_USER_ID}/media"
    payload = {
        'image_url': image_url,
        'caption': "Rate this 4K anime masterpiece! 🌸✨\n\n#animeart #aiart #animelover #otaku #kawaii #animegirl",
        'access_token': ACCESS_TOKEN
    }
    
    response = requests.post(container_url, data=payload).json()
    print("Container Response:", response)
    
    if 'id' not in response:
        print("Failed to create Instagram media container.")
        return
        
    creation_id = response['id']
    time.sleep(10)
    
    publish_url = f"https://graph.facebook.com/v18.0/{IG_USER_ID}/media_publish"
    publish_payload = {
        'creation_id': creation_id,
        'access_token': ACCESS_TOKEN
    }
    
    publish_response = requests.post(publish_url, data=publish_payload).json()
    print("Publish Response:", publish_response)
    
    if 'id' in publish_response:
        print("🎉 Successfully published 4K Anime post to Instagram!")
    else:
        print("Failed to publish post to Instagram.")

if __name__ == "__main__":
    publish_to_instagram()
    
