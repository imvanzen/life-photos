import os
from google.genai import types
from src.utils import get_client, logger, load_image_for_api

class ImageCorrector:
    def __init__(self):
        self.client = get_client()
    
    def upscale(self, image_path: str) -> str:
        """
        Upscales the image x2 using Imagen 3.
        Returns path to the upscaled image.
        """
        logger.info(f"Upscaling image: {image_path}")
        try:
            # Load image using helper (returns types.Image)
            img_input = load_image_for_api(image_path)
            
            # Use 'imagen-3.0-generate-002' for upscaling
            # Note: Verify if this model is available in your region/tier.
            model_name = 'imagen-3.0-generate-002'
            
            logger.info(f"Calling upscale_image with {model_name}...")
            
            response = self.client.models.upscale_image(
                model=model_name,
                image=img_input,
                upscale_factor='x2',
                config=types.UpscaleImageConfig(
                    output_mime_type='image/jpeg',
                ),
            )
            
            if response.generated_images:
                # Save to output directory
                filename = os.path.basename(image_path)
                name, ext = os.path.splitext(filename)
                output_path = os.path.join("output", f"{name}_upscaled.jpg")
                
                # Ensure output dir exists
                os.makedirs("output", exist_ok=True)
                
                response.generated_images[0].image.save(output_path)
                logger.info(f"Upscale success: {output_path}")
                return output_path
            
            logger.warning("upscale_image returned no images. Returning original.")
            return image_path
            
        except Exception as e:
            logger.warning(f"Upscaling failed: {e}. Proceeding with original.")
            return image_path

    # Removed 'restore' method as it was not in the focused plan and often redundant with upscale
