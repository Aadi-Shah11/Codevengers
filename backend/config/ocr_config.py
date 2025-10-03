"""
OCR Configuration settings for video processing and license plate recognition.
"""

import os
from typing import List

class OCRConfig:
    """Configuration class for OCR service settings."""
    
    # Video processing settings
    MAX_VIDEO_SIZE_MB = int(os.getenv("MAX_VIDEO_SIZE_MB", "10"))
    FRAME_SAMPLE_RATE = int(os.getenv("FRAME_SAMPLE_RATE", "30"))  # Extract every Nth frame
    
    # OCR settings
    OCR_CONFIDENCE_THRESHOLD = float(os.getenv("OCR_CONFIDENCE_THRESHOLD", "0.7"))
    USE_GPU = os.getenv("USE_GPU", "false").lower() == "true"
    OCR_LANGUAGES = ["en"]  # Supported languages for EasyOCR
    
    # License plate validation patterns
    LICENSE_PLATE_PATTERNS = [
        r'^[A-Z]{2,3}\d{3,4}$',  # AB123, ABC1234
        r'^\d{2,3}[A-Z]{2,3}\d{2,4}$',  # 12AB34, 123ABC1234
        r'^[A-Z]{1,2}\d{1,2}[A-Z]{1,2}\d{1,4}$',  # A1B234, AB12CD1234
        r'^[A-Z]{3}\d{3}$',  # ABC123 (common format)
        r'^\d{3}[A-Z]{3}$',  # 123ABC (reverse format)
    ]
    
    # Image preprocessing settings
    GAUSSIAN_BLUR_KERNEL = (5, 5)
    CLAHE_CLIP_LIMIT = 2.0
    CLAHE_TILE_GRID_SIZE = (8, 8)
    CANNY_THRESHOLD_1 = 50
    CANNY_THRESHOLD_2 = 150
    DILATION_KERNEL_SIZE = (3, 3)
    DILATION_ITERATIONS = 1
    
    # Supported video formats
    SUPPORTED_VIDEO_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
    
    # Temporary file settings
    TEMP_FILE_PREFIX = "video_upload_"
    CLEANUP_TEMP_FILES = True
    
    @classmethod
    def get_max_video_size_bytes(cls) -> int:
        """Get maximum video size in bytes."""
        return cls.MAX_VIDEO_SIZE_MB * 1024 * 1024
    
    @classmethod
    def is_supported_format(cls, filename: str) -> bool:
        """Check if video format is supported."""
        file_extension = os.path.splitext(filename.lower())[1]
        return file_extension in cls.SUPPORTED_VIDEO_FORMATS