import os
import random
import time
import requests
from datetime import datetime
from PIL import Image
from huggingface_hub import InferenceClient

IG_USER_ID = os.getenv("IG_USER_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

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
    print(f"Prompt: {prompt}")
    client = InferenceClient(token=HF_TOKEN)
    
    image = None
    for attempt in range(5):
        try:
            print(f"Attempt {attempt + 1}...")
            time.sleep(10) # Wait for model to wake up from cold start
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
            print(f"Error: {e}")
            
    if not image:
        return False
        
    image.save("generated_anime.jpg", quality=95)
    img = Image.open("generated_anime.jpg")
    img.resize((1080, 1350), Image.Resampling.LANCZOS).save("final_ig_post.jpg", quality=100)
    return True

def upload_image_for_public_url():
    with open("final_ig_post.jpg", "rb") as file:
        response = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": file})
    data = response.json()
    if response.status_code == 200 and "data" in data:
        return data["data"]["url"].replace("tmpfiles.org/", "tmpfiles.org/dl/")
    return None

def publish_to_instagram():
    if not generate_image(): return
    image_url = upload_image_for_public_url()
    if not image_url: return

    container_url = f"https://graph.facebook.com/v18.0/{IG_USER_ID}/media"
    res = requests.post(container_url, data={'image_url': image_url, 'caption': "Rate this 4K anime masterpiece! 🌸✨\n\n#animeart #aiart #animelover #otaku #kawaii #animegirl", 'access_token': ACCESS_TOKEN}).json()
    
    if 'id' in res:
        time.sleep(10)
        requests.post(f"https://graph.facebook.com/v18.0/{IG_USER_ID}/media_publish", data={'creation_id': res['id'], 'access_token': ACCESS_TOKEN})
        print("🎉 Published successfully!")

if __name__ == "__main__":
    publish_to_instagram()
    
