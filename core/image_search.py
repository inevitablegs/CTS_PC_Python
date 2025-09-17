import tempfile
import os
import io
import base64
import webbrowser
import subprocess
from PIL import Image

class ImageSearchHandler:
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
    
    def prepare_image_for_search(self, pil_image: Image.Image):
        """Prepare image for search with multiple formats"""
        # Save to temporary file (JPEG for compatibility)
        temp_path = os.path.join(self.temp_dir, "circle_search_temp.jpg")
        
        # Optimize image for web upload (reduce size if too large)
        img = pil_image.copy()
        
        # Resize if image is too large (max 1920x1080 for faster upload)
        max_size = (1920, 1080)
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            print(f"[INFO] Image resized to {img.size} for faster search")
        
        # Save optimized image
        img.save(temp_path, "JPEG", quality=85, optimize=True)
        
        # Read as bytes
        with open(temp_path, 'rb') as f:
            image_bytes = f.read()
        
        print(f"[INFO] Image prepared: {len(image_bytes)} bytes")
        return image_bytes, temp_path
    
    def save_to_desktop_for_upload(self, pil_image: Image.Image):
        """Save image to desktop for easy manual upload"""
        try:
            import os
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            if not os.path.exists(desktop_path):
                desktop_path = os.path.expanduser("~")  # Fallback to home directory
            
            image_path = os.path.join(desktop_path, "circle_search_image.jpg")
            
            # Optimize image
            img = pil_image.copy()
            max_size = (1920, 1080)
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            img.save(image_path, "JPEG", quality=90, optimize=True)
            print(f"[INFO] Image saved to desktop: {image_path}")
            
            return image_path
        except Exception as e:
            print(f"[ERROR] Could not save to desktop: {e}")
            return None
    
    def copy_to_clipboard_windows(self, pil_image: Image.Image):
        """Copy image to clipboard on Windows"""
        try:
            import io
            import win32clipboard
            from PIL import Image
            
            # Convert to bitmap format for clipboard
            output = io.BytesIO()
            pil_image.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]  # Remove BMP header
            output.close()
            
            # Copy to clipboard
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
            
            print("[INFO] Image copied to clipboard!")
            return True
            
        except ImportError:
            print("[INFO] win32clipboard not available")
            return False
        except Exception as e:
            print(f"[ERROR] Could not copy to clipboard: {e}")
            return False
    
    def perform_advanced_search(self, pil_image: Image.Image, search_engine="google"):
        """Perform advanced image search with multiple fallback methods"""
        try:
            # Method 1: Try to copy to clipboard for easy pasting
            clipboard_success = self.copy_to_clipboard_windows(pil_image)
            
            # Method 2: Save to desktop as backup
            desktop_path = self.save_to_desktop_for_upload(pil_image)
            
            # Method 3: Open the search engine
            if search_engine == "google":
                search_url = "https://images.google.com/"
                upload_hint = "Click the camera icon 📷 and paste or upload your image"
            else:  # bing
                search_url = "https://www.bing.com/visualsearch"
                upload_hint = "Click 'Browse' or drag-and-drop your image"
            
            webbrowser.open(search_url)
            
            # Provide user instructions
            print(f"[INFO] {search_engine.title()} opened for image search")
            
            if clipboard_success:
                print("✅ Image copied to clipboard - you can paste it directly!")
            elif desktop_path:
                print(f"✅ Image saved to: {desktop_path}")
                print("   You can upload this file to the search page")
            
            print(f"📖 Instructions: {upload_hint}")
            
            return search_url
            
        except Exception as e:
            print(f"[ERROR] Advanced search failed: {e}")
            return None
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        temp_files = [
            os.path.join(self.temp_dir, "circle_search_temp.jpg"),
            os.path.join(os.path.expanduser("~"), "Desktop", "circle_search_image.jpg")
        ]
        
        for temp_path in temp_files:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    print(f"[INFO] Cleaned up: {temp_path}")
            except Exception as e:
                print(f"[WARNING] Could not clean up {temp_path}: {e}")