from typing import Callable, Any, Optional
import time
import os
from google.genai import types
from src.utils import get_client, logger, load_image_for_api

class VideoGenerator:
    def __init__(self):
        self.client = get_client()
        self.model_name = "veo-3.1-generate-preview" 

    def generate(self, image_path: str, aspect_ratio: str, vibe_prompt: str, poll_callback: Optional[Callable[[Any], None]] = None) -> str:
        """
        Generates a video from the image using Veo 3.1.
        """
        logger.info(f"Generating video for: {image_path}")
        logger.info(f"Target Aspect Ratio: {aspect_ratio}")
        logger.info(f"Vibe Prompt: {vibe_prompt}")
        
        try:
            img_input = load_image_for_api(image_path)
            
            # Construct the final prompt
            full_prompt = f"Cinematic video, {vibe_prompt}. High fidelity, photorealistic, subtle natural motion."
            
            logger.info(f"Full Prompt: {full_prompt}")
            
            operation = self.client.models.generate_videos(
                model=self.model_name,
                prompt=full_prompt,
                image=img_input,
                config=types.GenerateVideosConfig(
                    aspect_ratio=aspect_ratio,
                    # person_generation='dont_allow', # Not supported by veo-3.1-preview yet
                    # duration_seconds=5, # Veo defaults are usually good
                )
            )
            
            logger.info("Video generation operation started. Polling...")
            
            while not operation.done:
                if poll_callback:
                    poll_callback(operation)
                time.sleep(5)
                operation = self.client.operations.get(operation)
            
            # Final callback to share result state
            if poll_callback:
                poll_callback(operation)
            
            if operation.result and operation.result.generated_videos:
                video_result = operation.result.generated_videos[0]
                
                # Save to output/
                filename = os.path.basename(image_path)
                name, ext = os.path.splitext(filename)
                output_path = os.path.join("output", f"{name}_animated.mp4")
                os.makedirs("output", exist_ok=True)
                
                # Check for video content
                if video_result.video.uri:
                    logger.info(f"Video URI found: {video_result.video.uri}")
                    try:
                        # Attempt download using File API
                        # The SDK expects 'file' argument which can be the object or name
                        file_content = self.client.files.download(file=video_result.video)
                        
                        with open(output_path, "wb") as f:
                            f.write(file_content)
                    except Exception as download_err:
                        logger.warning(f"File API download failed ({download_err}). trying raw HTTP if URI is URL...")
                        # Fallback logic if needed, but File API is standard for Veo
                        raise download_err
                elif hasattr(video_result.video, 'image_bytes') and video_result.video.image_bytes:
                     # "image_bytes" might be where video bytes are stored if small? 
                     # Or maybe just "bytes" field? types.Video doesn't usually have bytes.
                     pass
                else:
                    # Try .save() as last resort (local/bytes handling)
                    try:
                        video_result.video.save(output_path)
                    except NotImplementedError:
                         raise Exception("Video generated but cannot be saved (Remote URI not handled).")

                logger.info(f"Video saved to {output_path}")
                return output_path
            else:
                raise Exception("Operation completed but returned no videos.")
        
        except Exception as e:
            logger.exception(f"Error during video generation: {e}")
            raise e
