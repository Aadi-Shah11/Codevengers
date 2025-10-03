"""
Demo script for testing video upload endpoint with OCR functionality.
"""

import requests
import cv2
import numpy as np
import tempfile
import os
import sys
import time

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_demo_video(filename: str, license_plate: str = "ABC123") -> str:
    """Create a demo video with a license plate for testing."""
    print(f"Creating demo video: {filename} with plate: {license_plate}")
    
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
            # Create a frame with a license plate
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Add some background texture
            noise = np.random.randint(0, 30, (height, width, 3), dtype=np.uint8)
            frame = cv2.add(frame, noise)
            
            # Create license plate rectangle
            plate_width, plate_height = 200, 60
            plate_x = (width - plate_width) // 2
            plate_y = (height - plate_height) // 2
            
            # Add slight movement
            if frame_num > total_frames // 4:
                offset_x = int(10 * np.sin(frame_num * 0.2))
                offset_y = int(5 * np.cos(frame_num * 0.15))
                plate_x += offset_x
                plate_y += offset_y
            
            # Draw white rectangle for license plate
            cv2.rectangle(frame, (plate_x, plate_y), 
                         (plate_x + plate_width, plate_y + plate_height), 
                         (255, 255, 255), -1)
            
            # Draw black border
            cv2.rectangle(frame, (plate_x, plate_y), 
                         (plate_x + plate_width, plate_y + plate_height), 
                         (0, 0, 0), 3)
            
            # Add license plate text
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 1.5
            font_thickness = 3
            text_size = cv2.getTextSize(license_plate, font, font_scale, font_thickness)[0]
            
            text_x = plate_x + (plate_width - text_size[0]) // 2
            text_y = plate_y + (plate_height + text_size[1]) // 2
            
            cv2.putText(frame, license_plate, (text_x, text_y), 
                       font, font_scale, (0, 0, 0), font_thickness)
            
            # Add frame number for debugging
            cv2.putText(frame, f"Frame: {frame_num}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            out.write(frame)
        
        print(f"✓ Demo video created: {filename} ({total_frames} frames)")
        
    finally:
        out.release()
    
    return filename

def test_video_upload_api(video_path: str, base_url: str = "http://localhost:8000"):
    """Test the video upload API endpoint."""
    print(f"\n--- Testing Video Upload API ---")
    print(f"Video file: {video_path}")
    print(f"API URL: {base_url}/vehicles/upload_video")
    
    try:
        # Check if file exists
        if not os.path.exists(video_path):
            print(f"✗ Video file not found: {video_path}")
            return False
        
        file_size = os.path.getsize(video_path)
        print(f"File size: {file_size} bytes ({file_size / 1024:.1f} KB)")
        
        # Prepare the request
        with open(video_path, 'rb') as video_file:
            files = {
                'video_file': ('demo_video.mp4', video_file, 'video/mp4')
            }
            params = {
                'gate_id': 'DEMO_GATE'
            }
            
            print("Uploading video...")
            start_time = time.time()
            
            # Make the request
            response = requests.post(
                f"{base_url}/vehicles/upload_video",
                files=files,
                params=params,
                timeout=30
            )
            
            upload_time = time.time() - start_time
            print(f"Upload completed in {upload_time:.2f} seconds")
        
        # Check response
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Upload successful!")
            print(f"  - Filename: {data.get('filename')}")
            print(f"  - File size: {data.get('file_size')} bytes")
            print(f"  - Processing time: {data.get('processing_time')} seconds")
            
            ocr_results = data.get('ocr_results', {})
            print(f"  - OCR method: {ocr_results.get('method')}")
            print(f"  - Detection status: {ocr_results.get('detection_status')}")
            
            if ocr_results.get('license_plate'):
                print(f"  - Detected plate: {ocr_results.get('license_plate')}")
                print(f"  - Confidence: {ocr_results.get('confidence', 'N/A')}")
            
            verification = data.get('verification', {})
            print(f"  - Access granted: {verification.get('access_granted')}")
            print(f"  - Decision reason: {verification.get('decision_reason')}")
            
            print(f"  - Message: {data.get('message')}")
            
            return True
            
        else:
            print(f"✗ Upload failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"  Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"  Error: {response.text}")
            
            return False
    
    except requests.exceptions.ConnectionError:
        print("✗ Connection failed - is the API server running?")
        print("  Start the server with: uvicorn main:app --reload")
        return False
    except requests.exceptions.Timeout:
        print("✗ Request timed out")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_invalid_uploads(base_url: str = "http://localhost:8000"):
    """Test invalid upload scenarios."""
    print(f"\n--- Testing Invalid Upload Scenarios ---")
    
    # Test 1: Invalid file type
    print("\n1. Testing invalid file type...")
    try:
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_file.write(b"This is not a video file")
            temp_file.flush()
            
            with open(temp_file.name, 'rb') as f:
                files = {'video_file': ('test.txt', f, 'text/plain')}
                response = requests.post(f"{base_url}/vehicles/upload_video", files=files)
            
            if response.status_code == 400:
                print("✓ Correctly rejected invalid file type")
            else:
                print(f"✗ Unexpected response: {response.status_code}")
            
            os.unlink(temp_file.name)
    except Exception as e:
        print(f"✗ Error testing invalid file type: {e}")
    
    # Test 2: Unsupported video format
    print("\n2. Testing unsupported video format...")
    try:
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as temp_file:
            temp_file.write(b"fake webm content")
            temp_file.flush()
            
            with open(temp_file.name, 'rb') as f:
                files = {'video_file': ('test.webm', f, 'video/webm')}
                response = requests.post(f"{base_url}/vehicles/upload_video", files=files)
            
            if response.status_code == 400:
                print("✓ Correctly rejected unsupported format")
            else:
                print(f"✗ Unexpected response: {response.status_code}")
            
            os.unlink(temp_file.name)
    except Exception as e:
        print(f"✗ Error testing unsupported format: {e}")

def main():
    """Main demo function."""
    print("=== Video Upload OCR Demo ===")
    
    # Create demo directory
    demo_dir = "demo_videos"
    os.makedirs(demo_dir, exist_ok=True)
    
    # Test cases
    test_cases = [
        ("ABC123", "demo_abc123.mp4"),
        ("XYZ789", "demo_xyz789.mp4"),
        ("DEF456", "demo_def456.mp4"),
    ]
    
    base_url = "http://localhost:8000"
    
    print(f"Testing against API server: {base_url}")
    print("Make sure the FastAPI server is running with: uvicorn main:app --reload")
    
    # Test each case
    for license_plate, filename in test_cases:
        video_path = os.path.join(demo_dir, filename)
        
        print(f"\n{'='*50}")
        print(f"Test Case: {license_plate}")
        print(f"{'='*50}")
        
        # Create demo video
        create_demo_video(video_path, license_plate)
        
        # Test upload
        success = test_video_upload_api(video_path, base_url)
        
        # Clean up
        try:
            os.unlink(video_path)
            print(f"✓ Cleaned up: {video_path}")
        except Exception as e:
            print(f"⚠ Could not clean up {video_path}: {e}")
        
        if not success:
            print(f"⚠ Test failed for {license_plate}")
    
    # Test invalid scenarios
    test_invalid_uploads(base_url)
    
    print(f"\n{'='*50}")
    print("Demo completed!")
    print("Note: Some tests may fail if the database is not set up or server is not running.")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()