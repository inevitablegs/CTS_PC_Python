from PIL import Image, ImageDraw
import os

# Create a simple icon
img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Draw a search circle
draw.ellipse([10, 10, 54, 54], outline=(0, 100, 255, 255), width=4)
draw.ellipse([35, 35, 45, 45], fill=(0, 100, 255, 255))

# Create assets directory if it doesn't exist
os.makedirs('assets', exist_ok=True)

# Save the icon
img.save('assets/icon.png')
print("Icon created at assets/icon.png")