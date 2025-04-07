import cv2
import numpy as np
import os
from PIL import Image, ImageEnhance, ImageOps

def enhance_image(image_path, enhancement_strength=1.5):
    
    try:
        # Skip if already enhanced
        if "_enhanced" in image_path:
            print(f"⚠️ Skipping enhancement (already enhanced): {image_path}")
            return image_path
            
        if not os.path.exists(image_path):
            print(f"⚠️ Image not found: {image_path}")
            return None
            
        # Determine output path
        base_name, extension = os.path.splitext(image_path)
        enhanced_path = f"{base_name}_enhanced{extension}"
        
        # Check if enhanced version already exists
        if os.path.exists(enhanced_path):
            print(f"⚠️ Enhanced version already exists: {enhanced_path}")
            return enhanced_path
            
        # Read image with OpenCV for analysis
        cv_image = cv2.imread(image_path)
        if cv_image is None:
            print(f"⚠️ Failed to read image: {image_path}")
            return None
            
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        
        # Get image statistics
        brightness = np.mean(gray)
        contrast = np.std(gray)
        
        # Open with PIL for enhancements
        pil_image = Image.open(image_path)
        
        # Apply EXIF orientation correction
        pil_image = ImageOps.exif_transpose(pil_image)
        
        # Brightness adjustment (normalize to medium brightness range)
        target_brightness = 130  # Target middle brightness
        brightness_factor = min(max(target_brightness / (brightness + 1e-5), 0.7), 1.8)
        
        # Contrast adjustment
        target_contrast = 65  # Target standard deviation
        contrast_factor = min(max(target_contrast / (contrast + 1e-5), 0.8), 1.7)
        
        # Apply PIL enhancements
        # Brightness
        enhancer = ImageEnhance.Brightness(pil_image)
        pil_image = enhancer.enhance(brightness_factor)
        
        # Contrast
        enhancer = ImageEnhance.Contrast(pil_image)
        pil_image = enhancer.enhance(contrast_factor)
        
        # Sharpness
        enhancer = ImageEnhance.Sharpness(pil_image)
        pil_image = enhancer.enhance(enhancement_strength)
        
        # Color balance adjustment
        enhancer = ImageEnhance.Color(pil_image)
        pil_image = enhancer.enhance(1.2)
        
        # Save enhanced image
        pil_image.save(enhanced_path)
        
        
        print(f"✅ Enhanced image saved to {enhanced_path}")
        return enhanced_path
        
    except Exception as e:
        print(f"❌ Error enhancing image: {e}")
        return None

def apply_global_stylesheet(app, qss_file="MaterialDark.qss"):
    """Apply the QSS stylesheet globally to all windows."""
    try:
        if os.path.exists(qss_file):
            with open(qss_file, "r") as file:
                app.setStyleSheet(file.read())
            print(f"🎨 Applied global stylesheet: {qss_file}")
        else:
            print(f"⚠️ Stylesheet not found: {qss_file}")
    except Exception as e:
        print(f"❌ Error applying stylesheet: {e}")
