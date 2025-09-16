import tempfile
import os
from PIL import Image

class ImageSearchHandler:
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
    
    def prepare_image_for_search(self, pil_image: Image.Image):
        """Simple image preparation"""
        # Save to temporary file
        temp_path = os.path.join(self.temp_dir, "circle_search_temp.jpg")
        pil_image.save(temp_path, "JPEG", quality=85)
        
        # Read as bytes
        with open(temp_path, 'rb') as f:
            image_bytes = f.read()
        
        return image_bytes, temp_path
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        temp_path = os.path.join(self.temp_dir, "circle_search_temp.jpg")
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception as e:
            print(f"[WARNING] Could not clean up temp file: {e}")