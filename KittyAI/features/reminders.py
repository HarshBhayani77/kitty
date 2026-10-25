from datetime import datetime
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from database.database import DatabaseManager

class ReminderManager(QObject):
    """Manages tracking, triggering, and saving reminders."""
    
    reminder_due = pyqtSignal(str)  # Emits the reminder title when triggered

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        
        # Check for due reminders every 10 seconds
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_reminders)
        self.timer.start(10000)

    def add_new_reminder(self, title: str, due_time: str) -> None:
        """
        Add a reminder.
        due_time format: YYYY-MM-DD HH:MM:SS
        """
        self.db.add_reminder(title, due_time)

    def check_reminders(self) -> None:
        """Queries database for active due reminders and fires signals."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        reminders = self.db.get_all_reminders()
        
        for reminder in reminders:
            if not reminder["completed"]:
                # Parse due time and check if past/current
                try:
                    due_dt = datetime.strptime(reminder["due_time"], "%Y-%m-%d %H:%M:%S")
                    if due_dt <= datetime.now():
                        # Mark completed in DB
                        with self.db._get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute(
                                "UPDATE reminders SET completed = 1 WHERE id = ?", 
                                (reminder["id"],)
                            )
                            conn.commit()
                        
                        # Trigger alert
                        self.reminder_due.emit(reminder["title"])
                except ValueError as ve:
                    print(f"Error parsing reminder time format for '{reminder['title']}': {ve}")
