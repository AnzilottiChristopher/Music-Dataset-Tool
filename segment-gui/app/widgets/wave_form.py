import tkinter as tk
import librosa
import numpy as np

class WaveForm(tk.Canvas):
    def __init__(self, parent, width=700, height=100, bg="#ffffff", peak_color="#5ad", centerline="#333"):
        super().__init__(parent, width=width, height=height, bg=bg, highlightthickness=0)
        self._width = int(width)
        self._height = int(height)
        self._peak_color = peak_color
        self._centerline_color = centerline
        self._y = None
        self._sr = None
        self.duration = 0
        self.seek_callback = None

        # Playhead stuff
        self.playhead_id = None
        self._running = False
        self._paused = False
        self._current_position = 0  # Current position in seconds
        self._frame_delay = 20  # 50fps for smoother movement
        
        # Mouse interaction
        self._is_dragging = False
        self._hover_line_id = None
        
        # Bind mouse events for scrubbing
        self.bind("<Button-1>", self.on_mouse_click)
        self.bind("<B1-Motion>", self.on_mouse_drag)
        self.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.bind("<Motion>", self.on_mouse_hover)
        self.bind("<Leave>", self.on_mouse_leave)
        
    def set_seek_callback(self, callback):
        """Set the callback function to be called when seeking"""
        self.seek_callback = callback
        
    def load_audio(self, path):
        """Load audio file and draw waveform"""
        y, sr = librosa.load(path, sr=None, mono=True)
        self._y, self._sr = y, sr
        self.duration = len(y) / sr if sr > 0 else 0
        self.draw_waveform()
        # Reset playhead to start position
        self.stop_playhead()
        
    def draw_waveform(self):
        """Draw the audio waveform"""
        # Don't delete the playhead or hover line!
        self.delete("waveform")  # Only delete waveform elements
        if self._y is None or len(self._y) == 0:
            return

        w = self._width
        h = self._height
        mid = h // 2
        half_h = (h - 4) / 2

        n = len(self._y)
        if w <= n:
            win = n // w
            trimmed = self._y[:win * w]
            peaks = np.max(np.abs(trimmed.reshape(w, win)), axis=1)
        else:
            x_src = np.linspace(0, 1, n)
            x_dst = np.linspace(0, 1, w)
            peaks = np.interp(x_dst, x_src, np.abs(self._y))

        m = peaks.max()
        if m > 0:
            peaks = peaks / m

        # Tag all waveform elements so we can delete them separately
        self.create_line(0, mid, w, mid, fill=self._centerline_color, tags="waveform")

        for x in range(w):
            amp = peaks[x] * half_h
            y0 = mid - amp
            y1 = mid + amp
            self.create_line(x, y0, x, y1, fill=self._peak_color, tags="waveform")
    
    def on_mouse_click(self, event):
        """Handle mouse click for seeking"""
        if self.duration > 0:
            # Calculate position in seconds
            position_seconds = (event.x / self._width) * self.duration
            position_seconds = max(0, min(position_seconds, self.duration))
            
            self._is_dragging = True
            
            # Call the seek callback if set
            if self.seek_callback:
                self.seek_callback(position_seconds)
            else:
                # Just update playhead position if no callback
                self.set_playhead_position(position_seconds)
    
    def on_mouse_drag(self, event):
        """Handle mouse drag for scrubbing"""
        if self._is_dragging and self.duration > 0:
            # Calculate position in seconds
            x = max(0, min(event.x, self._width))
            position_seconds = (x / self._width) * self.duration
            
            # Call the seek callback if set
            if self.seek_callback:
                self.seek_callback(position_seconds)
            else:
                # Just update playhead position if no callback
                self.set_playhead_position(position_seconds)
    
    def on_mouse_release(self, event):
        """Handle mouse release"""
        self._is_dragging = False
    
    def on_mouse_hover(self, event):
        """Show a hover line when hovering over the waveform"""
        if self.duration > 0 and not self._is_dragging:
            # Remove old hover line
            if self._hover_line_id:
                self.delete(self._hover_line_id)
            
            # Create new hover line
            self._hover_line_id = self.create_line(
                event.x, 0, event.x, self._height,
                fill="#888", width=1, dash=(2, 2), tags="hover"
            )
            
            # Update cursor
            self.config(cursor="hand2")
    
    def on_mouse_leave(self, event):
        """Remove hover line when mouse leaves"""
        if self._hover_line_id:
            self.delete(self._hover_line_id)
            self._hover_line_id = None
        self.config(cursor="")
    
    def set_playhead_position(self, position_seconds):
        """Set playhead to a specific position"""
        if self.duration <= 0:
            return
        
        self._current_position = position_seconds
        frac = position_seconds / self.duration
        x = int(frac * self._width)
        
        # Create playhead if it doesn't exist
        if self.playhead_id is None:
            self.playhead_id = self.create_line(
                x, 0, x, self._height, fill="red", width=2, tags="playhead"
            )
        else:
            self.coords(self.playhead_id, x, 0, x, self._height)
        
        self.tag_raise("playhead")  # Bring to front
    
    def start_playhead(self):
        """Start playhead animation from current position"""
        self.start_playhead_at(self._current_position)
    
    def start_playhead_at(self, start_position):
        """Start playhead animation from a specific position"""
        if self.duration <= 0:
            return

        import pygame
        self._running = True
        self._paused = False
        self._current_position = start_position

        # Create playhead if missing
        if self.playhead_id is None:
            x = int((start_position / self.duration) * self._width)
            self.playhead_id = self.create_line(
                x, 0, x, self._height, fill="red", width=2, tags="playhead"
            )
        
        # Set initial position
        self.set_playhead_position(start_position)
        
        # Start the update loop
        self._start_time_ms = pygame.time.get_ticks()
        self._start_position = start_position
        self._update_playhead_sync()
    
    def pause_playhead(self):
        """Pause the playhead at current position"""
        self._paused = True
        self._running = False
        
    def _update_playhead_sync(self):
        """Update playhead using pygame's timer"""
        import pygame
        
        if not self._running or self._paused:
            return

        if not pygame.mixer.get_init():
            return

        # Check if music is still playing
        if not pygame.mixer.music.get_busy():
            self._running = False
            return

        # Calculate elapsed time since we started
        current_time_ms = pygame.time.get_ticks()
        elapsed_ms = current_time_ms - self._start_time_ms
        elapsed_seconds = elapsed_ms / 1000.0
        
        # Calculate current position
        current_position = self._start_position + elapsed_seconds
        
        # Ensure we don't exceed duration
        if current_position >= self.duration:
            current_position = self.duration
            self._running = False
        
        # Update position
        self._current_position = current_position
        frac = current_position / self.duration
        x = int(frac * self._width)

        if self.playhead_id:
            self.coords(self.playhead_id, x, 0, x, self._height)
        
        if self._running:
            self.after(self._frame_delay, self._update_playhead_sync)

    def stop_playhead(self):
        """Stop playhead animation and reset to start"""
        self._running = False
        self._paused = False
        self._current_position = 0
        if self.playhead_id is not None:
            self.coords(self.playhead_id, 0, 0, 0, self._height)
    
    def set_peak_color(self, color: str):
        """Change the color of the waveform"""
        self._peak_color = color
        if self._y is not None:
            self.draw_waveform()

    def clear(self):
        """Clear the waveform and reset"""
        self.delete("all")
        self._y = None
        self._sr = None
        self.duration = 0
        self._current_position = 0
        self.playhead_id = None
        self._hover_line_id = None
