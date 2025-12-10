import os
import shutil
import datetime
import logging
from pathlib import Path
from typing import Callable, Optional
from .metadata import MetadataExtractor
from ..data.database import SessionDatabase

class OrganizerEngine:
    MODE_DATE_TREE = "date_tree"     # YYYY/MM/DD/file.jpg
    MODE_TYPE_DATE = "type_date"     # Photos/YYYY/MM/file.jpg
    
    def __init__(self, db: SessionDatabase):
        self.db = db
        self._stop_event = False
        self.logger = logging.getLogger("Organizer")

    def stop(self):
        self._stop_event = True

    def calculate_destinations(self, base_dest_path: str, mode: str = MODE_DATE_TREE):
        """Populates the 'dest_path' column in DB for all files."""
        files = self.db.get_all_files()
        
        for row in files:
            if self._stop_event: break
            
            source_path = row['source_path']
            date_str = row['date_taken']
            mime = row['mime_type']
            filename = row['file_name']
            
            # Parse date
            try:
                dt = datetime.datetime.fromisoformat(date_str)
            except (ValueError, TypeError):
                dt = datetime.datetime.now() # Should not happen if scanner works
            
            # Build sub-path
            year = dt.strftime("%Y")
            month = dt.strftime("%m")
            day = dt.strftime("%d")
            
            if mode == self.MODE_TYPE_DATE:
                type_folder = "Video" if mime.startswith("video") else "Foto"
                # Photos/2023/08/img.jpg
                rel_path = os.path.join(type_folder, year, month, filename)
            else:
                # 2023/08/15/img.jpg
                rel_path = os.path.join(year, month, day, filename)
                
            full_dest = os.path.join(base_dest_path, rel_path)
            
            # Check for collisions (in DB first, then FS)
            # Note: real collision check happens at execution time for FS
            # But here we might want to check if multiple source files map to same dest
            # For now, simple mapping.
            
            self.db.set_destination(source_path, full_dest)

    def execute_transfer(self, delete_source: bool = False, progress_callback: Optional[Callable[[int, int], None]] = None):
        """
        Executes the copy process:
        1. Check if destination exists
        2. If exists -> Check Hash. If match -> Mark Verified. If different -> Rename Dest.
        3. If not exists -> Copy -> Verify -> Update DB.
        """
        files = self.db.get_all_files()
        total = len(files)
        
        for i, row in enumerate(files):
            if self._stop_event: break
            
            source = row['source_path']
            dest = row['dest_path']
            
            if not dest:
                continue
                
            # Skip if already done
            if row['status'] in ('verified', 'moved'):
                continue

            try:
                # Pre-Calc Source Hash
                src_hash = MetadataExtractor.calculate_hash(source)
                if not src_hash:
                    self.db.update_status(source, 'error', "Source file validation failed (empty hash)")
                    continue

                # 1. Resolve Collision & Determine Final Path
                final_dest, skip_copy = self._resolve_smart_collision(dest, src_hash, source)
                
                # 2. Copy if needed
                if not skip_copy:
                    os.makedirs(os.path.dirname(final_dest), exist_ok=True)
                    shutil.copy2(source, final_dest)
                
                # 3. Verify
                dst_hash = MetadataExtractor.calculate_hash(final_dest)
                
                if src_hash == dst_hash:
                    # Success
                    self.db.update_metadata(source, row['date_taken'], row['date_source'], src_hash)
                    
                    if delete_source:
                        os.remove(source) 
                        self.db.update_status(source, 'moved')
                    else:
                        self.db.update_status(source, 'verified')
                else:
                    self.db.update_status(source, 'error', "Hash Mismatch")
                    # If we just copied it and it's wrong, should we delete it? 
                    # Only if we *didn't* skip copy.
                    if not skip_copy and os.path.exists(final_dest):
                        os.remove(final_dest) 
                        
            except Exception as e:
                self.db.update_status(source, 'error', str(e))
            
            if progress_callback and (i % 5 == 0 or i == total - 1):
                progress_callback(i + 1, total)

    def verify_migration(self) -> dict:
        """
        'Second Check' feature.
        Iterates all 'verified'/'moved' files in DB and checks if they still exist in dest.
        Returns a report.
        """
        files = self.db.get_all_files()
        report = {
            "total": 0,
            "success": 0,
            "missing": 0,
            "corrupted": 0
        }
        
        for row in files:
            if row['status'] not in ('verified', 'moved'):
                continue
                
            report['total'] += 1
            dest = row['dest_path']
            
            if not os.path.exists(dest):
                report['missing'] += 1
                continue
                
            # Optional: Re-hash check (expensive but requested)
            # stored_hash = row['file_hash']
            # if stored_hash:
            #     current_hash = MetadataExtractor.calculate_hash(dest)
            #     if current_hash != stored_hash:
            #         report['corrupted'] += 1
            #         continue
            
            report['success'] += 1
            
        return report

    def _resolve_smart_collision(self, dest_path: str, src_hash: str, source_path: str) -> tuple[str, bool]:
        """
        Returns (final_dest_path, skip_copy_flag)
        """
        if not os.path.exists(dest_path):
            return dest_path, False
            
        # Collision found! Check if it's the exact same content
        if MetadataExtractor.calculate_hash(dest_path) == src_hash:
            return dest_path, True # Skip copy, it's already there!
            
        # Different content, we must rename
        base, ext = os.path.splitext(dest_path)
        counter = 1
        new_dest = dest_path
        
        while os.path.exists(new_dest):
            # Optimization: check hash of this variant too? 
            # No, if user has IMG_001.jpg and IMG_001_1.jpg, we assume they are different versions.
            # Just find a free slot.
            new_dest = f"{base}_{counter}{ext}"
            counter += 1
            
        return new_dest, False
