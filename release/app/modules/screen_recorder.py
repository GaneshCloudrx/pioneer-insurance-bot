"""
Screen Recorder - records the entire bot session continuously
"""
import time
import threading
import os
from datetime import datetime
from mss import mss
import numpy as np
import cv2
from modules.helper import log_print


class ScreenRecorder:
    """
    Records screen continuously during bot operation.
    Starts when initialized, stops when stop_recording() is called.
    """
    
    def __init__(self, output_dir="recordings", fps=5, quality="medium", max_file_size_gb=2):
        """
        Initialize screen recorder.
        
        Args:
            output_dir: Directory to save recordings (default: "recordings")
            fps: Frames per second (default: 2 for smaller files)
            quality: Video quality - "low", "medium", "high" (default: "medium")
            max_file_size_gb: Max file size in GB before creating new file (default: 5)
        """
        self.output_dir = output_dir
        self.fps = fps
        self.quality = quality
        self.max_file_size_bytes = max_file_size_gb * 1024 * 1024 * 1024  # Convert GB to bytes
        self.recording = False
        self.thread = None
        self.lock = threading.Lock()
        self.video_writer = None  # VideoWriter instance (created in recording thread)
        self.frame_count = 0  # Track number of frames captured
        self.initial_width = None  # Store initial resolution for consistency
        self.initial_height = None
        self.file_counter = 1  # Track file number for sequential naming
        self.base_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # Base timestamp
        # Don't create mss() here - create it in the recording thread
        
        # Quality settings for video encoding
        quality_settings = {
            "low": {"fourcc": cv2.VideoWriter_fourcc(*'mp4v'), "bitrate": 1000},
            "medium": {"fourcc": cv2.VideoWriter_fourcc(*'mp4v'), "bitrate": 2000},
            "high": {"fourcc": cv2.VideoWriter_fourcc(*'XVID'), "bitrate": 4000}
        }
        self.video_settings = quality_settings.get(quality, quality_settings["medium"])
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Generate initial filename
        self.filename = self._generate_filename()
        
        log_print(f"Screen recorder initialized - will save to: {self.filename}")
        log_print(f"Auto-rotation enabled: New file every {max_file_size_gb}GB")
    
    def _generate_filename(self):
        """Generate filename with counter for rotation."""
        if self.file_counter == 1:
            # First file: no counter suffix
            filename = os.path.join(self.output_dir, f"Bot_Session_{self.base_timestamp}.mp4")
        else:
            # Subsequent files: add part number
            filename = os.path.join(self.output_dir, f"Bot_Session_{self.base_timestamp}_part{self.file_counter}.mp4")
        return filename
    
    def start_recording(self):
        """Start recording screen in background thread."""
        if self.recording:
            log_print("Recording already in progress")
            return False
        
        self.recording = True
        self.frame_count = 0
        
        # Start recording thread
        self.thread = threading.Thread(target=self._record_loop, daemon=True)
        self.thread.start()
        
        log_print(f"Screen recording started (FPS: {self.fps}, Quality: {self.quality})")
        return True
    
    def stop_recording(self):
        """Stop recording and save video file."""
        if not self.recording:
            log_print("No recording in progress")
            return None
        
        log_print("Stopping screen recording and saving video...")
        
        # Stop recording loop
        self.recording = False
        
        # Wait for thread to finish (with timeout)
        if self.thread:
            self.thread.join(timeout=10)
        
        # Close video writer (frames are already written to disk)
        try:
            with self.lock:
                if self.video_writer is not None:
                    self.video_writer.release()
                    self.video_writer = None
            
            # Check if file exists and has content
            if os.path.exists(self.filename) and os.path.getsize(self.filename) > 0:
                file_size_mb = os.path.getsize(self.filename) / (1024 * 1024)
                log_print(f"Screen recording saved: {self.filename} ({file_size_mb:.2f} MB, {self.frame_count} frames)")
                return self.filename
            else:
                log_print("No frames captured - video file is empty or doesn't exist")
                return None
        except Exception as e:
            error_msg = str(e) if e else "Unknown error"
            error_type = type(e).__name__
            log_print(f"Error closing video file: {error_type}: {error_msg}")
            import traceback
            log_print(f"Traceback: {traceback.format_exc()}")
            return None
    
    def _rotate_video_file(self):
        """Close current video file and start a new one."""
        try:
            # Close current video writer
            if self.video_writer is not None:
                self.video_writer.release()
                
                # Log completion of current file
                if os.path.exists(self.filename):
                    file_size_gb = os.path.getsize(self.filename) / (1024 * 1024 * 1024)
                    log_print(f"✓ Video file completed: {self.filename} ({file_size_gb:.2f} GB, {self.frame_count} frames)")
                
                self.video_writer = None
            
            # Increment counter and generate new filename
            self.file_counter += 1
            self.filename = self._generate_filename()
            log_print(f"Starting new video file: {self.filename}")
            
            # Create new video writer
            fourcc = self.video_settings["fourcc"]
            self.video_writer = cv2.VideoWriter(
                self.filename,
                fourcc,
                self.fps,
                (self.initial_width, self.initial_height)
            )
            
            if not self.video_writer.isOpened():
                raise Exception(f"Failed to open video writer for {self.filename}")
            
            # Reset frame count for new file
            self.frame_count = 0
            log_print(f"✓ New video file initialized successfully")
            return True
            
        except Exception as e:
            log_print(f"ERROR: Failed to rotate video file: {e}")
            import traceback
            log_print(f"Traceback: {traceback.format_exc()}")
            return False
    
    def _record_loop(self):
        """Main recording loop - captures screen frames and writes directly to disk."""
        # Create mss instance in this thread (required for thread-local storage)
        sct = mss()
        
        frame_interval = 1.0 / self.fps
        last_capture_time = time.time()
        
        # Get screen dimensions (primary monitor) - check dynamically each time
        monitor = sct.monitors[1]  # monitors[0] is all monitors, [1] is primary
        initial_width = monitor["width"]
        initial_height = monitor["height"]
        
        # Store initial resolution for consistency (will resize frames if resolution changes)
        with self.lock:
            self.initial_width = initial_width
            self.initial_height = initial_height
        
        log_print(f"Recording screen: {initial_width}x{initial_height} at {self.fps} FPS")
        log_print("Note: If resolution changes during recording, frames will be resized to maintain consistency")
        
        # Initialize video writer - write directly to disk
        try:
            fourcc = self.video_settings["fourcc"]
            with self.lock:
                self.video_writer = cv2.VideoWriter(
                    self.filename,
                    fourcc,
                    self.fps,
                    (initial_width, initial_height)
                )
                
                if not self.video_writer.isOpened():
                    raise Exception(f"Failed to open video writer for {self.filename}")
            
            log_print(f"Video writer initialized - writing frames directly to disk")
        except Exception as e:
            error_msg = str(e) if e else "Unknown error"
            error_type = type(e).__name__
            log_print(f"ERROR: Failed to initialize video writer: {error_type}: {error_msg}")
            import traceback
            log_print(f"Traceback: {traceback.format_exc()}")
            self.recording = False
            return
        
        # Main recording loop
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        while self.recording:
            try:
                current_time = time.time()
                
                # Capture frame if enough time has passed
                if current_time - last_capture_time >= frame_interval:
                    # Get current monitor dimensions (resolution may have changed)
                    current_monitor = sct.monitors[1]
                    current_width = current_monitor["width"]
                    current_height = current_monitor["height"]
                    
                    # Capture screen
                    screenshot = sct.grab(current_monitor)
                    
                    # Convert to numpy array and then to BGR for OpenCV
                    img = np.array(screenshot)
                    img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                    
                    # Handle resolution changes: resize frame to match initial resolution
                    with self.lock:
                        if self.initial_width is not None and self.initial_height is not None:
                            img_height, img_width = img.shape[:2]
                            
                            # Check if resolution changed
                            if img_width != self.initial_width or img_height != self.initial_height:
                                # Resize frame to match initial resolution
                                img = cv2.resize(img, (self.initial_width, self.initial_height), interpolation=cv2.INTER_LINEAR)
                                # Log resolution change (only once per change to avoid spam)
                                if self.frame_count == 0 or (self.frame_count % 100 == 0):
                                    log_print(f"Resolution changed: {img_width}x{img_height} -> {self.initial_width}x{self.initial_height} (resized)")
                        
                        # Write frame directly to disk (no memory accumulation!)
                        if self.video_writer is not None and self.video_writer.isOpened():
                            self.video_writer.write(img)
                            self.frame_count += 1
                            
                            if self.frame_count % 1000 == 0:
                                try:
                                    if os.path.exists(self.filename):
                                        current_size = os.path.getsize(self.filename)
                                        if current_size >= self.max_file_size_bytes:
                                            size_gb = current_size / (1024 * 1024 * 1024)
                                            log_print(f"File size limit reached ({size_gb:.2f} GB), rotating to new file...")
                                            if not self._rotate_video_file():
                                                log_print("ERROR: Failed to rotate file, stopping recording")
                                                self.recording = False
                                                break
                                except Exception as e:
                                    pass
                    
                    consecutive_errors = 0  # Reset error counter on success
                    last_capture_time = current_time
                else:
                    # Sleep a bit to avoid busy waiting
                    time.sleep(0.01)
                    
            except MemoryError as e:
                # Memory errors are critical - log and stop
                error_msg = str(e) if e else "Out of memory"
                log_print(f"CRITICAL: Memory error capturing frame: {error_msg}")
                log_print("Stopping recording due to memory issues...")
                self.recording = False
                break
            except Exception as e:
                # Log error but continue recording
                error_msg = str(e) if e else "Unknown error"
                error_type = type(e).__name__
                if not error_msg or error_msg.strip() == "":
                    error_msg = f"{error_type} occurred"
                
                log_print(f"Error capturing frame: {error_type}: {error_msg}")
                
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    log_print(f"Too many consecutive errors ({consecutive_errors}), stopping recording...")
                    self.recording = False
                    break
                
                time.sleep(0.1)
        
        # Clean up video writer
        try:
            with self.lock:
                if self.video_writer is not None:
                    self.video_writer.release()
                    self.video_writer = None
        except Exception as e:
            error_msg = str(e) if e else "Unknown error"
            log_print(f"Error releasing video writer: {error_msg}")
        
        log_print(f"Recording stopped - captured {self.frame_count} frames")
    
    
    def is_recording(self):
        """Check if currently recording."""
        return self.recording
    
    def get_filename(self):
        """Get the output filename."""
        return self.filename
