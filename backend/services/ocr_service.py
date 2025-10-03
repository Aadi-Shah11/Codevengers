"""
OCR Service for license plate recognition from video files.
Handles video processing, frame extraction, and text recognition using OpenCV and EasyOCR.
"""

import cv2
import easyocr
import numpy as np
import tempfile
import os
import re
from typing import Optional, List, Tuple
from pathlib import Path
import logging

from config.ocr_config import OCRConfig

logger = logging.getLogger(__name__)

class OCRService:
    """Service for processing videos and extracting license plate text."""
    
    def __init__(self):
        """Initialize OCR service with EasyOCR reader."""
        try:
            # Initialize EasyOCR with configuration settings
            self.reader = easyocr.Reader(
                OCRConfig.OCR_LANGUAGES, 
                gpu=OCRConfig.USE_GPU
            )
            self.config = OCRConfig()
            logger.info(f"EasyOCR initialized successfully (GPU: {OCRConfig.USE_GPU})")
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR: {e}")
            raise
    
    def validate_video_file(self, file_path: str) -> bool:
        """
        Validate video file format and size.
        
        Args:
            file_path: Path to the video file
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Check file exists
            if not os.path.exists(file_path):
                logger.error(f"Video file not found: {file_path}")
                return False
            
            # Check file size using configuration
            file_size = os.path.getsize(file_path)
            max_size = OCRConfig.get_max_video_size_bytes()
            if file_size > max_size:
                logger.error(f"Video file too large: {file_size} bytes (max: {max_size})")
                return False
            
            # Check if OpenCV can open the video
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                logger.error(f"Cannot open video file: {file_path}")
                return False
            
            # Check if video has frames
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()
            
            if frame_count == 0:
                logger.error(f"Video file has no frames: {file_path}")
                return False
            
            logger.info(f"Video validation successful: {frame_count} frames, {file_size} bytes")
            return True
            
        except Exception as e:
            logger.error(f"Error validating video file: {e}")
            return False
    
    def extract_frames(self, video_path: str, sample_rate: int = None) -> List[np.ndarray]:
        """
        Extract frames from video for processing.
        
        Args:
            video_path: Path to the video file
            sample_rate: Extract every Nth frame (uses config default if None)
            
        Returns:
            List of extracted frames as numpy arrays
        """
        if sample_rate is None:
            sample_rate = OCRConfig.FRAME_SAMPLE_RATE
            
        frames = []
        
        try:
            cap = cv2.VideoCapture(video_path)
            frame_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Sample every Nth frame
                if frame_count % sample_rate == 0:
                    frames.append(frame)
                    logger.debug(f"Extracted frame {frame_count}")
                
                frame_count += 1
            
            cap.release()
            logger.info(f"Extracted {len(frames)} frames from {frame_count} total frames")
            
        except Exception as e:
            logger.error(f"Error extracting frames: {e}")
        
        return frames
    
    def preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocess frame for better OCR accuracy.
        
        Args:
            frame: Input frame as numpy array
            
        Returns:
            Preprocessed frame
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, OCRConfig.GAUSSIAN_BLUR_KERNEL, 0)
            
            # Enhance contrast using CLAHE
            clahe = cv2.createCLAHE(
                clipLimit=OCRConfig.CLAHE_CLIP_LIMIT, 
                tileGridSize=OCRConfig.CLAHE_TILE_GRID_SIZE
            )
            enhanced = clahe.apply(blurred)
            
            # Apply edge detection to help identify license plate regions
            edges = cv2.Canny(
                enhanced, 
                OCRConfig.CANNY_THRESHOLD_1, 
                OCRConfig.CANNY_THRESHOLD_2
            )
            
            # Dilate edges to connect broken lines
            kernel = np.ones(OCRConfig.DILATION_KERNEL_SIZE, np.uint8)
            dilated = cv2.dilate(edges, kernel, iterations=OCRConfig.DILATION_ITERATIONS)
            
            return enhanced  # Return enhanced grayscale for OCR
            
        except Exception as e:
            logger.error(f"Error preprocessing frame: {e}")
            return frame
    
    def extract_text_from_frame(self, frame: np.ndarray) -> List[Tuple[str, float]]:
        """
        Extract text from a single frame using EasyOCR.
        
        Args:
            frame: Preprocessed frame
            
        Returns:
            List of tuples (text, confidence)
        """
        try:
            # Use EasyOCR to detect text
            results = self.reader.readtext(frame)
            
            text_results = []
            for (bbox, text, confidence) in results:
                # Filter results with minimum confidence threshold
                if confidence > OCRConfig.OCR_CONFIDENCE_THRESHOLD:
                    text_results.append((text, confidence))
                    logger.debug(f"Detected text: '{text}' with confidence {confidence:.2f}")
            
            return text_results
            
        except Exception as e:
            logger.error(f"Error extracting text from frame: {e}")
            return []
    
    def validate_license_plate(self, text: str) -> bool:
        """
        Validate if extracted text matches license plate patterns.
        
        Args:
            text: Extracted text string
            
        Returns:
            bool: True if text matches license plate pattern
        """
        # Remove spaces and convert to uppercase
        cleaned_text = re.sub(r'\s+', '', text.upper())
        
        # Use patterns from configuration
        for pattern in OCRConfig.LICENSE_PLATE_PATTERNS:
            if re.match(pattern, cleaned_text):
                logger.info(f"Valid license plate pattern found: {cleaned_text}")
                return True
        
        return False
    
    def process_video(self, video_path: str) -> Optional[str]:
        """
        Process video file and extract license plate text.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Extracted license plate text or None if not found
        """
        try:
            # Validate video file
            if not self.validate_video_file(video_path):
                return None
            
            # Extract frames from video
            frames = self.extract_frames(video_path)
            if not frames:
                logger.error("No frames extracted from video")
                return None
            
            # Process each frame to find license plates
            best_result = None
            best_confidence = 0.0
            
            for i, frame in enumerate(frames):
                # Preprocess frame
                processed_frame = self.preprocess_frame(frame)
                
                # Extract text from frame
                text_results = self.extract_text_from_frame(processed_frame)
                
                # Find the best license plate candidate
                for text, confidence in text_results:
                    if self.validate_license_plate(text) and confidence > best_confidence:
                        best_result = re.sub(r'\s+', '', text.upper())
                        best_confidence = confidence
                        logger.info(f"Found license plate candidate: {best_result} (confidence: {confidence:.2f})")
            
            if best_result:
                logger.info(f"Best license plate result: {best_result} (confidence: {best_confidence:.2f})")
                return best_result
            else:
                logger.warning("No valid license plate found in video")
                return None
                
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            return None
    
    def save_uploaded_file(self, file_content: bytes, filename: str) -> str:
        """
        Save uploaded file to temporary location for processing.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            
        Returns:
            Path to saved temporary file
        """
        try:
            # Create temporary file with original extension
            file_extension = Path(filename).suffix
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, 
                suffix=file_extension,
                prefix=OCRConfig.TEMP_FILE_PREFIX
            )
            
            temp_file.write(file_content)
            temp_file.close()
            
            logger.info(f"Saved uploaded file to: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Error saving uploaded file: {e}")
            raise
    
    def cleanup_temp_file(self, file_path: str):
        """
        Clean up temporary file after processing.
        
        Args:
            file_path: Path to temporary file
        """
        if not OCRConfig.CLEANUP_TEMP_FILES:
            return
            
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.info(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up temporary file: {e}")