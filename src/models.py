from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class AnalysisResult:
    """
    Result of the image assessment phase.
    """
    is_suitable: bool          # Can we proceed with video generation?
    needs_upscale: bool        # Is resolution too low?
    needs_restoration: bool    # Are there scratches/artifacts/noise?
    needs_colorization: bool   # Is it B&W?
    reason: str                # Explanation for the assessment
    technical_score: float     # 0.0 to 1.0 quality score
    
    # New fields for Context-Aware Generation
    width: int = 0
    height: int = 0
    target_aspect_ratio: str = "16:9" # "16:9" or "9:16" usually
    vibe_emotion: str = ""
    vibe_lighting: str = ""
    vibe_action: str = ""

@dataclass
class ProcessResult:
    """
    Final result of the entire processing pipeline.
    """
    success: bool
    video_path: Optional[str] = None
    final_image_path: Optional[str] = None # The potentially enhanced image used for video
    error: Optional[str] = None
    logs: List[str] = field(default_factory=list)
