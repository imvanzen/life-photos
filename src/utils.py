import os
import logging
from google import genai
from google.genai import types

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("LifePhotos")

def get_client() -> genai.Client:
    """
    Returns a configured Google GenAI client.
    Raises ValueError if GOOGLE_API_KEY is not set.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.error("GOOGLE_API_KEY not found in environment variables.")
        raise ValueError("GOOGLE_API_KEY not found.")
    
    return genai.Client(api_key=api_key)

def load_image_for_api(image_path: str) -> types.Image:
    """
    Loads an image from a path and returns a types.Image object 
    compatible with the Google GenAI SDK.
    """
    # Use the SDK's built-in helper if available (handles mime types automatically)
    if hasattr(types.Image, 'from_file'):
        return types.Image.from_file(location=image_path)
    
    # Fallback to manual reading
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    
    # Basic mime type inference
    mime_type = "image/jpeg"
    ext = image_path.lower()
    if ext.endswith(".png"):
        mime_type = "image/png"
    elif ext.endswith(".webp"):
        mime_type = "image/webp"
    elif ext.endswith(".heic"):
        mime_type = "image/heic"
        
    # Attempt to construct with mime_type if supported, or just bytes
    try:
        return types.Image(image_bytes=image_bytes, mime_type=mime_type)
    except TypeError:
        return types.Image(image_bytes=image_bytes)
