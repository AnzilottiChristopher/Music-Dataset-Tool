import tkinter as tk
import librosa
import numpy as np
import time

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

        # playhead stuff
        self.playhead_id = None
        self._start_time = None
        self._running = False
        self._frame_delay = 10  # 30fps
        
    def load_audio(self, path):
        y, sr = librosa.load(path, sr=None, mono=True)
        self._y, self._sr = y, sr
        self.duration = len(y) / sr
        self.draw_waveform()
        # Reset playhead to start position
        self.stop_playhead()
        
    def draw_waveform(self):
        # Don't delete the playhead!
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
                
    def set_peak_color(self, color: str):
        self._peak_color = color
        if self._y is not None:
            self.draw_waveform()

    def clear(self):
        self.delete("all")
        self._y = None
        self._sr = None
        
    def start_playhead(self):
        """Start playhead synced to actual pygame playback."""
        if self.duration <= 0:
            return

        import pygame
        self._running = True

        # Create playhead if missing
        if self.playhead_id is None:
            self.playhead_id = self.create_line(
                0, 0, 0, self._height, fill="red", width=2, tags="playhead"
            )
        
        # Make sure it's visible and at the start
        self.coords(self.playhead_id, 0, 0, 0, self._height)
        self.tag_raise("playhead")  # Bring to front

        self._update_playhead_sync()
        
    def _update_playhead_sync(self):
        """Update playhead using pygame's reported position."""
        
        import pygame
        if not self._running:
            return

        if not pygame.mixer.get_init():
            return

        # Check if music is still playing
        if not pygame.mixer.music.get_busy():
            self._running = False
            return

        # pygame.mixer.music.get_pos() returns elapsed time in milliseconds
        pos_ms = pygame.mixer.music.get_pos()
        
        # get_pos() can return -1 briefly at the start, so skip this frame
        if pos_ms < 0:
            self.after(self._frame_delay, self._update_playhead_sync)
            return

        elapsed = pos_ms / 1000.0
        frac = min(1.0, elapsed / self.duration)
        x = int(frac * self._width)

        self.coords(self.playhead_id, x, 0, x, self._height)
        self.after(self._frame_delay, self._update_playhead_sync)

    def stop_playhead(self):
        """Stop playhead animation and reset to start."""
        self._running = False
        if self.playhead_id is not None:
            self.coords(self.playhead_id, 0, 0, 0, self._height)
