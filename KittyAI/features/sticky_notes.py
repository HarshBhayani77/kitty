from PyQt6.QtWidgets import QWidget, QTextEdit, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QMouseEvent
from database.database import DatabaseManager

class StickyNoteWindow(QWidget):
    """A frameless, editable desktop sticky note widget."""

    def __init__(self, note_id: int, content: str, x: int, y: int, color: str, db_manager: DatabaseManager, on_close_cb=None):
        super().__init__()
        self.note_id = note_id
        self.db = db_manager
        self.on_close_cb = on_close_cb
        
        self.drag_position = QPoint()

        # Window settings
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setGeometry(x, y, 200, 200)
        self.setStyleSheet(f"background-color: {color}; border: 1px solid #d0d0b0; border-radius: 4px;")

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)

        # Title bar buttons
        title_layout = QHBoxLayout()
        title_layout.addStretch()
        
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.setStyleSheet("border: none; font-weight: bold; font-size: 14px; color: #555;")
        self.close_btn.clicked.connect(self.close_and_delete)
        title_layout.addWidget(self.close_btn)
        
        layout.addLayout(title_layout)

        # Editor
        self.editor = QTextEdit()
        self.editor.setPlainText(content)
        self.editor.setStyleSheet("border: none; background: transparent; font-family: sans-serif; font-size: 11px;")
        self.editor.textChanged.connect(self.save_note)
        layout.addWidget(self.editor)

        self.setLayout(layout)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Track coordinates for dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Drag window across desktop."""
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
            self.save_note()

    def save_note(self) -> None:
        """Persists current state to SQLite database."""
        content = self.editor.toPlainText()
        pos = self.pos()
        self.db.update_note(self.note_id, content, pos.x(), pos.y())

    def close_and_delete(self) -> None:
        """Remove note from database and close widget."""
        self.db.delete_note(self.note_id)
        if self.on_close_cb:
            self.on_close_cb(self.note_id)
        self.close()


class StickyNoteManager:
    """Manages spawning, tracking, and restoring desktop sticky notes."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.active_notes = {}

    def spawn_note(self, content: str = "", x: int = 200, y: int = 200, color: str = "#ffeb3b") -> None:
        """Create new note window and save to DB."""
        note_id = self.db.add_note(content, x, y, color)
        self._create_note_window(note_id, content, x, y, color)

    def load_saved_notes(self) -> None:
        """Restore all saved sticky notes from database."""
        notes = self.db.get_all_notes()
        for note in notes:
            self._create_note_window(
                note["id"], 
                note["content"], 
                note["x"], 
                note["y"], 
                note["color"]
            )

    def _create_note_window(self, note_id: int, content: str, x: int, y: int, color: str) -> None:
        """Helper to instantiate widget and store in tracking dict."""
        note_win = StickyNoteWindow(
            note_id, content, x, y, color, self.db, self._on_note_closed
        )
        note_win.show()
        self.active_notes[note_id] = note_win

    def _on_note_closed(self, note_id: int) -> None:
        """Remove tracker reference when note window closes."""
        if note_id in self.active_notes:
            del self.active_notes[note_id]

    def close_all(self) -> None:
        """Closes all active note windows."""
        for note in list(self.active_notes.values()):
            note.close()
        self.active_notes.clear()
