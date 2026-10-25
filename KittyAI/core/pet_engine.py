import random
from PyQt6.QtCore import QObject, QTimer, pyqtSignal, QPoint

class PetEngine(QObject):
    """Coordinates the physical coordinates, movement velocity, and state decisions of the pet."""

    position_changed = pyqtSignal(int, int)  # Emits new (x, y) coordinates
    state_requested = pyqtSignal(str)       # Requests an animation state change

    def __init__(self, fps: int = 20, parent=None):
        super().__init__(parent)
        self.x = 200
        self.y = 200
        self.target_x = 200
        self.target_y = 200
        self.speed = 3
        self.hunting = False
        self.screengrab_width = 1920
        self.screengrab_height = 1080
        
        # Physics update timer (20 fps)
        self.physics_timer = QTimer(self)
        self.physics_timer.timeout.connect(self._update_position)
        self.physics_timer.start(int(1000 / fps))

        # Behavior decision timer (every 4 seconds, pet decides what to do)
        self.behavior_timer = QTimer(self)
        self.behavior_timer.timeout.connect(self._make_behavior_decision)
        self.behavior_timer.start(4000)

    def set_screen_geometry(self, width: int, height: int) -> None:
        """Update monitor boundaries to keep pet on screen."""
        self.screengrab_width = width
        self.screengrab_height = height

    def set_position(self, x: int, y: int) -> None:
        """Forcefully update the pet's position."""
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y
        self.position_changed.emit(self.x, self.y)

    def hunt_target(self, target_pos: QPoint) -> None:
        """Play hunt behavior in-place (eye tracking is active, but pet does not change coordinates)."""
        self.target_x = self.x
        self.target_y = self.y
        self.hunting = True
        self.state_requested.emit("walk")

    def stop_hunting(self) -> None:
        """Stop chasing the cursor."""
        self.hunting = False
        self._make_behavior_decision()

    def _update_position(self) -> None:
        """Incremental frame movement towards the active target coordinate."""
        if self.x == self.target_x and self.y == self.target_y:
            if self.hunting:
                self.hunting = False
            return

        # Calculate distance to target
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = (dx**2 + dy**2) ** 0.5

        if distance < self.speed:
            self.x = self.target_x
            self.y = self.target_y
        else:
            self.x += int(self.speed * (dx / distance))
            self.y += int(self.speed * (dy / distance))

        # Clamp position inside screen boundaries
        self.x = max(0, min(self.screengrab_width - 48, self.x))
        self.y = max(0, min(self.screengrab_height - 48, self.y))

        self.position_changed.emit(self.x, self.y)

    def _make_behavior_decision(self) -> None:
        """Pet AI state machine keeping pet alert and responsive in-place."""
        if self.hunting:
            return
        self.target_x = self.x
        self.target_y = self.y
        self.state_requested.emit("idle")
