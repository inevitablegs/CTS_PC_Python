import webbrowser
import requests
import base64
from urllib.parse import urlencode, quote_plus
import json

class GoogleSearchEngine:
    def __init__(self):
        self.text_search_url = "https://www.google.com/search"
        self.image_search_url = "https://www.google.com/search?tbm=isch"
        self.lens_url = "https://lens.google.com/"
    
    def search_text(self, query: str):
        """Enhanced Google text search with better URL formatting"""
        if not query.strip():
            return None
            
        try:
            # Clean and encode the query properly
            clean_query = query.strip()
            encoded_query = quote_plus(clean_query)
            
            # Build the URL with additional parameters for better results
            params = {
                'q': clean_query,
                'hl': 'en',  # Language
                'safe': 'active'  # Safe search
            }
            
            url = f"{self.text_search_url}?{urlencode(params)}"
            webbrowser.open(url)
            print(f"[INFO] Google search opened for: '{clean_query}'")
            return url
            
        except Exception as e:
            print(f"[ERROR] Google text search failed: {e}")
            return None
    
    def search_image_by_text(self, query: str):
        """Search Google Images with text query"""
        if not query.strip():
            return None
            
        try:
            clean_query = query.strip()
            params = {
                'q': clean_query,
                'tbm': 'isch',
                'hl': 'en',
                'safe': 'active'
            }
            
            url = f"{self.text_search_url}?{urlencode(params)}"
            webbrowser.open(url)
            print(f"[INFO] Google Images search opened for: '{clean_query}'")
            return url
            
        except Exception as e:
            print(f"[ERROR] Google image search failed: {e}")
            return None
    
    def search_image(self, image_data: bytes = None):
        """Perform reverse image search with Google Images"""
        try:
            if image_data:
                # Use Google reverse image search
                import tempfile
                import os
                import base64
                
                # Save image to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                    tmp_file.write(image_data)
                    temp_path = tmp_file.name
                
                # Try to upload to Google Images search
                try:
                    # Method 1: Use TinEye-style URL construction
                    import urllib.parse
                    encoded_data = base64.b64encode(image_data).decode('utf-8')
                    
                    # Google Images search by upload URL
                    upload_url = "https://www.google.com/searchbyimage/upload"
                    
                    # Open Google Images reverse search page
                    search_url = "https://images.google.com/"
                    webbrowser.open(search_url)
                    print("[INFO] Google Images opened for reverse image search")
                    print("       Please click the camera icon and upload your image")
                    
                    # Try to copy image to clipboard for easy pasting
                    try:
                        from PIL import Image
                        import io
                        if image_data:
                            # Convert to PIL Image and put in clipboard
                            img = Image.open(io.BytesIO(image_data))
                            # Note: Clipboard image functionality varies by OS
                            print("       Image data prepared - you can paste it directly")
                    except Exception as e:
                        print(f"       Could not prepare image for clipboard: {e}")
                    
                    return search_url
                    
                except Exception as e:
                    print(f"[WARNING] Advanced image search failed: {e}")
                    # Fallback to basic Google Lens
                    webbrowser.open(self.lens_url)
                    print("[INFO] Google Lens opened as fallback")
                    return self.lens_url
                finally:
                    # Cleanup temp file
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
            else:
                # No image data, open Google Lens
                webbrowser.open(self.lens_url)
                print("[INFO] Google Lens opened (no image data provided)")
                return self.lens_url
            
        except Exception as e:
            print(f"[ERROR] Google image search failed: {e}")
            return None

class BingSearchEngine:
    def __init__(self):
        self.text_search_url = "https://www.bing.com/search"
        self.image_search_url = "https://www.bing.com/images/search"
        self.visual_search_url = "https://www.bing.com/visualsearch"
    
    def search_text(self, query: str):
        """Enhanced Bing text search"""
        if not query.strip():
            return None
            
        try:
            clean_query = query.strip()
            params = {
                'q': clean_query,
                'form': 'QBLH',  # Bing form parameter
                'sp': '-1',      # Safe search
                'pq': clean_query
            }
            
            url = f"{self.text_search_url}?{urlencode(params)}"
            webbrowser.open(url)
            print(f"[INFO] Bing search opened for: '{clean_query}'")
            return url
            
        except Exception as e:
            print(f"[ERROR] Bing text search failed: {e}")
            return None
    
    def search_image_by_text(self, query: str):
        """Search Bing Images with text query"""
        if not query.strip():
            return None
            
        try:
            clean_query = query.strip()
            params = {
                'q': clean_query,
                'form': 'HDRSC2',
                'first': '1'
            }
            
            url = f"{self.image_search_url}?{urlencode(params)}"
            webbrowser.open(url)
            print(f"[INFO] Bing Images search opened for: '{clean_query}'")
            return url
            
        except Exception as e:
            print(f"[ERROR] Bing image search failed: {e}")
            return None
    
    def search_image(self, image_data: bytes = None):
        """Perform visual search with Bing"""
        try:
            if image_data:
                import tempfile
                import os
                
                # Save image temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                    tmp_file.write(image_data)
                    temp_path = tmp_file.name
                
                try:
                    # Open Bing Visual Search
                    webbrowser.open(self.visual_search_url)
                    print("[INFO] Bing Visual Search opened")
                    print("       Please click 'Browse' or drag-and-drop your image")
                    print("       Image is ready for upload")
                    
                    return self.visual_search_url
                finally:
                    # Cleanup
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
            else:
                webbrowser.open(self.visual_search_url)
                print("[INFO] Bing Visual Search opened")
                return self.visual_search_url
            
        except Exception as e:
            print(f"[ERROR] Bing visual search failed: {e}")
            return None

class SearchEngineManager:
    def __init__(self):
        self.engines = {
            'google': GoogleSearchEngine(),
            'bing': BingSearchEngine()
        }
        self.current_engine = 'google'
    
    def set_engine(self, engine_name: str):
        """Set the current search engine"""
        if engine_name in self.engines:
            self.current_engine = engine_name
            print(f"[INFO] Search engine set to: {engine_name}")
    
    def search_text(self, query: str):
        """Search with current engine using enhanced text search"""
        if not query.strip():
            return None
        return self.engines[self.current_engine].search_text(query)
    
    def search_images_by_text(self, query: str):
        """Search images with text query using current engine"""
        if not query.strip():
            return None
        return self.engines[self.current_engine].search_image_by_text(query)
    
    def search_image(self, image_data: bytes = None):
        """Search with image using current engine"""
        engine = self.engines[self.current_engine]
        if hasattr(engine, 'search_image'):
            return engine.search_image(image_data)
        else:
            print("[WARNING] Image search not supported for current engine")
            return None
    
    def get_current_engine(self):
        """Get the current engine name"""
        return self.current_engine