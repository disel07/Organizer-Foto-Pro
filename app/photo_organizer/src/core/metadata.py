import os
import re
import datetime
import mimetypes
import hashlib
from typing import Tuple, Optional
from PIL import Image
from PIL.ExifTags import TAGS
import exifread
import hachoir.parser
import hachoir.metadata

class MetadataExtractor:
    
    # Regex patterns for filename date extraction
    DATE_PATTERNS = [
        r'(?P<year>20\d{2})[-_]?(?P<month>\d{2})[-_]?(?P<day>\d{2})', # YYYY-MM-DD or YYYYMMDD
        r'(?P<day>\d{2})[-_]?(?P<month>\d{2})[-_]?(?P<year>20\d{2})', # DD-MM-YYYY
        r'IMG[-_](?P<year>20\d{2})(?P<month>\d{2})(?P<day>\d{2})',     # IMG_YYYYMMDD
        r'VID[-_](?P<year>20\d{2})(?P<month>\d{2})(?P<day>\d{2})',     # VID_YYYYMMDD
        r'WP[-_](?P<year>20\d{2})(?P<month>\d{2})(?P<day>\d{2})',      # WP_YYYYMMDD (WhatsApp)
        r'Screenshot[-_](?P<year>20\d{2})(?P<month>\d{2})(?P<day>\d{2})' # Screenshot_YYYYMMDD
    ]

    @staticmethod
    def calculate_hash(file_path: str, algorithm: str = 'md5', chunk_size: int = 8192) -> str:
        """Calculates file hash efficiently."""
        hasher = hashlib.new(algorithm)
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except OSError:
            return ""

    @staticmethod
    def get_mime_type(file_path: str) -> str:
        mime, _ = mimetypes.guess_type(file_path)
        return mime or "application/octet-stream"

    @classmethod
    def get_date(cls, file_path: str) -> Tuple[datetime.datetime, str]:
        """
        Returns (best_guess_date, source_of_date)
        Priority: EXIF > Metadata (Video) > Filename > OS Stat
        """
        mime = cls.get_mime_type(file_path)
        
        # 1. Try EXIF for Images
        if mime.startswith('image'):
            date = cls._get_exif_date(file_path)
            if date:
                return date, "EXIF"

        # 2. Try Hachoir for Videos
        if mime.startswith('video'):
            date = cls._get_video_date(file_path)
            if date:
                return date, "VideoMetadata"

        # 3. Try Filename Regex
        date = cls._get_date_from_filename(os.path.basename(file_path))
        if date:
            return date, "Filename"

        # 4. Fallback to OS File Stats
        try:
            stat = os.stat(file_path)
            # Use the earliest of mtime or ctime
            timestamp = min(stat.st_mtime, stat.st_ctime)
            return datetime.datetime.fromtimestamp(timestamp), "FileSystem"
        except OSError:
            # If all fails, return Now? No, better to return None or a very old date? 
            # We return now but log it as 'Unknown' essentially
            return datetime.datetime.now(), "Unknown"

    @staticmethod
    def _get_exif_date(file_path: str) -> Optional[datetime.datetime]:
        try:
            # Try with ExifRead first (often faster/more robust for just tags)
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f, details=False, stop_tag='DateTimeOriginal')
                
            date_str = None
            if 'EXIF DateTimeOriginal' in tags:
                date_str = str(tags['EXIF DateTimeOriginal'])
            elif 'Image DateTime' in tags:
                date_str = str(tags['Image DateTime'])
                
            if date_str:
                try:
                    return datetime.datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                except ValueError:
                    pass
        except Exception:
            pass
            
        # Fallback to Pillow
        try:
            img = Image.open(file_path)
            exif_data = img._getexif()
            if exif_data:
                # 36867 is DateTimeOriginal
                date_str = exif_data.get(36867)
                if date_str:
                    return datetime.datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
        except Exception:
            pass
            
        return None

    @staticmethod
    def _get_video_date(file_path: str) -> Optional[datetime.datetime]:
        try:
            parser = hachoir.parser.createParser(file_path)
            if not parser:
                return None
            
            with parser:
                metadata = hachoir.metadata.extractMetadata(parser)
            
            if metadata and metadata.has('creation_date'):
                return metadata.get('creation_date')
        except Exception:
            pass
        return None

    @classmethod
    def _get_date_from_filename(cls, filename: str) -> Optional[datetime.datetime]:
        for pattern in cls.DATE_PATTERNS:
            match = re.search(pattern, filename)
            if match:
                try:
                    parts = match.groupdict()
                    return datetime.datetime(
                        year=int(parts['year']),
                        month=int(parts['month']),
                        day=int(parts['day'])
                    )
                except (ValueError, KeyError):
                    continue
        return None
