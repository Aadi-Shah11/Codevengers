"""
Test cases for OCR service functionality.
"""

import pytest
import numpy as np
import cv2
import tempfile
import os
from unittest.mock import Mock, patch

from services.ocr_service import OCRService
from config.ocr_config import OCRConfig


class TestOCRService:
    """Test cases for OCR service."""
    
    @pytest.fixture
    def ocr_service(self):
        """Create OCR service instance for testing."""
        with patch('easyocr.Reader'):
            service = OCRService()
            service.reader = Mock()
            return service
    
    def test_validate_license_plate_valid_patterns(self, ocr_service):
        """Test license plate validation with valid patterns."""
        valid_plates = [
            "ABC123",
            "AB1234", 
            "123ABC",
            "12ABC34",
            "A1B234"
        ]
        
        for plate in valid_plates:
            assert ocr_service.validate_license_plate(plate), f"Should validate {plate}"
    
    def test_validate_license_plate_invalid_patterns(self, ocr_service):
        """Test license plate validation with invalid patterns."""
        invalid_plates = [
            "A",
            "12",
            "ABCDEFG",
            "1234567",
            "AB-123",  # Hyphens are not removed, so this should be invalid
            "A1B2C3D4E5"  # Too long
        ]
        
        for plate in invalid_plates:
            assert not ocr_service.validate_license_plate(plate), f"Should not validate {plate}"
    
    def test_validate_license_plate_case_insensitive(self, ocr_service):
        """Test that license plate validation is case insensitive."""
        assert ocr_service.validate_license_plate("abc123")
        assert ocr_service.validate_license_plate("ABC123")
        assert ocr_service.validate_license_plate("AbC123")
    
    def test_validate_license_plate_with_spaces(self, ocr_service):
        """Test license plate validation removes spaces."""
        assert ocr_service.validate_license_plate("ABC 123")
        assert ocr_service.validate_license_plate("A BC1 23")
    
    def test_preprocess_frame(self, ocr_service):
        """Test frame preprocessing."""
        # Create a simple test frame
        frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        processed = ocr_service.preprocess_frame(frame)
        
        # Check that output is grayscale
        assert len(processed.shape) == 2, "Processed frame should be grayscale"
        assert processed.shape == (100, 100), "Processed frame should maintain dimensions"
    
    def test_extract_text_from_frame(self, ocr_service):
        """Test text extraction from frame."""
        # Mock EasyOCR results
        mock_results = [
            ([(0, 0), (100, 0), (100, 50), (0, 50)], "ABC123", 0.85),
            ([(0, 60), (100, 60), (100, 110), (0, 110)], "INVALID", 0.6),
        ]
        ocr_service.reader.readtext.return_value = mock_results
        
        frame = np.zeros((100, 100), dtype=np.uint8)
        results = ocr_service.extract_text_from_frame(frame)
        
        # Should only return results above confidence threshold
        assert len(results) == 1
        assert results[0] == ("ABC123", 0.85)
    
    def test_save_uploaded_file(self, ocr_service):
        """Test saving uploaded file to temporary location."""
        test_content = b"test video content"
        filename = "test_video.mp4"
        
        temp_path = ocr_service.save_uploaded_file(test_content, filename)
        
        try:
            # Check file was created
            assert os.path.exists(temp_path)
            
            # Check content is correct
            with open(temp_path, 'rb') as f:
                saved_content = f.read()
            assert saved_content == test_content
            
            # Check file extension is preserved
            assert temp_path.endswith('.mp4')
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_cleanup_temp_file(self, ocr_service):
        """Test temporary file cleanup."""
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        # Verify file exists
        assert os.path.exists(temp_path)
        
        # Clean up file
        ocr_service.cleanup_temp_file(temp_path)
        
        # Verify file is deleted (if cleanup is enabled)
        if OCRConfig.CLEANUP_TEMP_FILES:
            assert not os.path.exists(temp_path)
    
    def test_validate_video_file_nonexistent(self, ocr_service):
        """Test validation of non-existent video file."""
        assert not ocr_service.validate_video_file("/nonexistent/path.mp4")
    
    @patch('cv2.VideoCapture')
    def test_validate_video_file_cannot_open(self, mock_cv2, ocr_service):
        """Test validation when OpenCV cannot open video."""
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        try:
            # Mock VideoCapture to return unopened capture
            mock_cap = Mock()
            mock_cap.isOpened.return_value = False
            mock_cv2.return_value = mock_cap
            
            assert not ocr_service.validate_video_file(temp_path)
            
        finally:
            os.unlink(temp_path)
    
    def test_config_integration(self):
        """Test that OCR service integrates with configuration properly."""
        # Test that configuration values are accessible
        assert OCRConfig.MAX_VIDEO_SIZE_MB > 0
        assert OCRConfig.FRAME_SAMPLE_RATE > 0
        assert 0 < OCRConfig.OCR_CONFIDENCE_THRESHOLD <= 1
        assert len(OCRConfig.LICENSE_PLATE_PATTERNS) > 0
        assert len(OCRConfig.SUPPORTED_VIDEO_FORMATS) > 0