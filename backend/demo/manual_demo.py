#!/usr/bin/env python3
"""
Manual Interactive Demo for Smart Campus Access Control
Allows user to input license plates and test the OCR system
"""

import sys
import os
import cv2
import numpy as np
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

def create_video_with_plate(license_plate: str, filename: str) -> str:
    """Create a video with user's license plate."""
    print(f"🎬 Creating video with license plate: {license_plate}")
    
    # Video properties
    width, height = 640, 480
    fps = 15
    duration_seconds = 2
    total_frames = fps * duration_seconds
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    
    try:
        for frame_num in range(total_frames):
            # Create a clean frame
            frame = np.ones((height, width, 3), dtype=np.uint8) * 40  # Dark background
            
            # Add some texture
            noise = np.random.randint(0, 20, (height, width, 3), dtype=np.uint8)
            frame = cv2.add(frame, noise)
            
            # Create license plate rectangle (large and clear)
            plate_width, plate_height = 300, 80
            plate_x = (width - plate_width) // 2
            plate_y = (height - plate_height) // 2
            
            # Add slight movement for realism
            if frame_num > total_frames // 4:
                offset_x = int(8 * np.sin(frame_num * 0.3))
                offset_y = int(4 * np.cos(frame_num * 0.2))
                plate_x += offset_x
                plate_y += offset_y
            
            # Draw white rectangle for license plate
            cv2.rectangle(frame, (plate_x, plate_y), 
                         (plate_x + plate_width, plate_y + plate_height), 
                         (255, 255, 255), -1)
            
            # Draw black border
            cv2.rectangle(frame, (plate_x, plate_y), 
                         (plate_x + plate_width, plate_y + plate_height), 
                         (0, 0, 0), 4)
            
            # Add license plate text (large and clear)
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 2.2
            font_thickness = 4
            text_size = cv2.getTextSize(license_plate, font, font_scale, font_thickness)[0]
            
            text_x = plate_x + (plate_width - text_size[0]) // 2
            text_y = plate_y + (plate_height + text_size[1]) // 2
            
            cv2.putText(frame, license_plate, (text_x, text_y), 
                       font, font_scale, (0, 0, 0), font_thickness)
            
            # Add frame info
            cv2.putText(frame, f"Frame: {frame_num+1}/{total_frames}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            out.write(frame)
        
        print(f"✅ Video created: {filename}")
        
    finally:
        out.release()
    
    return filename

def test_ocr_with_plate(license_plate: str):
    """Test OCR system with user's license plate."""
    try:
        from services.ocr_service import OCRService
        
        print(f"\n🔍 Testing OCR with license plate: {license_plate}")
        
        # Create temporary video file
        temp_dir = Path("temp_videos")
        temp_dir.mkdir(exist_ok=True)
        
        video_filename = temp_dir / f"manual_test_{license_plate.replace(' ', '_')}.mp4"
        
        # Create video with user's license plate
        create_video_with_plate(license_plate, str(video_filename))
        
        # Initialize OCR service
        print("🤖 Initializing OCR service...")
        ocr_service = OCRService()
        
        # Test video validation
        print("📋 Validating video file...")
        is_valid = ocr_service.validate_video_file(str(video_filename))
        print(f"   Video validation: {'✅ PASSED' if is_valid else '❌ FAILED'}")
        
        if not is_valid:
            return
        
        # Test frame extraction
        print("🎞️ Extracting frames...")
        frames = ocr_service.extract_frames(str(video_filename))
        print(f"   Extracted {len(frames)} frames")
        
        if frames:
            # Test preprocessing
            print("🔧 Preprocessing frames...")
            processed_frame = ocr_service.preprocess_frame(frames[0])
            print(f"   Frame preprocessed: {processed_frame.shape}")
            
            # Test text extraction
            print("📖 Extracting text from frames...")
            text_results = ocr_service.extract_text_from_frame(processed_frame)
            print(f"   Found {len(text_results)} text candidates:")
            
            for text, confidence in text_results:
                print(f"     - '{text}' (confidence: {confidence:.2f})")
        
        # Test complete video processing
        print("🎯 Running complete OCR processing...")
        detected_plate = ocr_service.process_video(str(video_filename))
        
        print(f"\n{'='*50}")
        print(f"🎯 RESULTS:")
        print(f"{'='*50}")
        print(f"Input License Plate:    {license_plate}")
        print(f"Detected License Plate: {detected_plate or 'None detected'}")
        
        if detected_plate:
            if detected_plate.upper() == license_plate.upper():
                print(f"✅ SUCCESS: Perfect match!")
            else:
                print(f"⚠️  PARTIAL: Close but not exact match")
        else:
            print(f"❌ FAILED: No license plate detected")
        
        # Test license plate validation
        if detected_plate:
            is_valid_pattern = ocr_service.validate_license_plate(detected_plate)
            print(f"Pattern validation: {'✅ Valid' if is_valid_pattern else '❌ Invalid'}")
        
        print(f"{'='*50}")
        
        # Clean up
        try:
            video_filename.unlink()
            print(f"🧹 Cleaned up temporary file")
        except:
            pass
            
    except ImportError as e:
        print(f"❌ OCR service not available: {e}")
        print("   Make sure dependencies are installed: pip install opencv-python easyocr")
    except Exception as e:
        print(f"❌ Error during OCR testing: {e}")

def test_license_plate_patterns():
    """Test license plate validation patterns."""
    print("\n🔍 Testing License Plate Validation Patterns:")
    print("-" * 50)
    
    try:
        from services.ocr_service import OCRService
        ocr_service = OCRService()
        
        test_plates = [
            "ABC123", "XYZ789", "AB1234", "123ABC", 
            "DEF456", "GHI789", "12ABC34", "A1B234",
            "INVALID", "12345", "ABCDEFG", "AB-123"
        ]
        
        for plate in test_plates:
            is_valid = ocr_service.validate_license_plate(plate)
            status = "✅ Valid" if is_valid else "❌ Invalid"
            print(f"  {plate:<10} → {status}")
            
    except Exception as e:
        print(f"❌ Error testing patterns: {e}")

def main():
    """Main interactive demo function."""
    print("🚗 Smart Campus Access Control - Manual Demo")
    print("=" * 60)
    
    while True:
        print("\n📋 Choose an option:")
        print("1. Test OCR with your license plate")
        print("2. Test license plate validation patterns")
        print("3. Exit")
        
        try:
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == "1":
                print("\n" + "="*50)
                license_plate = input("🚗 Enter license plate to test: ").strip().upper()
                
                if not license_plate:
                    print("❌ Please enter a valid license plate")
                    continue
                
                if len(license_plate) > 10:
                    print("❌ License plate too long (max 10 characters)")
                    continue
                
                print(f"\n🎯 Testing with license plate: {license_plate}")
                test_ocr_with_plate(license_plate)
                
            elif choice == "2":
                test_license_plate_patterns()
                
            elif choice == "3":
                print("\n👋 Thanks for testing the Smart Campus Access Control system!")
                break
                
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Demo interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()