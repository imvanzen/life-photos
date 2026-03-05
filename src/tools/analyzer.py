import json
from PIL import Image
from pydantic import BaseModel
from google.genai import types
from src.models import AnalysisResult
from src.utils import get_client, logger, load_image_for_api

class AnalysisSchema(BaseModel):
    is_suitable: bool
    needs_upscale: bool
    needs_restoration: bool
    needs_colorization: bool
    reason: str
    technical_score: float
    vibe_emotion: str
    vibe_lighting: str
    vibe_action: str

class ImageAnalyzer:
    def __init__(self):
        self.client = get_client()
        self.model_name = "gemini-2.0-flash" 

    def _get_target_aspect_ratio(self, width: int, height: int) -> str:
        ratio = width / height
        # Veo supported ratios: 16:9 (1.77), 9:16 (0.56), 4:3 (1.33), 3:4 (0.75), 1:1 (1.0)
        
        if ratio > 1.5:
            return "16:9"
        elif ratio < 0.65:
            return "9:16"
        elif ratio > 1.2:
            return "4:3"
        elif ratio < 0.85:
            return "3:4"
        else:
            return "1:1"

    def analyze(self, image_path: str) -> AnalysisResult:
        logger.info(f"Analyzing image: {image_path}")
        
        try:
            # 1. Get Technical Metadata via PIL
            with Image.open(image_path) as img:
                width, height = img.size
                
            target_ratio = self._get_target_aspect_ratio(width, height)
            logger.info(f"Dimensions: {width}x{height}, Target Ratio: {target_ratio}")

            # 2. Get AI Analysis via Gemini
            image_input = load_image_for_api(image_path)
            
            # Convert types.Image to types.Part for generate_content compatibility
            # types.Image is great for Vision/Video specialized APIs, but generate_content prefers Parts or PIL
            if image_input.image_bytes:
                 image_part = types.Part.from_bytes(
                     data=image_input.image_bytes, 
                     mime_type=image_input.mime_type or "image/jpeg"
                 )
            else:
                # Fallback if from_file didn't load bytes (unlikely)
                with open(image_path, "rb") as f:
                    image_part = types.Part.from_bytes(data=f.read(), mime_type="image/jpeg")

            prompt = """
            Act as a professional cinematographer and photo editor. Analyze this image to prepare it for cinematic animation.
            
            Evaluate Technical Quality:
            1. Suitability: Is it clear enough to animate?
            2. Needs Upscale: Is resolution or detail too low for high-def video?
            3. Needs Restoration: Are there artifacts/damage?
            
            Extract Cinematic Vibe (be specific and evocative):
            1. Emotion/Mood: (e.g., "Nostalgic and serene", "Energetic and bright", "Melancholic mystery")
            2. Lighting: (e.g., "Golden hour backlighting", "Soft diffused studio light", "Moody chiaroscuro")
            3. Subject Action for Animation: Describe a subtle, natural movement suitable for a loop. (e.g., "Gently smiling while breeze moves hair", "Staring intensely with subtle breathing", "Laughing with head tilt")
            
            Return JSON matching the schema.
            """
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, image_part],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=AnalysisSchema,
                    temperature=0.2
                )
            )
            
            if not response.parsed:
                logger.error("Failed to parse analysis response")
                return AnalysisResult(
                    is_suitable=False, needs_upscale=False, needs_restoration=False, needs_colorization=False,
                    reason="AI Analysis failed to return valid JSON.", technical_score=0.0
                )
                
            data: AnalysisSchema = response.parsed
            
            logger.info(f"Analysis complete. Score: {data.technical_score}, Vibe: {data.vibe_emotion}")
            
            return AnalysisResult(
                is_suitable=data.is_suitable,
                needs_upscale=data.needs_upscale,
                needs_restoration=data.needs_restoration,
                needs_colorization=data.needs_colorization,
                reason=data.reason,
                technical_score=data.technical_score,
                width=width,
                height=height,
                target_aspect_ratio=target_ratio,
                vibe_emotion=data.vibe_emotion,
                vibe_lighting=data.vibe_lighting,
                vibe_action=data.vibe_action
            )

        except Exception as e:
            logger.exception(f"Error analyzing image: {e}")
            return AnalysisResult(
                is_suitable=False, needs_upscale=False, needs_restoration=False, needs_colorization=False,
                reason=f"System error during analysis: {str(e)}", technical_score=0.0
            )
