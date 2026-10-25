from PyQt6.QtCore import QObject, QTimer, pyqtSignal

class PomodoroTimer(QObject):
    """Encapsulates the standard Pomodoro focus and rest intervals."""
    
    tick = pyqtSignal(int, int, str)  # Emits (minutes, seconds, current_mode)
    session_completed = pyqtSignal(str)  # Emits completed session type ("work" or "break")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_tick)
        
        self.work_duration = 25 * 60  # Default 25 minutes
        self.break_duration = 5 * 60  # Default 5 minutes
        
        self.time_remaining = 0
        self.current_mode = "idle"  # idle, work, break
        self.sessions_completed = 0

    def start_work(self) -> None:
        """Start a Pomodoro focus session."""
        self.current_mode = "work"
        self.time_remaining = self.work_duration
        self.timer.start(1000)
        self._notify_tick()

    def start_break(self) -> None:
        """Start a break session."""
        self.current_mode = "break"
        self.time_remaining = self.break_duration
        self.timer.start(1000)
        self._notify_tick()

    def stop(self) -> None:
        """Cancel and reset the active timer."""
        self.timer.stop()
        self.current_mode = "idle"
        self.time_remaining = 0
        self.tick.emit(0, 0, "idle")

    def pause(self) -> None:
        """Pause the running countdown."""
        self.timer.stop()

    def resume(self) -> None:
        """Resume a paused countdown."""
        if self.current_mode != "idle" and self.time_remaining > 0:
            self.timer.start(1000)

    def _on_tick(self) -> None:
        """Decrements countdown and handles transition when time runs out."""
        if self.time_remaining > 0:
            self.time_remaining -= 1
            self._notify_tick()
        else:
            self.timer.stop()
            completed_type = self.current_mode
            if completed_type == "work":
                self.sessions_completed += 1
            self.session_completed.emit(completed_type)
            self.current_mode = "idle"

    def _notify_tick(self) -> None:
        """Calculates minutes/seconds and emits tick signal."""
        minutes = self.time_remaining // 60
        seconds = self.time_remaining % 60
        self.tick.emit(minutes, seconds, self.current_mode)
