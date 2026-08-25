import os
import random
import time
import requests
from PIL import Image
from huggingface_hub import InferenceClient

HF_TOKEN = os.getenv("HF_TOKEN")
IG_USER_ID = os.getenv("IG_USER_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

# Character list with specific facial/appearance features for accurate generation
ANIME_CHARACTERS = [
    "Hinata Hyuga from Naruto with long flowing dark indigo hair and glowing pale lavender eyes",
    "Asuna from Sword Art Online with long chestnut-brown hair and warm hazel eyes",
    "Rem from Re:Zero with distinctive light blue bob cut covering one eye and bright blue eyes",
    "Mikasa from Attack on Titan with sleek black hair and sharp grey eyes",
    "Zero Two from Darling in the Franxx with iconic long pink hair, red horns, and striking cyan eyes",
    "Yor Forger from Spy x Family with long black hair, crimson red eyes, and elegant hairband",
    "Mitsuri Kanroji from Demon Slayer with striking long pink-to-green braided hair and emerald green eyes",
    "Saber from Fate with neatly braided blonde hair and striking green eyes"
]

# Random seductive and alluring poses
SEDUCTIVE_POSES = [
    "sitting on a luxury sofa, leaning forward slightly with an alluring teasing smirk, intense eye contact",
    "looking back over her shoulder seductively with a soft captivating smile, dramatic cinematic lighting",
    "touching her hair sensually while giving a bold, magnetic, and flirtatious gaze to the camera",
    "leaning against a wall with legs crossed provocatively, soft alluring expression, cinematic shadows",
    "stretching gracefully with a warm seductive mood, soft warm evening ambient lighting"
]

BACKGROUNDS = [
    "cozy luxury room background with warm glowing ambient lamps and beautiful bokeh",
    "Tokyo city night street background with soft blurred neon lights and aesthetic depth of field",
    "luxury modern bedroom with soft moody lighting and warm atmosphere",
    "starlit rooftop balcony overlooking a city skyline with soft glowing lights"
]

BASE_QUALITY = "masterpiece, best quality, ultra-detailed vertical portrait, 8k resolution, sharp focus, seductive and alluring mood, cinematic dramatic lighting, flawless smooth skin, flawless anatomy, zero artifacts, no watermarks"

def generate_image():
    character = random.choice(ANIME_CHARACTERS)
    pose = random.choice(SEDUCTIVE_POSES)
    bg = random.choice(BACKGROUNDS)
    
    prompt = f"{BASE_QUALITY}, {character}, {pose}, in {bg}, sensual fashion, form-fitting stylish clothing"
    print(f"[INFO] Selected Prompt: {prompt[:120]}...")
    
    client = InferenceClient(
        model="stabilityai/stable-diffusion-xl-base-1.0",
        token=HF_TOKEN,
    )
    
    for attempt in range(3):
        try:
            print(f"[INFO] Attempt {attempt + 1}/3 - Generating image with Hugging Face...")
            
            image = client.text_to_image(prompt=prompt)
            
            # Convert to RGB and force JPEG saving
            image = image.convert("RGB")
            image.save("generated_anime.jpg", "JPEG")
            
            print("[SUCCESS] Seductive image generated and saved as JPEG!")
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
        # Changed to catbox.moe for reliable direct image hosting that Instagram accepts
        with open("generated_anime.jpg", "rb") as f:
            response = requests.post(
                "https://catbox.moe/user/api.php",
                data={"reqtype": "fileupload"},
                files={"fileToUpload": f},
                timeout=30
            )
        
        if response.status_code == 200 and response.text.startswith("http"):
            public_url = response.text.strip()
            print(f"[SUCCESS] Image uploaded to Catbox: {public_url}")
            return public_url
        else:
            print(f"[ERROR] Upload failed: {response.text}")
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
        caption = "Rate this gorgeous aesthetic masterpiece! ✨🔥\n\n#animeart #aiart #animelover #seductiveanime #aesthetic #animegirl"
        
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
