import os
import random
import time
import requests
from datetime import datetime
from PIL import Image
import replicate

IG_USER_ID = os.getenv("IG_USER_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

# Validate required environment variables
if not REPLICATE_API_TOKEN:
    print("[ERROR] REPLICATE_API_TOKEN not found in environment variables!")
    print("[ERROR] Please add REPLICATE_API_TOKEN to GitHub Secrets")
    exit(1)

if not IG_USER_ID:
    print("[ERROR] IG_USER_ID not found in environment variables!")
    exit(1)

if not ACCESS_TOKEN:
    print("[ERROR] ACCESS_TOKEN not found in environment variables!")
    exit(1)

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
    return f"{BASE_QUALITY}, {random.choice(HAIR_COLORS)} {random.choice(HAIR_STYLES)}, {random.choice(DRESSES)}, {random.choice(POSES_AND_SETTINGS)}, modest fully-covered clothing, clean background, ultra high resolution"

def generate_image():
    prompt = generate_random_anime_prompt()
    print(f"[INFO] Selected Prompt: {prompt}")
    
    # Set API token
    os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN
    
    image = None
    for attempt in range(3):
        try:
            print(f"[INFO] Attempt {attempt + 1}/3 - Generating image with Replicate...")
            
            # Using Animagine XL 3.1 via Replicate
            output = replicate.run(
                "cagliostrolab/animagine-xl-3.1:0bae911e474a0210655ba270d5846d3b9ef144fe537eb411506a9a326421fea58",
                input={
                    "prompt": prompt,
                    "negative_prompt": "nsfw, nude, bad anatomy, bad hands, low resolution, blurry, watermark, signature, text, cropped",
                    "width": 896,
                    "height": 1152,
                    "num_outputs": 1,
                    "scheduler": "DPMSolverMultistep",
                    "num_inference_steps": 25,
                    "guidance_scale": 7.5
                }
            )
            
            if output and len(output) > 0:
                image_url = output[0]
                print(f"[SUCCESS] Image generated: {image_url}")
                
                # Download image
                img_response = requests.get(image_url, timeout=30)
                if img_response.status_code == 200:
                    with open("generated_anime.jpg", "wb") as f:
                        f.write(img_response.content)
                    print("[INFO] Image downloaded successfully")
                    break
                    
        except Exception as e:
            print(f"[ERROR] Attempt {attempt + 1} failed: {str(e)}")
            if attempt < 2:
                wait_time = (attempt + 1) * 10
                print(f"[INFO] Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            
    if not os.path.exists("generated_anime.jpg"):
        print("[FAILED] Image generation failed after all attempts")
        return False
        
    # Resize for Instagram
    try:
        img = Image.open("generated_anime.jpg")
        img.resize((1080, 1350), Image.Resampling.LANCZOS).save("final_ig_post.jpg", quality=100)
        print("[SUCCESS] Image resized for Instagram")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to resize image: {str(e)}")
        return False

def upload_image_for_public_url():
    try:
        with open("final_ig_post.jpg", "rb") as file:
            response = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": file}, timeout=30)
        data = response.json()
        if response.status_code == 200 and "data" in data:
            public_url = data["data"]["url"].replace("tmpfiles.org/", "tmpfiles.org/dl/")
            print(f"[SUCCESS] Image uploaded: {public_url}")
            return public_url
        else:
            print(f"[ERROR] Upload failed: {data}")
            return None
    except Exception as e:
        print(f"[ERROR] Failed to upload image: {str(e)}")
        return None

def publish_to_instagram():
    print("[START] Publishing to Instagram...")
    
    if not generate_image():
        print("[FAILED] Image generation failed")
        return
    
    image_url = upload_image_for_public_url()
    if not image_url:
        print("[FAILED] Image upload failed")
        return

    try:
        container_url = f"https://graph.facebook.com/v18.0/{IG_USER_ID}/media"
        caption = "Rate this 4K anime masterpiece! 🌸✨\n\n#animeart #aiart #animelover #otaku #kawaii #animegirl"
        
        print("[INFO] Creating Instagram media container...")
        res = requests.post(
            container_url,
            data={
                'image_url': image_url,
                'caption': caption,
                'access_token': ACCESS_TOKEN
            },
            timeout=30
        )
        
        res_data = res.json()
        
        if 'id' in res_data:
            media_id = res_data['id']
            print(f"[INFO] Container created, ID: {media_id}")
            
            time.sleep(10)
            
            print("[INFO] Publishing to Instagram feed...")
            publish_res = requests.post(
                f"https://graph.facebook.com/v18.0/{IG_USER_ID}/media_publish",
                data={
                    'creation_id': media_id,
                    'access_token': ACCESS_TOKEN
                },
                timeout=30
            )
            
            if publish_res.status_code == 200:
                print("[SUCCESS] 🎉 Published successfully to Instagram!")
            else:
                print(f"[ERROR] Publishing failed: {publish_res.json()}")
        else:
            print(f"[ERROR] Container creation failed: {res_data}")
            
    except Exception as e:
        print(f"[ERROR] Failed to publish: {str(e)}")

if __name__ == "__main__":
    publish_to_instagram()
