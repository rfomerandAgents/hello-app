"""Cloudflare R2 uploader for ADW screenshots.

Uploads screenshots to Cloudflare R2 and returns public URLs via custom domain.

Setup:
1. Create R2 bucket in Cloudflare Dashboard
2. Connect a custom domain (e.g., screenshots.{{PROJECT_DOMAIN}}) for public access
3. Set environment variables:
   - CLOUDFLARE_ACCOUNT_ID: Your Cloudflare account ID
   - CLOUDFLARE_R2_ACCESS_KEY_ID: R2 API access key
   - CLOUDFLARE_R2_SECRET_ACCESS_KEY: R2 API secret key
   - CLOUDFLARE_R2_BUCKET_NAME: Bucket name (e.g., "screenshots")
   - CLOUDFLARE_R2_PUBLIC_DOMAIN: Custom domain (e.g., "screenshots.{{PROJECT_DOMAIN}}")
"""

import os
import logging
from typing import Optional, Dict, List
from pathlib import Path
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError


class R2Uploader:
    """Handle uploads to Cloudflare R2 bucket with public custom domain."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.client = None
        self.bucket_name = None
        self.public_domain = None
        self.enabled = False

        # Initialize if all required env vars exist
        self._initialize()

    def _initialize(self) -> None:
        """Initialize R2 client if all required environment variables are set."""
        account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        access_key_id = os.getenv("CLOUDFLARE_R2_ACCESS_KEY_ID")
        secret_access_key = os.getenv("CLOUDFLARE_R2_SECRET_ACCESS_KEY")
        self.bucket_name = os.getenv("CLOUDFLARE_R2_BUCKET_NAME")
        public_domain_raw = os.getenv("CLOUDFLARE_R2_PUBLIC_DOMAIN", "screenshots.{{PROJECT_DOMAIN}}")

        # Sanitize public_domain by removing any protocol prefix
        self.public_domain = public_domain_raw
        if self.public_domain.startswith("https://"):
            self.public_domain = self.public_domain[8:]
            self.logger.debug(f"Stripped 'https://' prefix from public domain: {public_domain_raw} -> {self.public_domain}")
        elif self.public_domain.startswith("http://"):
            self.public_domain = self.public_domain[7:]
            self.logger.debug(f"Stripped 'http://' prefix from public domain: {public_domain_raw} -> {self.public_domain}")

        # Check if all required vars are present
        if not all([account_id, access_key_id, secret_access_key, self.bucket_name]):
            self.logger.info("R2 upload disabled - missing required environment variables")
            return

        try:
            # Create R2 client
            self.client = boto3.client(
                's3',
                endpoint_url=f'https://{account_id}.r2.cloudflarestorage.com',
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                config=Config(signature_version='s3v4'),
                region_name='us-east-1'
            )
            self.enabled = True
            self.logger.info(f"R2 upload enabled - bucket: {self.bucket_name}, public domain: {self.public_domain}")
        except Exception as e:
            self.logger.warning(f"Failed to initialize R2 client: {e}")
            self.enabled = False

    def _get_public_url(self, object_key: str) -> str:
        """Generate public URL for an object using the custom domain.

        Args:
            object_key: The S3 object key (path within bucket)

        Returns:
            Public HTTPS URL via custom domain
        """
        return f"https://{self.public_domain}/{object_key}"

    def upload_file(self, file_path: str, object_key: Optional[str] = None) -> Optional[str]:
        """
        Upload a file to R2 and return a public URL via custom domain.

        Args:
            file_path: Path to the file to upload (absolute or relative)
            object_key: Optional S3 object key. If not provided, will use default pattern

        Returns:
            Public URL if upload successful, None if upload is disabled or fails
        """
        if not self.enabled:
            return None

        # Convert to absolute path if relative
        if not os.path.isabs(file_path):
            self.logger.info(f"Converting relative path to absolute: {file_path}")
            file_path = os.path.abspath(file_path)
            self.logger.info(f"Absolute path: {file_path}")

        if not os.path.exists(file_path):
            self.logger.warning(f"File not found at absolute path: {file_path}")
            return None

        # Generate object key if not provided
        if not object_key:
            # Use pattern: adw/{adw_id}/review/{filename}
            object_key = f"adw/review/{Path(file_path).name}"

        try:
            # Upload file with public-read ACL for custom domain access
            self.client.upload_file(
                file_path,
                self.bucket_name,
                object_key,
                ExtraArgs={'ContentType': self._get_content_type(file_path)}
            )
            self.logger.info(f"Uploaded {file_path} to R2 as {object_key}")

            # Return public URL via custom domain (no signature needed)
            public_url = self._get_public_url(object_key)
            self.logger.info(f"Public URL: {public_url}")
            return public_url

        except ClientError as e:
            self.logger.error(f"Failed to upload {file_path} to R2: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error uploading to R2: {e}")
            return None

    def _get_content_type(self, file_path: str) -> str:
        """Get content type based on file extension."""
        ext = Path(file_path).suffix.lower()
        content_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.svg': 'image/svg+xml',
        }
        return content_types.get(ext, 'application/octet-stream')

    def _parse_base64_data_uri(self, data: str) -> tuple[bool, Optional[str], Optional[str]]:
        """Parse a base64 data URI into components.

        Args:
            data: String that might be a base64 data URI

        Returns:
            Tuple of (is_base64, mime_type, base64_data)
            Returns (False, None, None) if not a valid base64 data URI
        """
        if not data or not data.startswith("data:image/"):
            return (False, None, None)

        try:
            # Format: data:image/png;base64,iVBOR...
            header, base64_content = data.split(",", 1)
            mime_type = header.split(";")[0].replace("data:", "")
            return (True, mime_type, base64_content)
        except (ValueError, IndexError):
            return (False, None, None)
    
    def upload_base64(self, base64_data: str, object_key: str, mime_type: str = "image/png") -> Optional[str]:
        """Upload base64-encoded image data directly to R2.

        Args:
            base64_data: Base64-encoded image data (without data URI prefix)
            object_key: S3 object key for the upload
            mime_type: MIME type of the image (default: image/png)

        Returns:
            Public URL if upload successful, None if upload is disabled or fails
        """
        if not self.enabled:
            return None

        try:
            import base64 as b64
            image_bytes = b64.b64decode(base64_data)

            self.client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=image_bytes,
                ContentType=mime_type
            )
            self.logger.info(f"Uploaded base64 image to R2 as {object_key}")

            public_url = self._get_public_url(object_key)
            self.logger.info(f"Public URL: {public_url}")
            return public_url

        except Exception as e:
            self.logger.error(f"Failed to upload base64 image to R2: {e}")
            return None

    def upload_screenshots(self, screenshots: List[str], adw_id: str) -> Dict[str, str]:
        """
        Upload multiple screenshots and return mapping of local paths to public URLs.

        Args:
            screenshots: List of local screenshot file paths
            adw_id: ADW workflow ID for organizing uploads

        Returns:
            Dict mapping local paths to public URLs (or original paths if upload disabled/failed)
        """
        url_mapping = {}

        for screenshot_path in screenshots:
            if not screenshot_path:
                continue

            # Generate object key with ADW ID for organization
            filename = Path(screenshot_path).name
            object_key = f"adw/{adw_id}/review/{filename}"

            # Upload and get public URL
            public_url = self.upload_file(screenshot_path, object_key)

            # Map to public URL if successful, otherwise keep original path
            url_mapping[screenshot_path] = public_url or screenshot_path

        return url_mapping