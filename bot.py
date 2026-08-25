import os
import random
import time
import requests
from PIL import Image
from huggingface_hub import InferenceClient

HF_TOKEN = os.getenv("HF_TOKEN")
IG_USER_ID = os.getenv("IG_USER_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

ANIME_CHARACTERS = [
    "Asuna from Sword Art Online", "Rem from Re:Zero", "Mikasa from Attack on Titan",
    "Zero Two from Darling in the Franxx", "Emilia from Re:Zero", "Ram from Re:Zero",
    "Aqua from Konosuba", "Mitsuri from Demon Slayer", "Yor Forger from Spy x Family",
    "Nobara from Jujutsu Kaisen", "Chizuru from Rent-a-Girlfriend", "Saber from Fate"
]

POSES = [
    "jumping with happiness", "tilting head curiously", "hand on cheek with blush",
    "spinning and dancing joyfully", "sitting cross-legged playfully", "winking flirty",
    "looking back over shoulder romantically", "touching hair seductively"
]

BACKGROUNDS = [
    "Tokyo city street with neon lights", "Beautiful beach resort at sunset",
    "Cherry blossom garden at night", "Starry night rooftop overlooking city",
    "Enchanted forest with magical trees", "High school hallway anime aesthetic",
    "Cafe with cozy indoor atmosphere", "Night festival with paper lanterns"
]

BASE_QUALITY = "masterpiece, best quality, ultra detailed, 8k resolution, 4k wallpaper, sharp focus, aesthetic, anime style illustration, beautiful face, perfect features"

def generate_image():
    character = random.choice(ANIME_CHARACTERS)
    pose = random.choice(POSES)
    bg = random.choice(BACKGROUNDS)
    
    prompt = f"{BASE_QUALITY}, {character}, {pose}, {bg}, anime girl, modest fully-covered clothing, ultra high resolution"
    print(f"[INFO] Selected Prompt: {prompt[:100]}...")
    
    # Initialize the official Hugging Face Inference Client
    client = InferenceClient(
        provider="hf-inference",
        api_key=HF_TOKEN,
    )
    
    for attempt in range(3):
        try:
            print(f"[INFO] Attempt {attempt + 1}/3 - Generating image with Hugging Face...")
            
            # Use the official text_to_image method
            image = client.text_to_image(
                prompt=prompt,
                model="stabilityai/stable-diffusion-xl-base-1.0"
            )
            
            # Save the returned PIL Image
            image.save("generated_anime.jpg")
            print("[SUCCESS] Image generated and saved!")
            return True
                
        except Exception as e:
            print(f"[ERROR] Attempt {attempt + 1} failed: {str(e)}")
            if attempt < 2:
                wait_time = (attempt + 1) * 10
                print(f"[INFO] Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
    
    print("[FAILED] Image generation failed after all attempts")
    return False

def upload_image_for_public_url():
    try:
        with open("generated_anime.jpg", "rb") as f:
            response = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": f}, timeout=30)
        
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
    
