#!/usr/bin/env python3
"""
Create test video files for OCR demo
Generates realistic license plate videos for testing the frontend
"""

import cv2
import numpy as np
import os
from pathlib import Path
import sys

def create_license_plate_video(license_plate: str, filename: str, duration: int = 3):
    """
    Create a high-quality video with a license plate for testing.
    
    Args:
        license_plate: Text to display on license plate
        filename: Output video filename
        duration: Video duration in seconds
    """
    print(f"🎬 Creating video: {filename} with plate: {license_plate}")
    
    # Video properties
    width, height = 1280, 720  # HD resolution
    fps = 30
    total_frames = fps * duration
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    
    try:
        for frame_num in range(total_frames):
            # Create realistic background (road/parking lot)
            frame = create_realistic_background(width, height, frame_num)
            
            # Add license plate
            frame = add_license_plate(frame, license_plate, frame_num, total_frames)
            
            # Add some camera shake for realism
            if frame_num > total_frames // 4:
                shake_x = int(2 * np.sin(frame_num * 0.3))
                shake_y = int(1 * np.cos(frame_num * 0.4))
                frame = apply_camera_shake(frame, shake_x, shake_y)
            
            out.write(frame)
        
        print(f"✅ Video created: {filename} ({total_frames} frames)")
        
    finally:
        out.release()
    
    return filename

def create_realistic_background(width: int, height: int, frame_num: int):
    """Create a realistic road/parking background."""
    # Create gradient background (asphalt-like)
    background = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Asphalt gray gradient
    for y in range(height):
        gray_value = int(40 + (y / height) * 30)  # 40-70 gray range
        background[y, :] = [gray_value, gray_value, gray_value]
    
    # Add some texture/noise
    noise = np.random.randint(-10, 10, (height, width, 3), dtype=np.int16)
    background = np.clip(background.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    # Add road markings
    add_road_markings(background, width, height)
    
    # Add some lighting variation
    add_lighting_effects(background, width, height, frame_num)
    
    return background

def add_road_markings(background, width, height):
    """Add road markings for realism."""
    # Add lane lines
    line_color = (200, 200, 200)
    
    # Horizontal lines (parking spaces)
    for y in range(height // 4, height, height // 8):
        cv2.line(background, (0, y), (width, y), line_color, 2)
    
    # Vertical lines
    for x in range(width // 6, width, width // 4):
        cv2.line(background, (x, height // 3), (x, height), line_color, 2)

def add_lighting_effects(background, width, height, frame_num):
    """Add subtle lighting effects."""
    # Create a subtle lighting gradient
    center_x, center_y = width // 2, height // 3
    
    for y in range(height):
        for x in range(width):
            distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            max_distance = np.sqrt(width**2 + height**2)
            
            # Subtle brightness variation
            brightness_factor = 1.0 + 0.1 * (1 - distance / max_distance)
            
            # Apply brightness
            background[y, x] = np.clip(background[y, x] * brightness_factor, 0, 255)

def add_license_plate(frame, license_plate: str, frame_num: int, total_frames: int):
    """Add a realistic license plate to the frame."""
    height, width = frame.shape[:2]
    
    # License plate dimensions and position
    plate_width = int(width * 0.25)  # 25% of frame width
    plate_height = int(plate_width * 0.3)  # Standard plate ratio
    
    # Position (slightly moving for realism)
    base_x = (width - plate_width) // 2
    base_y = int(height * 0.6)  # Lower part of frame
    
    # Add subtle movement
    if frame_num > total_frames // 4:
        offset_x = int(15 * np.sin(frame_num * 0.1))
        offset_y = int(8 * np.cos(frame_num * 0.15))
        plate_x = base_x + offset_x
        plate_y = base_y + offset_y
    else:
        plate_x, plate_y = base_x, base_y
    
    # Ensure plate stays in frame
    plate_x = max(10, min(plate_x, width - plate_width - 10))
    plate_y = max(10, min(plate_y, height - plate_height - 10))
    
    # Create license plate background
    plate_bg = (255, 255, 255)  # White background
    cv2.rectangle(frame, (plate_x, plate_y), 
                 (plate_x + plate_width, plate_y + plate_height), 
                 plate_bg, -1)
    
    # Add plate border
    border_color = (0, 0, 0)  # Black border
    cv2.rectangle(frame, (plate_x, plate_y), 
                 (plate_x + plate_width, plate_y + plate_height), 
                 border_color, 4)
    
    # Add inner border for realism
    inner_border = (100, 100, 100)
    cv2.rectangle(frame, (plate_x + 8, plate_y + 8), 
                 (plate_x + plate_width - 8, plate_y + plate_height - 8), 
                 inner_border, 2)
    
    # Add license plate text
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = plate_width / 200.0  # Scale based on plate size
    font_thickness = max(2, int(font_scale * 2))
    
    # Calculate text size and position
    text_size = cv2.getTextSize(license_plate, font, font_scale, font_thickness)[0]
    text_x = plate_x + (plate_width - text_size[0]) // 2
    text_y = plate_y + (plate_height + text_size[1]) // 2
    
    # Add text shadow for depth
    shadow_offset = 2
    cv2.putText(frame, license_plate, 
               (text_x + shadow_offset, text_y + shadow_offset), 
               font, font_scale, (128, 128, 128), font_thickness)
    
    # Add main text
    cv2.putText(frame, license_plate, (text_x, text_y), 
               font, font_scale, (0, 0, 0), font_thickness)
    
    # Add some wear/aging effects
    add_plate_effects(frame, plate_x, plate_y, plate_width, plate_height)
    
    return frame

def add_plate_effects(frame, plate_x, plate_y, plate_width, plate_height):
    """Add realistic wear and aging effects to license plate."""
    # Add subtle scratches
    for _ in range(3):
        start_x = plate_x + np.random.randint(10, plate_width - 10)
        start_y = plate_y + np.random.randint(10, plate_height - 10)
        end_x = start_x + np.random.randint(-20, 20)
        end_y = start_y + np.random.randint(-5, 5)
        
        cv2.line(frame, (start_x, start_y), (end_x, end_y), (200, 200, 200), 1)
    
    # Add slight dirt/aging
    for _ in range(5):
        spot_x = plate_x + np.random.randint(0, plate_width)
        spot_y = plate_y + np.random.randint(0, plate_height)
        spot_size = np.random.randint(1, 3)
        
        cv2.circle(frame, (spot_x, spot_y), spot_size, (220, 220, 220), -1)

def apply_camera_shake(frame, shake_x, shake_y):
    """Apply subtle camera shake effect."""
    height, width = frame.shape[:2]
    
    # Create transformation matrix
    M = np.float32([[1, 0, shake_x], [0, 1, shake_y]])
    
    # Apply transformation
    shaken_frame = cv2.warpAffine(frame, M, (width, height), 
                                 borderMode=cv2.BORDER_REPLICATE)
    
    return shaken_frame

def create_test_video_set():
    """Create a set of test videos with different license plates."""
    # Create output directory
    output_dir = Path("test_videos")
    output_dir.mkdir(exist_ok=True)
    
    # Test cases with different license plates
    test_cases = [
        ("ABC123", "demo_abc123.mp4"),
        ("XYZ789", "demo_xyz789.mp4"), 
        ("DEF456", "demo_def456.mp4"),
        ("TEST01", "demo_test01.mp4"),
        ("DEMO99", "demo_demo99.mp4"),
    ]
    
    created_videos = []
    
    print("🎬 Creating test video set...")
    print("=" * 50)
    
    for license_plate, filename in test_cases:
        video_path = output_dir / filename
        create_license_plate_video(license_plate, str(video_path), duration=4)
        created_videos.append(str(video_path))
        
        # Show file size
        file_size = os.path.getsize(video_path)
        print(f"   📁 Size: {file_size / 1024 / 1024:.1f} MB")
        print()
    
    print("=" * 50)
    print(f"✅ Created {len(created_videos)} test videos")
    print(f"📁 Location: {output_dir.absolute()}")
    print()
    print("🎯 How to use:")
    print("1. Start your backend: uvicorn main:app --reload")
    print("2. Open web-dashboard/index.html")
    print("3. Drag and drop any of these videos to test OCR")
    print()
    
    return created_videos

def main():
    """Main function to create test videos."""
    print("🎬 Test Video Creator for Smart Campus Access Control")
    print("=" * 60)
    
    try:
        videos = create_test_video_set()
        
        print("🎉 All test videos created successfully!")
        print()
        print("📋 Available test videos:")
        for i, video in enumerate(videos, 1):
            filename = Path(video).name
            plate = filename.split('_')[1].split('.')[0].upper()
            print(f"   {i}. {filename} → License Plate: {plate}")
        
    except Exception as e:
        print(f"❌ Error creating videos: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()