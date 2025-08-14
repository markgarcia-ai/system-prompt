import os
import uuid
from typing import Optional, Tuple
from PIL import Image
import io
import base64
from pathlib import Path

class ImageStorage:
    """Handles image storage with multiple backend options"""
    
    def __init__(self, storage_type: str = "local"):
        self.storage_type = storage_type
        self.upload_dir = "app/static/uploads"
        self.max_size = (1920, 1080)  # Max dimensions
        self.quality = 85  # JPEG quality
        
        # Ensure upload directory exists
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(f"{self.upload_dir}/prompts", exist_ok=True)
        os.makedirs(f"{self.upload_dir}/avatars", exist_ok=True)
        os.makedirs(f"{self.upload_dir}/outputs", exist_ok=True)
    
    def save_image(self, image_data: bytes, category: str, filename: Optional[str] = None) -> str:
        """Save image with optimization"""
        
        # Generate filename if not provided
        if not filename:
            ext = self._get_image_extension(image_data)
            filename = f"{uuid.uuid4()}.{ext}"
        
        # Optimize image
        optimized_data = self._optimize_image(image_data)
        
        # Save based on storage type
        if self.storage_type == "local":
            return self._save_local(optimized_data, category, filename)
        elif self.storage_type == "base64":
            return self._save_base64(optimized_data)
        else:
            raise ValueError(f"Unsupported storage type: {self.storage_type}")
    
    def _optimize_image(self, image_data: bytes) -> bytes:
        """Optimize image for web"""
        try:
            # Open image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            # Resize if too large
            if image.size[0] > self.max_size[0] or image.size[1] > self.max_size[1]:
                image.thumbnail(self.max_size, Image.Resampling.LANCZOS)
            
            # Save optimized image
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=self.quality, optimize=True)
            return output.getvalue()
        
        except Exception as e:
            print(f"Error optimizing image: {e}")
            return image_data  # Return original if optimization fails
    
    def _save_local(self, image_data: bytes, category: str, filename: str) -> str:
        """Save image to local filesystem"""
        filepath = os.path.join(self.upload_dir, category, filename)
        
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        return f"/static/uploads/{category}/{filename}"
    
    def _save_base64(self, image_data: bytes) -> str:
        """Convert image to base64 data URL"""
        encoded = base64.b64encode(image_data).decode('utf-8')
        return f"data:image/jpeg;base64,{encoded}"
    
    def _get_image_extension(self, image_data: bytes) -> str:
        """Detect image format from data"""
        try:
            image = Image.open(io.BytesIO(image_data))
            return image.format.lower()
        except:
            return 'jpg'  # Default to jpg
    
    def delete_image(self, image_url: str) -> bool:
        """Delete image from storage"""
        try:
            if self.storage_type == "local" and image_url.startswith("/static/uploads/"):
                filepath = image_url.replace("/static/", "app/static/")
                if os.path.exists(filepath):
                    os.remove(filepath)
                    return True
            return False
        except Exception as e:
            print(f"Error deleting image: {e}")
            return False

# Cloudinary integration (alternative to local storage)
class CloudinaryStorage:
    """Cloudinary image storage integration"""
    
    def __init__(self):
        try:
            import cloudinary
            import cloudinary.uploader
            import cloudinary.api
            
            cloudinary.config(
                cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
                api_key=os.getenv("CLOUDINARY_API_KEY"),
                api_secret=os.getenv("CLOUDINARY_API_SECRET")
            )
            self.cloudinary = cloudinary
        except ImportError:
            raise ImportError("cloudinary package not installed. Run: pip install cloudinary")
    
    def save_image(self, image_data: bytes, category: str, filename: Optional[str] = None) -> str:
        """Upload image to Cloudinary"""
        try:
            # Upload to Cloudinary
            result = self.cloudinary.uploader.upload(
                io.BytesIO(image_data),
                folder=f"prompt-market/{category}",
                public_id=filename or str(uuid.uuid4()),
                transformation=[
                    {'width': 1920, 'height': 1080, 'crop': 'limit'},
                    {'quality': 'auto:good'}
                ]
            )
            return result['secure_url']
        except Exception as e:
            print(f"Error uploading to Cloudinary: {e}")
            raise
    
    def delete_image(self, image_url: str) -> bool:
        """Delete image from Cloudinary"""
        try:
            # Extract public_id from URL
            public_id = image_url.split('/')[-1].split('.')[0]
            result = self.cloudinary.uploader.destroy(public_id)
            return result.get('result') == 'ok'
        except Exception as e:
            print(f"Error deleting from Cloudinary: {e}")
            return False

# AWS S3 integration
class S3Storage:
    """AWS S3 image storage integration"""
    
    def __init__(self):
        try:
            import boto3
            self.s3 = boto3.client(
                's3',
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("AWS_REGION", "us-east-1")
            )
            self.bucket_name = os.getenv("AWS_S3_BUCKET")
        except ImportError:
            raise ImportError("boto3 package not installed. Run: pip install boto3")
    
    def save_image(self, image_data: bytes, category: str, filename: Optional[str] = None) -> str:
        """Upload image to S3"""
        try:
            if not filename:
                filename = f"{uuid.uuid4()}.jpg"
            
            key = f"images/{category}/{filename}"
            
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=image_data,
                ContentType='image/jpeg',
                ACL='public-read'
            )
            
            return f"https://{self.bucket_name}.s3.amazonaws.com/{key}"
        except Exception as e:
            print(f"Error uploading to S3: {e}")
            raise
    
    def delete_image(self, image_url: str) -> bool:
        """Delete image from S3"""
        try:
            # Extract key from URL
            key = image_url.split(f"{self.bucket_name}.s3.amazonaws.com/")[1]
            self.s3.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except Exception as e:
            print(f"Error deleting from S3: {e}")
            return False

# Factory function to get storage instance
def get_image_storage(storage_type: str = None) -> ImageStorage:
    """Get image storage instance based on configuration"""
    
    if not storage_type:
        storage_type = os.getenv("IMAGE_STORAGE_TYPE", "local")
    
    if storage_type == "local":
        return ImageStorage("local")
    elif storage_type == "cloudinary":
        return CloudinaryStorage()
    elif storage_type == "s3":
        return S3Storage()
    elif storage_type == "base64":
        return ImageStorage("base64")
    else:
        raise ValueError(f"Unsupported storage type: {storage_type}")

# Usage examples:
"""
# Local storage (default)
storage = get_image_storage("local")
image_url = storage.save_image(image_data, "prompts", "my_prompt.jpg")

# Cloudinary storage
storage = get_image_storage("cloudinary")
image_url = storage.save_image(image_data, "prompts")

# S3 storage
storage = get_image_storage("s3")
image_url = storage.save_image(image_data, "prompts")

# Base64 storage (for small images)
storage = get_image_storage("base64")
data_url = storage.save_image(image_data, "prompts")
""" 