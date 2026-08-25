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

# Top 15 Famous Anime Characters
ANIME_CHARACTERS = [
    "Asuna from Sword Art Online",
    "Rem from Re:Zero",
    "Mikasa from Attack on Titan",
    "Zero Two from Darling in the Franxx",
    "Emilia from Re:Zero",
    "Ram from Re:Zero",
    "Aqua from Konosuba",
    "Mitsuri from Demon Slayer",
    "Daki from Demon Slayer",
    "Nobara from Jujutsu Kaisen",
    "Mitsuri Kanroji",
    "Yor Forger from Spy x Family",
    "Chizuru from Rent-a-Girlfriend",
    "Yuna from Is It Wrong to Try to Pick Up Girls",
    "Saber from Fate series"
]

# Romantic Poses
ROMANTIC_POSES = [
    "hand near lips in a shy kiss gesture",
    "hand on cheek with blush",
    "both hands near face looking surprised",
    "touching hair seductively",
    "hand on heart emotional pose",
    "fingers together shy pose",
    "winking with flirty hand gesture",
    "looking back over shoulder romantically",
    "hand on chest with blush",
    "walking with wind blowing hair"
]

# Cute Poses
CUTE_POSES = [
    "lying down innocently on soft bed",
    "hugging a pillow adorably",
    "leaning against wall relaxed",
    "sitting cross-legged playfully",
    "jumping with happiness",
    "tilting head curiously",
    "tongue out playfully mischievous",
    "making peace sign cheerfully",
    "arm stretched yawning sleepily",
    "sitting on knees innocently",
    "peeking from behind shyly",
    "spinning and dancing joyfully"
]

# Anime Universe Settings/Backgrounds
ANIME_BACKGROUNDS = [
    "Tokyo city street with neon lights and modern buildings",
    "Isekai fantasy village with magical atmosphere",
    "High school hallway with anime aesthetic",
    "Beautiful beach resort at sunset",
    "Enchanted forest with magical trees and glowing lights",
    "Night festival with paper lanterns",
    "Magical girl academy with pink and white theme",
    "Demon slayer mountain temple at dawn",
    "Cafe with cozy indoor atmosphere and warm lighting",
    "Cherry blossom garden in full bloom at night",
    "Starry night rooftop overlooking city",
    "Ancient shrine with traditional Japanese architecture"
]

# Different Anime Styles/Clothing
ANIME_STYLES = [
    "wearing school uniform blazer and skirt",
    "wearing casual modern street clothes",
    "wearing traditional Japanese kimono",
    "wearing fantasy adventure armor",
    "wearing magical girl transformation dress",
    "wearing elegant ball gown",
    "wearing casual hoodie and jeans",
    "wearing shrine maiden outfit",
    "wearing swimsuit at beach",
    "wearing traditional maid outfit",
    "wearing magical academy uniform",
    "wearing demon slayer corps uniform"
]

BASE_QUALITY = "masterpiece, best quality, ultra detailed, 8k resolution, 4k wallpaper, sharp focus, aesthetic, anime style illustration, beautiful face, perfect features"

def generate_random_anime_prompt():
    character = random.choice(ANIME_CHARACTERS)
    
    # Random mix of romantic and cute poses
    if random.choice([True, False]):
        pose = random.choice(ROMANTIC_POSES)
    else:
        pose = random.choice(CUTE_POSES)
    
    background = random.choice(ANIME_BACKGROUNDS)
    style = random.choice(ANIME_STYLES)
    
    prompt = f"{BASE_QUALITY}, {character}, {style}, {pose}, {background}, modest fully-covered clothing where appropriate, clean detailed background, ultra high resolution, anime girl"
    
    return prompt

def generate_image():
    prompt = generate_random_anime_prompt()
    print(f"[INFO] Selected Prompt: {prompt}")
    
    # Set API token
    os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN
    
    image = None
    for attempt in range(3):
        try:
            print(f"[INFO] Attempt {attempt + 1}/3 - Generating image with Replicate...")
            
            # Using Stable Diffusion XL (more reliable and free tier friendly)
            output = replicate.run(
                "stability-ai/sdxl:39ed52f2a60c3b36b96384b26f1ea0d2f189f60b848c4aa73c60860d3de47e5c",
                input={
                    "prompt": prompt,
                    "negative_prompt": "nsfw, nude, bad anatomy, bad hands, low resolution, blurry, watermark, signature, text, cropped, extra limbs",
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
