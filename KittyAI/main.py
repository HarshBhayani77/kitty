import os
import sys
import time
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QPoint, QTimer

# Import modular components
from database.database import DatabaseManager
from core.pet_engine import PetEngine
from core.animation_engine import AnimationEngine
from core.ai_manager import AIManager
from core.system_monitor import SystemMonitor
from core.sound_manager import SoundManager
from features.personalization import PersonalizationManager
from features.pomodoro import PomodoroTimer
from features.reminders import ReminderManager
from features.sticky_notes import StickyNoteManager
from ui.pet_window import PetWindow
from ui.notification_widget import NotificationWidget

def main():
    # Initialize the Qt Application
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running even if window settings close

    # 1. Database Setup
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "kitty_ai.db")
    db_manager = DatabaseManager(db_path=db_path)

    # 2. Managers & Engines Initialization
    pet_engine = PetEngine()
    anim_engine = AnimationEngine()
    ai_manager = AIManager(
        personality=db_manager.get_setting("personality_style", "default")
    )
    personalization = PersonalizationManager(db_manager)
    pomodoro = PomodoroTimer()
    reminder_mgr = ReminderManager(db_manager)
    sticky_mgr = StickyNoteManager(db_manager)

    # Set initial screen boundaries for pet movements
    screen = app.primaryScreen()
    if screen is not None:
        screen_rect = screen.availableGeometry()
        width, height = screen_rect.width(), screen_rect.height()
    else:
        width, height = 1920, 1080
    pet_engine.set_screen_geometry(width, height)

    # 3. Main GUI window Setup
    pet_win = PetWindow(
        db_manager=db_manager,
        pet_engine=pet_engine,
        anim_engine=anim_engine,
        ai_manager=ai_manager,
        personalization=personalization,
        pomodoro=pomodoro
    )

    # 4. Integrate system monitor signals
    sys_monitor = SystemMonitor(interval_seconds=4)
    
    last_alert_time = [0.0]
    def on_metrics_updated(metrics: dict):
        cpu = metrics["cpu"]
        memory = metrics["memory"]
        now = time.time()
        # Only alert on critical threshold (>95%) with 5-minute cooldown, never forcing sleep
        if now - last_alert_time[0] > 300.0:
            if cpu > 95.0:
                last_alert_time[0] = now
                pet_win.show_message(f"CPU load is extremely high ({cpu:.1f}%)! Take a breath! 🙀", 3500)
            elif memory > 96.0:
                last_alert_time[0] = now
                pet_win.show_message(f"RAM is critical ({memory:.1f}%)! Consider closing tabs. 😿", 3500)

    sys_monitor.metrics_updated.connect(on_metrics_updated)
    sys_monitor.start()

    # 5. Connect Pomodoro timer callbacks
    def on_pomo_tick(minutes: int, seconds: int, mode: str):
        if mode == "work":
            pet_win.show_message(f"Focus Work: {minutes:02d}:{seconds:02d} 🐾", 1500)
        elif mode == "break":
            pet_win.show_message(f"Break Rest: {minutes:02d}:{seconds:02d} 💤", 1500)

    def on_pomo_finished(mode: str):
        user_name = db_manager.get_setting("user_name", "human")
        sound_enabled = db_manager.get_setting("sound_enabled", "true") == "true"
        volume = int(db_manager.get_setting("volume", "80"))
        
        if mode == "work":
            toast = NotificationWidget(f"Focus session complete, {user_name}! Take a break!")
            toast.show_notification()
            pet_win.show_message(f"Great job, {user_name}! Let's take a break! 🎉", 4000)
            anim_engine.set_state("jump")
            SoundManager.play_sound("meow", volume_percent=volume, enabled=sound_enabled)
            pomodoro.start_break()
        elif mode == "break":
            toast = NotificationWidget(f"Break ended, {user_name}! Back to focus!")
            toast.show_notification()
            pet_win.show_message(f"Break is over, {user_name}! Time to work! 🐾", 4000)
            anim_engine.set_state("walk")
            SoundManager.play_sound("meow", volume_percent=volume, enabled=sound_enabled)
            pomodoro.start_work()

    pomodoro.tick.connect(on_pomo_tick)
    pomodoro.session_completed.connect(on_pomo_finished)

    # 6. Connect reminder triggers
    def on_reminder_triggered(title: str):
        user_name = db_manager.get_setting("user_name", "human")
        sound_enabled = db_manager.get_setting("sound_enabled", "true") == "true"
        volume = int(db_manager.get_setting("volume", "80"))
        
        toast = NotificationWidget(f"Reminder: {title}")
        toast.show_notification(duration_ms=6000)
        pet_win.show_message(f"Don't forget: {title}, {user_name}! 🔔", 5000)
        anim_engine.set_state("jump")
        SoundManager.play_sound("meow", volume_percent=volume, enabled=sound_enabled)

    reminder_mgr.reminder_due.connect(on_reminder_triggered)

    # 7. Restore saved sticky notes
    sticky_mgr.load_saved_notes()

    # Show Pet Window
    pet_win.show()

    # Welcome message bubble
    QTimer.singleShot(1000, lambda: pet_win.show_message("Meow! Click me for PC Status, double-click for full HUD, or right-click for Meow Chat! 😺", 5000))

    # Run Application Event Loop
    try:
        sys.exit(app.exec())
    finally:
        # Clean shutdown of background threads
        sys_monitor.stop()
        sticky_mgr.close_all()

if __name__ == "__main__":
    from PyQt6.QtCore import QTimer
    main()
