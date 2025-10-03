"""
Demo script for OCR video processing functionality.
Tests license plate extraction from video files.
"""

import sys
import os
import cv2
import numpy as np
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ocr_service import OCRService
from config.ocr_config import OCRConfig

def create_sample_video_with_license_plate(output_path: str, license_plate_text: str = "ABC123"):
    """
    Create a sample video with a license plate for testing.
    
    Args:
        output_path: Path where to save the video
        license_plate_text: Text to display as license plate
    """
    # Video properties
    width, height = 640, 480
    fps = 30
    duration_seconds = 3
    total_frames = fps * duration_seconds
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    try:
        for frame_num in range(total_frames):
            # Create a frame with a license plate
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Add some background noise
            noise = np.random.randint(0, 50, (height, width, 3), dtype=np.uint8)
            frame = cv2.add(frame, noise)
            
            # Create license plate rectangle
            plate_width, plate_height = 200, 60
            plate_x = (width - plate_width) // 2
            plate_y = (height - plate_height) // 2
            
            # Draw white rectangle for license plate
            cv2.rectangle(frame, (plate_x, plate_y), 
                         (plate_x + plate_width, plate_y + plate_height), 
                         (255, 255, 255), -1)
            
            # Draw black border
            cv2.rectangle(frame, (plate_x, plate_y), 
                         (plate_x + plate_width, plate_y + plate_height), 
                         (0, 0, 0), 2)
            
            # Add license plate text
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 1.2
            font_thickness = 2
            text_size = cv2.getTextSize(license_plate_text, font, font_scale, font_thickness)[0]
            
            text_x = plate_x + (plate_width - text_size[0]) // 2
            text_y = plate_y + (plate_height + text_size[1]) // 2
            
            cv2.putText(frame, license_plate_text, (text_x, text_y), 
                       font, font_scale, (0, 0, 0), font_thickness)
            
            # Add some movement to make it more realistic
            if frame_num > total_frames // 3:
                # Slightly move the plate position
                offset_x = int(5 * np.sin(frame_num * 0.1))
                offset_y = int(3 * np.cos(frame_num * 0.1))
                
                # Redraw with offset
                frame = np.zeros((height, width, 3), dtype=np.uint8)
                frame = cv2.add(frame, noise)
                
                new_plate_x = plate_x + offset_x
                new_plate_y = plate_y + offset_y
                
                cv2.rectangle(frame, (new_plate_x, new_plate_y), 
                             (new_plate_x + plate_width, new_plate_y + plate_height), 
                             (255, 255, 255), -1)
                cv2.rectangle(frame, (new_plate_x, new_plate_y), 
                             (new_plate_x + plate_width, new_plate_y + plate_height), 
                             (0, 0, 0), 2)
                
                new_text_x = new_plate_x + (plate_width - text_size[0]) // 2
                new_text_y = new_plate_y + (plate_height + text_size[1]) // 2
                
                cv2.putText(frame, license_plate_text, (new_text_x, new_text_y), 
                           font, font_scale, (0, 0, 0), font_thickness)
            
            out.write(frame)
        
        print(f"Sample video created: {output_path}")
        
    finally:
        out.release()

def test_ocr_pipeline():
    """Test the complete OCR pipeline with sample videos."""
    print("=== OCR Video Processing Demo ===\n")
    
    # Initialize OCR service
    try:
        ocr_service = OCRService()
        print("✓ OCR Service initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize OCR service: {e}")
        return
    
    # Create demo directory
    demo_dir = Path("demo_videos")
    demo_dir.mkdir(exist_ok=True)
    
    # Test cases with different license plates
    test_cases = [
        ("ABC123", "sample_video_abc123.mp4"),
        ("XYZ789", "sample_video_xyz789.mp4"),
        ("DEF456", "sample_video_def456.mp4"),
    ]
    
    for license_plate, video_filename in test_cases:
        print(f"\n--- Testing with license plate: {license_plate} ---")
        
        video_path = demo_dir / video_filename
        
        # Create sample video
        print(f"Creating sample video: {video_filename}")
        create_sample_video_with_license_plate(str(video_path), license_plate)
        
        # Test video validation
        print("Testing video validation...")
        is_valid = ocr_service.validate_video_file(str(video_path))
        print(f"✓ Video validation: {'PASSED' if is_valid else 'FAILED'}")
        
        if not is_valid:
            continue
        
        # Test frame extraction
        print("Testing frame extraction...")
        frames = ocr_service.extract_frames(str(video_path))
        print(f"✓ Extracted {len(frames)} frames")
        
        if frames:
            # Test preprocessing on first frame
            print("Testing frame preprocessing...")
            processed_frame = ocr_service.preprocess_frame(frames[0])
            print(f"✓ Frame preprocessed: {processed_frame.shape}")
            
            # Test text extraction
            print("Testing text extraction...")
            text_results = ocr_service.extract_text_from_frame(processed_frame)
            print(f"✓ Found {len(text_results)} text candidates")
            
            for text, confidence in text_results:
                print(f"  - Text: '{text}' (confidence: {confidence:.2f})")
        
        # Test complete video processing
        print("Testing complete video processing...")
        detected_plate = ocr_service.process_video(str(video_path))
        
        if detected_plate:
            print(f"✓ Detected license plate: {detected_plate}")
            if detected_plate == license_plate:
                print("✓ Detection SUCCESSFUL - matches expected plate")
            else:
                print(f"⚠ Detection PARTIAL - expected '{license_plate}', got '{detected_plate}'")
        else:
            print("✗ No license plate detected")
        
        # Clean up video file
        try:
            video_path.unlink()
            print(f"✓ Cleaned up video file: {video_filename}")
        except Exception as e:
            print(f"⚠ Could not clean up video file: {e}")
    
    print(f"\n=== Demo completed ===")
    print(f"Configuration used:")
    print(f"  - Max video size: {OCRConfig.MAX_VIDEO_SIZE_MB}MB")
    print(f"  - Frame sample rate: {OCRConfig.FRAME_SAMPLE_RATE}")
    print(f"  - OCR confidence threshold: {OCRConfig.OCR_CONFIDENCE_THRESHOLD}")
    print(f"  - GPU enabled: {OCRConfig.USE_GPU}")

def test_license_plate_validation():
    """Test license plate validation patterns."""
    print("\n=== License Plate Validation Test ===")
    
    ocr_service = OCRService()
    
    test_plates = [
        ("ABC123", True),
        ("XYZ789", True),
        ("AB1234", True),
        ("123ABC", True),
        ("12ABC34", True),
        ("A1B234", True),
        ("INVALID", False),
        ("12345", False),
        ("ABCDEFG", False),
        ("AB-123", False),
    ]
    
    for plate, expected in test_plates:
        result = ocr_service.validate_license_plate(plate)
        status = "✓" if result == expected else "✗"
        print(f"{status} {plate}: {result} (expected: {expected})")

if __name__ == "__main__":
    print("Starting OCR Demo...")
    
    # Test license plate validation
    test_license_plate_validation()
    
    # Test complete OCR pipeline
    test_ocr_pipeline()
    
    print("\nDemo finished!")