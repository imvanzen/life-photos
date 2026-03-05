from typing import Callable, Optional, Any, Union
from src.models import AnalysisResult, ProcessResult
from src.tools.analyzer import ImageAnalyzer
from src.tools.corrector import ImageCorrector
from src.tools.generator import VideoGenerator
from src.utils import logger

class PhotoProcessor:
    def __init__(self):
        self.analyzer = ImageAnalyzer()
        self.corrector = ImageCorrector()
        self.generator = VideoGenerator()

    def process_workflow(self, image_path: str, status_callback: Optional[Callable[[Union[str, Any]], None]] = None) -> ProcessResult:
        """
        Executes the full photo-to-video pipeline.
        
        Args:
            status_callback: Can receive a string (log message) or an object (e.g. Operation) for detailed progress.
        """
        logs = []
        
        def update_status(msg: Union[str, Any]):
            if isinstance(msg, str):
                logger.info(msg)
                logs.append(msg)
            if status_callback:
                status_callback(msg)

        update_status("🚀 Starting Photo Processing Pipeline...")
        current_image_path = image_path

        try:
            # 1. Analyze
            update_status("🔍 Phase 1: Analyzing Image Quality & Vibe...")
            analysis: AnalysisResult = self.analyzer.analyze(current_image_path)
            
            logs.append(f"Dimensions: {analysis.width}x{analysis.height} ({analysis.target_aspect_ratio})")
            logs.append(f"Vibe: {analysis.vibe_emotion}, {analysis.vibe_lighting}, {analysis.vibe_action}")
            logs.append(f"Needs: Upscale={analysis.needs_upscale}")
            
            if not analysis.is_suitable:
                update_status(f"❌ Image Rejected: {analysis.reason}")
                return ProcessResult(success=False, error=analysis.reason, logs=logs)
            
            update_status(f"✅ Image Accepted. Score: {analysis.technical_score:.2f}")

            # 2. Correct (Upscale only)
            if analysis.needs_upscale:
                update_status("⚙️ Phase 2: Upscaling Image for Maximum Fidelity...")
                current_image_path = self.corrector.upscale(current_image_path)
                logs.append(f"Upscaled image to: {current_image_path}")
            
            # 3. Animate
            update_status(f"🎥 Phase 3: Generating Video (Veo 3.1) - Ratio: {analysis.target_aspect_ratio}...")
            
            # Construct Vibe Prompt part
            vibe_prompt = f"{analysis.vibe_emotion} atmosphere. Lighting is {analysis.vibe_lighting}. Subject is {analysis.vibe_action}"
            
            # Pass the raw callback to generator so it can stream operations back
            video_path = self.generator.generate(
                image_path=current_image_path,
                aspect_ratio=analysis.target_aspect_ratio,
                vibe_prompt=vibe_prompt,
                poll_callback=status_callback 
            )
            
            if video_path:
                update_status("✨ Video Generation Complete!")
                return ProcessResult(
                    success=True,
                    video_path=video_path,
                    final_image_path=current_image_path,
                    logs=logs
                )
            else:
                return ProcessResult(success=False, error="Video generation returned no result.", logs=logs)

        except Exception as e:
            err_msg = f"Pipeline Error: {str(e)}"
            logger.exception(err_msg)
            return ProcessResult(success=False, error=err_msg, logs=logs)
