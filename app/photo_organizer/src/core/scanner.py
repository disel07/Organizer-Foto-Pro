import os
import concurrent.futures
from pathlib import Path
from typing import List, Callable, Optional
from .metadata import MetadataExtractor
from ..data.database import SessionDatabase

class Scanner:
    SKIP_DIRS = {'.git', '.svn', '$RECYCLE.BIN', 'System Volume Information', '__pycache__'}
    SKIP_FILES = {'.DS_Store', 'Thumbs.db', 'desktop.ini'}
    MEDIA_EXTENSIONS = {
        # Images
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.heic', '.raw', '.cr2', '.nef', '.arw',
        # Videos
        '.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp'
    }

    def __init__(self, db: SessionDatabase):
        self.db = db
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count() or 4)
        self.is_running = False
        self._stop_event = False
        self.total_files_found = 0

    def scan_path(self, root_path: str, progress_callback: Optional[Callable[[str], None]] = None):
        """
        Recursively scans the path. Submits metadata extraction tasks to thread pool.
        """
        self.is_running = True
        self._stop_event = False
        self.total_files_found = 0
        
        root = Path(root_path)
        if not root.exists():
            return

        futures = []

        try:
            for entry in self._safe_walk(root):
                if self._stop_event:
                    break
                
                if entry.is_file():
                    ext = os.path.splitext(entry.name)[1].lower()
                    if ext in self.MEDIA_EXTENSIONS and entry.name not in self.SKIP_FILES:
                        self.total_files_found += 1
                        # Submit job to worker pool
                        future = self.executor.submit(self._process_file, entry.path, entry.name, entry.stat().st_size)
                        futures.append(future)
                        

                        if progress_callback and self.total_files_found % 50 == 0:
                            progress_callback(f"Trovati {self.total_files_found} file... ({entry.name})")

            # Wait for all tasks to complete
            concurrent.futures.wait(futures)
            
        except Exception as e:
            print(f"Scan error: {e}")
        finally:
            self.is_running = False

    def stop(self):
        self._stop_event = True
        self.executor.shutdown(wait=False)

    def _safe_walk(self, path: Path):
        """Generator that yields DirEntry objects, skipping system folders."""
        try:
            # os.scandir is faster than os.walk
            with os.scandir(path) as it:
                for entry in it:
                    if entry.name in self.SKIP_FILES or entry.name in self.SKIP_DIRS:
                        continue
                    
                    if entry.is_dir(follow_symlinks=False):
                        yield from self._safe_walk(Path(entry.path))
                    else:
                        yield entry
        except PermissionError:
            pass # Skip unreadable folders
        except OSError:
            pass

    def _process_file(self, file_path: str, name: str, size: int):
        """Worker function: Extract metadata and save to DB."""
        if self._stop_event:
            return

        # 1. Insert into DB (Pending)
        mime = MetadataExtractor.get_mime_type(file_path)
        self.db.add_file(file_path, name, size, mime)
        
        # 2. Extract Date
        date_taken, date_source = MetadataExtractor.get_date(file_path)
        
        # 3. Update DB
        self.db.update_metadata(
            source_path=file_path,
            date_taken=date_taken.isoformat(),
            date_source=date_source
        )
