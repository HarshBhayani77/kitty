from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, QEasingCurve
from PyQt6.QtGui import QColor, QScreen

class NotificationWidget(QWidget):
    """A premium, animated, frameless notification toast that pops up near the system tray."""

    def __init__(self, message: str, duration_ms: int = 3000, parent=None):
        super().__init__(parent)
        
        # Window attributes for frameless, always-on-top, non-stealing overlay
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # Premium dark glassmorphism styling
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(26, 26, 46, 220);
                border: 1px solid rgba(231, 76, 60, 100);
                border-radius: 8px;
            }
            QLabel {
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                background: transparent;
                border: none;
            }
        """)

        # Layout
        layout = QVBoxLayout()
        self.label = QLabel(message)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Set size and fit contents
        self.setFixedSize(260, 60)

        # Opacity effect for fade transitions
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)

        # Position widget in the bottom-right corner of the primary screen
        self.position_notification()

        # Animation configs
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_animation.setDuration(400)

        # Timers to control show -> wait -> fade out -> close
        self.close_timer = QTimer(self)
        self.close_timer.setSingleShot(True)
        self.close_timer.timeout.connect(self.fade_out)

    def position_notification(self) -> None:
        """Position toast in bottom-right corner above system taskbar."""
        primary_screen = QScreen.availableGeometry(self.screen())
        screen_geom = primary_screen
        
        x = screen_geom.right() - self.width() - 20
        y = screen_geom.bottom() - self.height() - 20
        self.move(QPoint(x, y))

    def show_notification(self, duration_ms: int = 3000) -> None:
        """Fades in the notification widget and sets exit timer."""
        self.show()
        self.fade_animation.stop()
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()
        
        self.close_timer.start(duration_ms)

    def fade_out(self) -> None:
        """Fades out and closes the widget once the fade concludes."""
        self.fade_animation.stop()
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(self.close)
        self.fade_animation.start()
