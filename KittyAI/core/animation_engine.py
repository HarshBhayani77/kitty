import os
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap

class AnimationEngine(QObject):
    """Manages pet animation states, transitions, and frame updates."""
    
    frame_changed = pyqtSignal(int)  # Emits current frame index on change
    state_changed = pyqtSignal(str)  # Emits new state name on transition

    def __init__(self, sprite_dir: str = "assets/sprites", fps: int = 10, parent=None):
        super().__init__(parent)
        self.sprite_dir = sprite_dir
        self.fps = fps
        self.current_state = "idle"
        self.current_frame = 0
        self.states = {
            "idle": 4,      # Number of frames in idle animation
            "walk": 4,      # Number of frames in walk animation
            "sleep": 2,     # Number of frames in sleep animation
            "jump": 6,      # Number of frames in jump animation
            "drag": 1,      # Frame when the pet is dragged
            "knead": 4      # Keyboard kneading animation
        }
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._next_frame)
        self.timer.start(int(1000 / self.fps))

    def set_state(self, state: str) -> None:
        """Change the current animation state and reset frames."""
        if state in self.states and state != self.current_state:
            self.current_state = state
            self.current_frame = 0
            self.state_changed.emit(state)
            self.frame_changed.emit(self.current_frame)

    def get_current_frame_count(self) -> int:
        """Returns total frames for current state."""
        return self.states.get(self.current_state, 1)

    def _next_frame(self) -> None:
        """Advances the animation to the next frame."""
        frame_count = self.get_current_frame_count()
        if frame_count > 1:
            self.current_frame = (self.current_frame + 1) % frame_count
            self.frame_changed.emit(self.current_frame)

    def load_frame_pixmap(self, skin: str) -> QPixmap:
        """
        Attempts to load a specific sprite file from disk.
        Returns a blank or placeholder QPixmap if not found, allowing 
        vector rendering to take over.
        """
        filename = f"{skin}_{self.current_state}_{self.current_frame}.png"
        path = os.path.join(self.sprite_dir, filename)
        
        if os.path.exists(path):
            return QPixmap(path)
        
        # Return empty QPixmap if no sprite file exists
        return QPixmap()
