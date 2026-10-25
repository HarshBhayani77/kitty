import sys
import math
import time
import random
from PyQt6.QtWidgets import QWidget, QMenu
from PyQt6.QtCore import Qt, QPoint, QRect, QRectF, QPointF, QLineF, QTimer
from PyQt6.QtGui import (
    QPainter, QColor, QMouseEvent, QPaintEvent, QPen, QPolygon, QPolygonF,
    QBrush, QAction, QFont, QCursor, QPainterPath
)
from pynput import keyboard, mouse
from core.sound_manager import SoundManager
from core.system_monitor import SystemMonitor

from database.database import DatabaseManager
from core.pet_engine import PetEngine
from core.animation_engine import AnimationEngine
from core.ai_manager import AIManager
from features.personalization import PersonalizationManager
from features.pomodoro import PomodoroTimer
from ui.pc_status_hud import PcStatusHud
from ui.chat_dialog import ChatDialog
from ui.speech_bubble import SpeechBubbleWidget


class PetWindow(QWidget):
    """The transparent, always-on-top window displaying the desktop companion cat.

    Features:
      * Structured PC Status Popup Card with Color Boxes on click.
      * Full live PC Status HUD on double-click or middle-click.
      * Eye tracking mouse cursor smoothly and continuously.
      * Realistic, natural quick-blink (80ms) keeping eyes awake and open.
      * Smooth, adorable chibi cat vector art without vibration or jagged spikes.
      * Paws strike keyboard when typing.
      * Overheat mode (blush, steam puffs) during intense typing.
      * Carry physics: Scruff dangle when dragged.
      * Customizable sizing from 50% to 200%.
      * Multiple coat skins (Black, Orange Tabby, Siamese, Mackerel, Calico) and Custom Fur.
      * Interactive Meow Chat powered by conversation API or local personality engine.
    """

    BASE_WIDTH = 140
    BASE_HEIGHT = 150

    def __init__(self, db_manager: DatabaseManager, pet_engine: PetEngine,
                 anim_engine: AnimationEngine, ai_manager: AIManager,
                 personalization: PersonalizationManager, pomodoro: PomodoroTimer):
        super().__init__()
        self.db = db_manager
        self.pet = pet_engine
        self.anim = anim_engine
        self.ai = ai_manager
        self.pers = personalization
        self.pomo = pomodoro

        self.scale_factor = 0.65
        self.drag_position = QPoint()
        self.press_pos = QPoint()
        self.has_dragged = False
        self.is_dragging = False
        self.wobble_angle = 0.0

        # Chat and input state
        self.is_thinking = False
        self.jump_y_offset = 0
        self._last_info_click_time = 0.0

        # Child windows
        self.hud = PcStatusHud()
        self.chat_dialog = ChatDialog(ai_manager=self.ai, db_manager=self.db, pet_window=self)
        self.settings_win = None

        # Frameless, on-top, tool window
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        self.resize(self.BASE_WIDTH, self.BASE_HEIGHT)

        # Floating speech bubble widget with structured color boxes & arrow pointer
        self.bubble = SpeechBubbleWidget()

        # Connect pet signals
        self.pet.position_changed.connect(self.move)
        self.pet.state_requested.connect(self.anim.set_state)
        self.anim.frame_changed.connect(self.on_frame_changed)

        # Personalization & Fur Parameters
        self.user_name = "human"
        self.pinned_note = ""
        self.custom_fur_enabled = False
        self.body_color_hex = "#111111"
        self.belly_color_hex = "#222222"
        self.eye_color_hex = "#ffeb3b"
        self.pattern_type = "none"
        self.pattern_color_hex = "#444444"

        # Shake and Wobble tracking
        self.wobble_force = 0.0
        self.last_drag_pos = QPoint()

        # Global Mouse/Cursor tracking for Follow & Hunt
        self.last_global_cursor_pos = QCursor.pos()
        self.petting_points = 0.0
        self.last_pet_x = 0

        # Typing Speed tracking (Overheat Mode)
        self.typing_timestamps = []
        self.is_overheated = False
        self.steam_puffs = []
        self.hearts = []

        # Typing hands animation
        self.last_type_time = 0.0
        self.typing_paw = False

        # Natural, quick-blink timing (80ms blink duration)
        self._next_blink = time.time() + random.uniform(3.0, 6.5)
        self._blink_end = 0.0

        # Scroll unrolling tracking
        self.paper_unroll_val = 0.0
        self.last_scroll_time = 0.0

        # Stretch Reminder active
        self.is_stretching = False

        # State monitoring timer running at ~30 FPS
        self.tracking_timer = QTimer(self)
        self.tracking_timer.timeout.connect(self._track_mouse_and_state)
        self.tracking_timer.start(33)

        self.stretch_timer = QTimer(self)
        self.stretch_timer.timeout.connect(self._trigger_stretch)
        self.stretch_timer.start(120000)

        self.stretch_active_timer = QTimer(self)
        self.stretch_active_timer.setSingleShot(True)
        self.stretch_active_timer.timeout.connect(self._stop_stretch)

        # Load dynamic configurations
        self.load_local_settings()

        # Initialize pynput listeners
        self.keyboard_listener = keyboard.Listener(on_press=self._on_key_press)
        self.keyboard_listener.start()

        self.scroll_listener = mouse.Listener(on_scroll=self._on_scroll)
        self.scroll_listener.start()

        # Trigger initial position
        self.move(self.pet.x, self.pet.y)

    def load_local_settings(self) -> None:
        """Reload user personalization, size scale, and appearance from database."""
        self.user_name = self.db.get_setting("user_name", "human") or "human"
        self.pinned_note = self.db.get_setting("pinned_note", "")

        # Scale Factor & Window Resize
        scale_pct = int(self.db.get_setting("pet_scale", "65"))
        self.scale_factor = max(0.30, min(1.8, scale_pct / 100.0))
        new_w = int(self.BASE_WIDTH * self.scale_factor)
        new_h = int(self.BASE_HEIGHT * self.scale_factor)
        self.resize(new_w, new_h)

        # Custom fur & colors
        self.custom_fur_enabled = self.db.get_setting("custom_fur_enabled", "false") == "true"
        self.body_color_hex = self.db.get_setting("body_color", "#111111")
        self.belly_color_hex = self.db.get_setting("belly_color", "#222222")
        self.eye_color_hex = self.db.get_setting("eye_color", "#ffeb3b")
        self.pattern_type = self.db.get_setting("pattern_type", "none")
        self.pattern_color_hex = self.db.get_setting("pattern_color", "#444444")

        # Stretch interval
        try:
            stretch_interval = int(self.db.get_setting("stretch_interval", "30"))
            if stretch_interval > 0:
                self.stretch_timer.start(stretch_interval * 60000)
            else:
                self.stretch_timer.stop()
        except ValueError:
            pass

        self._reposition_bubble()
        self.update()

    def _on_key_press(self, key) -> None:
        """Trigger typing paws and count typing speed for Overheat Mode."""
        now = time.time()
        self.typing_timestamps.append(now)
        self.last_type_time = now
        self.typing_paw = not self.typing_paw
        QTimer.singleShot(0, lambda: self.anim.set_state("knead"))
        QTimer.singleShot(900, lambda: self.anim.set_state("idle") if self.anim.current_state == "knead" else None)

    def _on_scroll(self, x, y, dx, dy) -> None:
        """Trigger paper unspooling when user scrolls globally."""
        self.last_scroll_time = time.time()
        self.paper_unroll_val = min(150.0, self.paper_unroll_val + 6.0)
        QTimer.singleShot(0, lambda: self.anim.set_state("knead"))
        QTimer.singleShot(0, lambda: self.show_message("Wheee! Scroll scroll! 🧻", 2000))

    def _trigger_stretch(self) -> None:
        """Let pet grow big and stretch."""
        self.is_stretching = True
        self.anim.set_state("jump")
        self.show_message(f"Paws up! Let's stretch together, {self.user_name}! 🐈", 8000)
        SoundManager.play_sound("meow", volume_percent=int(self.db.get_setting("volume", "80")), enabled=self.db.get_setting("sound_enabled", "true") == "true")
        self.stretch_active_timer.start(10000)
        self.update()

    def _stop_stretch(self) -> None:
        """Return pet to regular size."""
        self.is_stretching = False
        self.anim.set_state("idle")
        self.update()

    def _track_mouse_and_state(self) -> None:
        """Background state monitoring running at ~30 FPS."""
        now = time.time()

        # Natural, fast blink scheduling (0.08s quick blink)
        if now >= self._next_blink and now >= self._blink_end:
            self._blink_end = now + 0.08  # 80ms quick natural blink!
            self._next_blink = now + random.uniform(3.5, 7.5)

        # Shake and Wobble: only active when dragging
        if self.is_dragging:
            if self.wobble_force > 0.1:
                self.wobble_angle = math.sin(time.time() * 20.0) * self.wobble_force
                self.wobble_force *= 0.88
            else:
                self.wobble_angle = 0.0
        else:
            self.wobble_angle = 0.0
            self.wobble_force = 0.0

        # Global Mouse Hunt tracking
        cursor_pos = QCursor.pos()
        delta_pos = cursor_pos - self.last_global_cursor_pos
        self.last_global_cursor_pos = cursor_pos
        mouse_speed = math.sqrt(delta_pos.x()**2 + delta_pos.y()**2)

        if mouse_speed > 90 and not self.is_dragging and not self.pet.hunting:
            self.show_message(f"Hunting cursor, {self.user_name}! 😼", 1500)
            self.pet.hunt_target(cursor_pos)
            SoundManager.play_sound("meow", volume_percent=int(self.db.get_setting("volume", "80")), enabled=self.db.get_setting("sound_enabled", "true") == "true")

        # Typing Speed check (Overheat)
        self.typing_timestamps = [t for t in self.typing_timestamps if now - t < 3.0]
        if len(self.typing_timestamps) > 15:
            if not self.is_overheated:
                self.is_overheated = True
                self.show_message(f"Typing too fast! Overheating, {self.user_name}! 🔥", 3000)
                SoundManager.play_sound("meow", volume_percent=int(self.db.get_setting("volume", "80")), enabled=self.db.get_setting("sound_enabled", "true") == "true")
            if random.random() < 0.25:
                self.steam_puffs.append({"x": random.randint(-16, 16), "y": -46, "radius": 3, "opacity": 1.0})
        else:
            self.is_overheated = False

        # Update particles
        for p in self.steam_puffs:
            p["radius"] += 0.3
            p["y"] -= 2
            p["opacity"] -= 0.05
        self.steam_puffs = [p for p in self.steam_puffs if p["opacity"] > 0]

        for h in self.hearts:
            h["y"] -= 1.5
            h["x"] += h["dx"]
            h["opacity"] -= 0.04
        self.hearts = [h for h in self.hearts if h["opacity"] > 0]

        # Paper Scroll unroll decay
        if now - self.last_scroll_time > 2.0 and self.paper_unroll_val > 0:
            self.paper_unroll_val = max(0.0, self.paper_unroll_val - 3.0)

        # Reposition bubble if visible
        if self.bubble.isVisible():
            self._reposition_bubble()

        self.update()

    def on_frame_changed(self, frame: int) -> None:
        self.update()

    def show_message(self, message: str, duration_ms: int = 4000) -> None:
        """Display a speech bubble dialog above the pet's head."""
        self.bubble.show_dialog_text(message, duration_ms)
        self._reposition_bubble()

    def _reposition_bubble(self) -> None:
        """Keep the bubble centered just above the cat's head for any scale."""
        if not self.bubble.isVisible():
            return
        bx = self.x() + (self.width() // 2) - (self.bubble.width() // 2)
        by = self.y() + int(12 * self.scale_factor) - self.bubble.height()
        self.bubble.move(bx, by)

    def hide_bubble(self) -> None:
        self.bubble.hide_bubble()

    def draw_pixel_heart(self, painter: QPainter, x: int, y: int, size: int, color: QColor) -> None:
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        s = size * 2.2
        painter.drawEllipse(QRectF(x - s * 0.5, y - s * 0.5, s * 0.55, s * 0.55))
        painter.drawEllipse(QRectF(x - s * 0.05, y - s * 0.5, s * 0.55, s * 0.55))
        tri = QPolygonF([
            QPointF(x - s * 0.5, y - s * 0.15),
            QPointF(x + s * 0.55, y - s * 0.15),
            QPointF(x + 0.02 * s, y + s * 0.55),
        ])
        painter.drawPolygon(tri)
        painter.restore()

    def mousePressEvent(self, a0: QMouseEvent | None) -> None:
        if a0 is None:
            return
        event = a0
        if event.button() == Qt.MouseButton.LeftButton:
            self.press_pos = event.globalPosition().toPoint()
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.last_drag_pos = event.globalPosition().toPoint()
            self.has_dragged = False
            event.accept()

    def mouseMoveEvent(self, a0: QMouseEvent | None) -> None:
        if a0 is None:
            return
        event = a0
        if event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self.press_pos
            if not self.has_dragged and (abs(delta.x()) > 5 or abs(delta.y()) > 5):
                self.has_dragged = True
                self.is_dragging = True
                self.anim.set_state("drag")

            if self.is_dragging:
                new_pos = event.globalPosition().toPoint() - self.drag_position
                self.pet.set_position(new_pos.x(), new_pos.y())
                current_pos = event.globalPosition().toPoint()
                delta_drag = current_pos - self.last_drag_pos
                self.last_drag_pos = current_pos
                drag_speed = math.sqrt(delta_drag.x()**2 + delta_drag.y()**2)
                if drag_speed > 8:
                    self.wobble_force = min(25.0, self.wobble_force + drag_speed * 0.3)
                event.accept()
                return

        # Head petting gesture & eye tracking when not dragging
        local_pos = event.position().toPoint()
        head_min_x = 55 * self.scale_factor
        head_max_x = 125 * self.scale_factor
        head_min_y = 45 * self.scale_factor
        head_max_y = 125 * self.scale_factor
        if head_min_x <= local_pos.x() <= head_max_x and head_min_y <= local_pos.y() <= head_max_y:
            dx = local_pos.x() - self.last_pet_x
            self.last_pet_x = local_pos.x()
            if abs(dx) > 2:
                self.petting_points += 1.0
                if random.random() < 0.4:
                    self.hearts.append({
                        "x": random.randint(-18, 18),
                        "y": -46,
                        "opacity": 1.0,
                        "size": random.choice([2, 3]),
                        "dx": random.uniform(-0.6, 0.6)
                    })
                if self.petting_points > 25:
                    self.petting_points = 0
                    self.show_message("Purrrr... ❤️", 2500)
                    SoundManager.play_sound("purr", volume_percent=int(self.db.get_setting("volume", "80")), enabled=self.db.get_setting("sound_enabled", "true") == "true")
        else:
            self.petting_points = max(0.0, self.petting_points - 0.2)
            self.pet.hunt_target(event.globalPosition().toPoint())

    def mouseReleaseEvent(self, a0: QMouseEvent | None) -> None:
        if a0 is None:
            return
        event = a0
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.has_dragged:
                now = time.time()
                # 1st Click -> Show Information (System Status Card)
                # 2nd Click -> Open Chat Window!
                if self.bubble.isVisible() or (now - self._last_info_click_time < 4.0):
                    self.hide_bubble()
                    self.open_chat_dialog()
                    self._last_info_click_time = 0.0
                else:
                    self._last_info_click_time = now
                    self.on_pet_clicked()
            else:
                self.is_dragging = False
                self.anim.set_state("idle")
                self.pet.stop_hunting()
            event.accept()
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.toggle_pc_status_hud()
            event.accept()

    def mouseDoubleClickEvent(self, a0: QMouseEvent | None) -> None:
        if a0 and a0.button() == Qt.MouseButton.LeftButton:
            # Rapid 2nd click / double-click opens chat directly
            self.hide_bubble()
            self.open_chat_dialog()
            self._last_info_click_time = 0.0
            a0.accept()

    def on_pet_clicked(self) -> None:
        """Called on click on Kitty: shows structured Color Box Status Card and purrs!"""
        snap = SystemMonitor.get_system_snapshot()
        vol = int(self.db.get_setting("volume", "80"))
        snd = self.db.get_setting("sound_enabled", "true") == "true"
        SoundManager.play_sound("purr", volume_percent=vol, enabled=snd)

        # Show the structured 2x2 colored box card!
        self.bubble.show_status_snapshot(snap, duration_ms=6500)
        self._reposition_bubble()

    def leaveEvent(self, a0) -> None:
        self.pet.stop_hunting()

    def toggle_pc_status_hud(self) -> None:
        """Toggle the full PC Status HUD window next to the pet."""
        if not hasattr(self, 'hud') or self.hud is None:
            self.hud = PcStatusHud()
        self.hud.toggle_hud(self.x(), self.y())

    def open_chat_dialog(self) -> None:
        """Open the interactive Meow Chat window and focus the prompt input."""
        if not hasattr(self, 'chat_dialog') or self.chat_dialog is None:
            self.chat_dialog = ChatDialog(ai_manager=self.ai, db_manager=self.db, pet_window=self)
        cx = max(30, self.x() - 400)
        cy = max(30, min(self.y() - 120, 500))
        self.chat_dialog.move(cx, cy)
        self.chat_dialog.show()
        self.chat_dialog.raise_()
        self.chat_dialog.activateWindow()
        if hasattr(self.chat_dialog, 'input_field'):
            self.chat_dialog.input_field.setFocus()

    def contextMenuEvent(self, a0) -> None:
        """Spawn right-click menu options."""
        event = a0
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1a1a2e;
                color: #ffffff;
                border: 1px solid #e74c3c;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 18px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #e74c3c;
                color: #ffffff;
            }
        """)

        action_hud = QAction("📊 PC Status HUD", self)
        action_hud.triggered.connect(self.toggle_pc_status_hud)
        menu.addAction(action_hud)

        action_chat = QAction("💬 Meow Chat", self)
        action_chat.triggered.connect(self.open_chat_dialog)
        menu.addAction(action_chat)

        menu.addSeparator()

        action_pomo = QAction("🎯 Pomodoro Focus", self)
        action_pomo.triggered.connect(self.toggle_pomodoro)
        menu.addAction(action_pomo)

        action_note = QAction("📝 New Sticky Note", self)
        action_note.triggered.connect(self.create_sticky_note)
        menu.addAction(action_note)

        action_pin = QAction("📌 Pin Note...", self)
        action_pin.triggered.connect(self.trigger_pin_note)
        menu.addAction(action_pin)

        if self.pinned_note:
            action_unpin = QAction("🗑️ Clear Pinned Note", self)
            action_unpin.triggered.connect(self.trigger_clear_pinned_note)
            menu.addAction(action_unpin)

        menu.addSeparator()

        action_settings = QAction("⚙️ Settings", self)
        action_settings.triggered.connect(self.open_settings)
        menu.addAction(action_settings)

        action_exit = QAction("❌ Exit Kitty", self)
        action_exit.triggered.connect(self.quit_app)
        menu.addAction(action_exit)

        menu.exec(event.globalPos())

    def trigger_pin_note(self) -> None:
        from PyQt6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, "Pin Note", "Pin an important note above kitty's head:")
        if ok and text.strip():
            self.pinned_note = text.strip()
            self.db.set_setting("pinned_note", self.pinned_note)
            self.update()

    def trigger_clear_pinned_note(self) -> None:
        self.pinned_note = ""
        self.db.set_setting("pinned_note", "")
        self.update()

    def toggle_pomodoro(self) -> None:
        if self.pomo.current_mode == "idle":
            self.pomo.start_work()
            self.show_message("Focus time! Paws down, keep working! 🐾")
        else:
            self.pomo.stop()
            self.show_message("Pomodoro stopped. Rest easy.")

    def create_sticky_note(self) -> None:
        from features.sticky_notes import StickyNoteManager
        mgr = StickyNoteManager(self.db)
        mgr.spawn_note("Meow, write something!", self.x() - 220, self.y())

    def open_settings(self) -> None:
        from ui.settings_window import SettingsWindow
        self.settings_win = SettingsWindow(self.db)
        self.settings_win.settings_saved.connect(self.load_local_settings)
        self.settings_win.show()

    # ------------------------------------------------------------------
    #  Rendering & Fur Patterns (Clean, Cute, Smooth Vector Graphics)
    # ------------------------------------------------------------------
    def _resolve_colors(self) -> dict:
        """Resolve the active palette from custom fur or the selected skin."""
        if self.custom_fur_enabled:
            return {
                "body": QColor(self.body_color_hex),
                "belly": QColor(self.belly_color_hex),
                "eyes": QColor(self.eye_color_hex),
                "nose": QColor("#f88888"),
                "pattern": self.pattern_type,
                "pattern_color": QColor(self.pattern_color_hex),
                "points": None,
                "skin": "custom"
            }
        skin = self.pers.get_current_skin()
        skin_colors = {
            "black": {
                "body": QColor("#1c1c22"), "belly": QColor("#2d2d38"),
                "eyes": QColor("#f2c14e"), "nose": QColor("#d98a9a"),
                "pattern": "none", "pattern_color": QColor("#111115"),
                "points": None, "skin": "black"
            },
            "orange": {
                "body": QColor("#d9772e"), "belly": QColor("#f2c48a"),
                "eyes": QColor("#27ae60"), "nose": QColor("#e88b9a"),
                "pattern": "stripes", "pattern_color": QColor("#ba4a00"),
                "points": None, "skin": "orange"
            },
            "siamese": {
                "body": QColor("#f4ece1"), "belly": QColor("#fdfefe"),
                "eyes": QColor("#3498db"), "nose": QColor("#5a4536"),
                "pattern": "siamese_points", "pattern_color": QColor("#4a3728"),
                "points": QColor("#4a3728"), "skin": "siamese"
            },
            "mackerel": {
                "body": QColor("#7f8c8d"), "belly": QColor("#ecf0f1"),
                "eyes": QColor("#2ecc71"), "nose": QColor("#e88b9a"),
                "pattern": "stripes", "pattern_color": QColor("#2c3e50"),
                "points": None, "skin": "mackerel"
            },
            "calico": {
                "body": QColor("#ffffff"), "belly": QColor("#ffffff"),
                "eyes": QColor("#f39c12"), "nose": QColor("#f88888"),
                "pattern": "calico_patches", "pattern_color": QColor("#d9772e"),
                "points": QColor("#2c3e50"), "skin": "calico"
            }
        }
        return skin_colors.get(skin, skin_colors["black"])

    def paintEvent(self, a0: QPaintEvent | None) -> None:
        """Draw the pet programmatically with smooth, calm, vibration-free QPainter primitives."""
        if a0 is None:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        colors = self._resolve_colors()

        frame = self.anim.current_frame
        state = self.anim.current_state
        now = time.time()
        dragging = self.is_dragging
        typing_active = (now - self.last_type_time) < 0.45 and not dragging

        # Transform parameters: zero jitter/vibration
        scale_x = 1.0
        scale_y = 1.0
        cy_lift = 0
        if self.is_stretching:
            scale_x = scale_y = 1.6
        elif dragging:
            scale_x = 0.88
            scale_y = 1.25
            cy_lift = -6

        cx = self.width() / 2.0
        cy = (self.height() / 2.0) + (cy_lift - self.jump_y_offset) * self.scale_factor + int(14 * self.scale_factor)

        # --- Floating pinned note callout above the head ---
        if self.pinned_note:
            painter.save()
            painter.setBrush(QBrush(QColor("#fff9c4")))
            painter.setPen(QPen(QColor("#d4c970"), 1.5))
            text_width = len(self.pinned_note) * 6 + 12
            rect_x = int(cx - text_width // 2)
            rect_y = int(cy - (75 if not self.is_stretching else 115) * self.scale_factor)
            painter.drawRoundedRect(rect_x, rect_y, text_width, 18, 4, 4)
            pointer = QPolygon([
                QPoint(int(cx - 4), rect_y + 18),
                QPoint(int(cx + 4), rect_y + 18),
                QPoint(int(cx), rect_y + 22)
            ])
            painter.drawPolygon(pointer)
            painter.setPen(QColor("#000000"))
            painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            painter.drawText(rect_x + 6, rect_y + 13, self.pinned_note)
            painter.restore()

        # --- Floating pomodoro timer next to pet ---
        if self.pomo.current_mode != "idle":
            painter.save()
            minutes = self.pomo.time_remaining // 60
            seconds = self.pomo.time_remaining % 60
            pomo_text = f"{minutes:02d}:{seconds:02d}"
            box_x = int(cx + 38 * self.scale_factor)
            box_y = int(cy - 20 * self.scale_factor)
            box_color = QColor("#e74c3c") if self.pomo.current_mode == "work" else QColor("#2ecc71")
            painter.setBrush(QBrush(QColor("#1a1a2e")))
            painter.setPen(QPen(box_color, 2))
            painter.drawRoundedRect(box_x, box_y, 48, 16, 4, 4)
            painter.setPen(QColor("#ffffff"))
            painter.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
            painter.drawText(box_x + 6, box_y + 12, pomo_text)
            painter.restore()

        # --- Pupil direction toward cursor ---
        pupil_dx = 0.0
        pupil_dy = 0.0
        if now >= self._blink_end:
            cur = QCursor.pos()
            hx = self.x() + cx
            hy = self.y() + cy - 18 * self.scale_factor
            ex = cur.x() - hx
            ey = cur.y() - hy
            dist = math.hypot(ex, ey)
            if dist > 1.0:
                pupil_dx = max(-3.0, min(3.0, (ex / dist) * 3.0))
                pupil_dy = max(-2.5, min(2.5, (ey / dist) * 2.5))

        # --- Main Cat Drawing Space ---
        painter.save()
        painter.translate(cx, cy)
        if dragging and self.wobble_angle != 0.0:
            painter.rotate(self.wobble_angle)
        painter.scale(self.scale_factor * scale_x, self.scale_factor * scale_y)

        # Steam puffs
        if self.steam_puffs:
            painter.save()
            painter.setPen(Qt.PenStyle.NoPen)
            for p in self.steam_puffs:
                painter.setBrush(QBrush(QColor(240, 240, 240, int(p["opacity"] * 220))))
                painter.drawEllipse(QRectF(p["x"], p["y"], p["radius"], p["radius"]))
            painter.restore()

        self._draw_cat(painter, colors, state, frame, typing_active, dragging,
                       self.is_thinking, pupil_dx, pupil_dy)

        # Hearts
        for h in self.hearts:
            heart_color = QColor(255, 70, 90, int(h["opacity"] * 255))
            self.draw_pixel_heart(painter, int(h["x"]), int(h["y"]), int(h["size"]), heart_color)

        painter.restore()
        painter.end()

    def _fur_blob(self, painter: QPainter, cx: float, cy: float, rx: float, ry: float,
                  fill: QColor, tuft_len: float = 5.0, n: int = 22, phase: float = 0.0) -> None:
        """Draw a fluffy fur blob: an ellipse with stylized spiky fur tufts around the rim."""
        path = QPainterPath()
        first = True
        for i in range(n + 1):
            a = phase + (i / n) * 2 * math.pi
            bx = cx + math.cos(a) * rx
            by = cy + math.sin(a) * ry
            if first:
                path.moveTo(bx, by)
                first = False
            else:
                am = a - (math.pi / n)
                tx = cx + math.cos(am) * (rx + tuft_len)
                ty = cy + math.sin(am) * (ry + tuft_len)
                path.lineTo(tx, ty)
                path.lineTo(bx, by)
        path.closeSubpath()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(fill)
        painter.drawPath(path)

    def _draw_cat(self, painter: QPainter, colors: dict, state: str, frame: int,
                  typing_active: bool, dragging: bool, thinking: bool,
                  pupil_dx: float, pupil_dy: float) -> None:
        """Draw the iconic fluffy, spiky-furred companion. 100% calm and static without vibration motion."""
        now = time.time()
        heat = 1.0 if self.is_overheated else 0.0

        def tint(c: QColor, f: float) -> QColor:
            c = QColor(c)
            if f <= 0: return c
            return QColor(
                min(255, int(c.red() + (235 - c.red()) * 0.55 * f)),
                max(0, int(c.green() + (70 - c.green()) * 0.55 * f)),
                max(0, int(c.blue() + (70 - c.blue()) * 0.55 * f)),
                c.alpha(),
            )

        fur = tint(colors["body"], heat)
        fur_dark = QColor(fur).darker(150)
        fur_light = tint(colors["belly"], heat * 0.5)
        amber = QColor(colors["eyes"])
        amber_dark = QColor(amber).darker(135)
        nose_c = QColor(colors["nose"])
        pupil_c = QColor("#14140f")
        ear_in = QColor(nose_c).darker(115)

        pattern = colors.get("pattern", "none")
        pat_color = colors.get("pattern_color", QColor("#ba4a00"))
        points_color = colors.get("points", None)

        # Only close eyes during actual 80ms quick blink
        blinking = now < self._blink_end
        eyes_closed = blinking

        # 1. Ground shadow
        if not dragging and not self.is_stretching:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 55))
            painter.drawEllipse(QRectF(-30, 48, 60, 13))

        # 2. Heat aura
        if heat > 0:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 90, 60, 45))
            painter.drawEllipse(QRectF(-38, -58, 76, 66))

        # 3. Fluffy Bushy Tail (Calm static curl with zero motion jitter)
        tail_fur = points_color if (pattern == "siamese_points" and points_color) else fur
        if dragging:
            tail_pts = [(20, 40, 11), (30, 30, 12), (34, 16, 12), (30, 4, 10)]
        else:
            tail_pts = [(26, 34, 12), (40, 26, 13), (46, 8, 12), (42, -8, 10), (34, -18, 7)]

        for tx, ty, tr in tail_pts:
            self._fur_blob(painter, tx, ty, tr, tr, fur_dark, tuft_len=4, n=14)
        for tx, ty, tr in tail_pts:
            self._fur_blob(painter, tx, ty, tr - 2, tr - 2, tail_fur, tuft_len=3, n=12)

        if pattern == "stripes":
            painter.save()
            painter.setPen(QPen(pat_color, 2.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            for tx, ty, tr in tail_pts[1:4]:
                painter.drawLine(QLineF(tx - 4, ty - 2, tx + 4, ty + 2))
            painter.restore()

        # 4. Spiky Fluffy Ears (behind head)
        ear_fur = points_color if (pattern == "siamese_points" and points_color) else fur
        if dragging:
            ears = [(-20, -34), (20, -34)]
        else:
            ears = [(-19, -42), (19, -42)]

        for i, (ex, ey) in enumerate(ears):
            self._fur_blob(painter, ex, ey, 12, 15, fur_dark, tuft_len=5, n=12)
            self._fur_blob(painter, ex, ey, 9, 12, ear_fur, tuft_len=4, n=11)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(ear_in)
            painter.drawEllipse(QRectF(ex - 3.5, ey - 4, 7, 11))

        # 5. Fluffy Body (The iconic tufted fur silhouette)
        self._fur_blob(painter, 0, 22, 30, 26, fur_dark, tuft_len=6, n=26)
        self._fur_blob(painter, 0, 22, 27, 23, fur, tuft_len=5, n=24)

        # Calico body patches
        if pattern == "calico_patches":
            painter.save()
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(pat_color)
            painter.drawEllipse(QRectF(-20, 10, 18, 16))
            if points_color:
                painter.setBrush(points_color)
                painter.drawEllipse(QRectF(4, 20, 18, 15))
            painter.restore()

        # Soft chest sheen (subtle bib)
        painter.setPen(Qt.PenStyle.NoPen)
        sheen = QColor(fur_light)
        sheen.setAlpha(80)
        painter.setBrush(sheen)
        painter.drawEllipse(QRectF(-11, 14, 22, 26))

        # Tabby body stripes
        if pattern == "stripes":
            painter.save()
            painter.setPen(QPen(pat_color, 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawArc(QRectF(-22, 14, 16, 12), 40 * 16, 100 * 16)
            painter.drawArc(QRectF(-22, 24, 16, 12), 40 * 16, 100 * 16)
            painter.drawArc(QRectF(6, 14, 16, 12), 40 * 16, 100 * 16)
            painter.drawArc(QRectF(6, 24, 16, 12), 40 * 16, 100 * 16)
            painter.restore()

        # 6. Fluffy Head (Big, fluffy, tufted cheek silhouette)
        self._fur_blob(painter, 0, -18, 33, 30, fur_dark, tuft_len=6, n=30, phase=0.15)
        self._fur_blob(painter, 0, -18, 30, 27, fur, tuft_len=5, n=28, phase=0.15)

        # Siamese mask
        if pattern == "siamese_points" and points_color:
            painter.save()
            painter.setPen(Qt.PenStyle.NoPen)
            mask_col = QColor(points_color)
            mask_col.setAlpha(235)
            painter.setBrush(mask_col)
            painter.drawEllipse(QRectF(-18, -25, 36, 26))
            painter.restore()

        # Calico head patch
        if pattern == "calico_patches":
            painter.save()
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(pat_color)
            painter.drawEllipse(QRectF(4, -36, 18, 16))
            painter.restore()

        # Tabby forehead "M"
        if pattern == "stripes":
            painter.save()
            painter.setPen(QPen(pat_color, 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            m_path = QPainterPath()
            m_path.moveTo(-7, -29)
            m_path.lineTo(-3.5, -22)
            m_path.lineTo(0, -26)
            m_path.lineTo(3.5, -22)
            m_path.lineTo(7, -29)
            painter.drawPath(m_path)
            painter.restore()

        # 7. Cheeks / Blush
        blush = 120 if typing_active else 40
        if heat > 0: blush = 220
        blush += int(min(70, self.petting_points * 3))
        if blush > 0:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 130, 140, min(220, blush)))
            painter.drawEllipse(QRectF(-27, -12, 15, 9))
            painter.drawEllipse(QRectF(12, -12, 15, 9))

        # 8. Eyes (Awake, bright, cursor-tracking, with stylized grumpy lids)
        eye_centres = [(-12, -20), (12, -20)]
        er_x, er_y = 10.0, 11.0
        if eyes_closed:
            eye_pen = QPen(fur_dark, 2.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(eye_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for ex, ey in eye_centres:
                arc = QPainterPath()
                arc.moveTo(ex - 8, ey - 1)
                arc.quadTo(ex, ey + 4, ex + 8, ey - 1)
                painter.drawPath(arc)
        else:
            for idx, (ex, ey) in enumerate(eye_centres):
                inner_sign = 1 if ex < 0 else -1  # toward the nose
                # Amber sclera
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(amber_dark)
                painter.drawEllipse(QRectF(ex - er_x, ey - er_y, 2 * er_x, 2 * er_y))
                painter.setBrush(amber)
                painter.drawEllipse(QRectF(ex - er_x + 1.5, ey - er_y + 1.5, 2 * er_x - 3, 2 * er_y - 3))
                # Slit pupil (smoothly tracks cursor)
                painter.setBrush(pupil_c)
                painter.drawEllipse(QRectF(ex - 2.4 + pupil_dx, ey - 7.5 + pupil_dy, 4.8, 15))
                # Glossy highlight
                painter.setBrush(QColor(255, 255, 255, 220))
                painter.drawEllipse(QRectF(ex - 4 + pupil_dx, ey - 6 + pupil_dy, 3.2, 3.2))
                # Grumpy stylized upper lid
                if not dragging:
                    inner_x = ex + inner_sign * (er_x + 1.5)
                    outer_x = ex - inner_sign * (er_x + 1.5)
                    lid = QPolygonF([
                        QPointF(outer_x, ey - er_y - 2),
                        QPointF(inner_x, ey - er_y - 2),
                        QPointF(inner_x, ey + 1),
                        QPointF(outer_x, ey - er_y + 4),
                    ])
                    painter.setBrush(fur)
                    painter.drawPolygon(lid)
                    # Brow tuft
                    painter.setBrush(fur_dark)
                    brow = QPolygonF([
                        QPointF(outer_x, ey - er_y - 1),
                        QPointF(inner_x, ey - er_y - 4),
                        QPointF(inner_x, ey - er_y + 1),
                    ])
                    painter.drawPolygon(brow)

        # 9. Nose
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(nose_c)
        painter.drawPolygon(QPolygonF([
            QPointF(-4, -6), QPointF(4, -6), QPointF(0, -1)
        ]))

        # 10. Cute downturned :3 mouth & little white fang
        mouth_pen = QPen(fur_dark, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(mouth_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        if dragging:
            painter.setBrush(QColor("#7a3540"))
            painter.drawEllipse(QRectF(-3.5, -1, 7, 7))
            painter.setBrush(Qt.BrushStyle.NoBrush)
        else:
            m = QPainterPath()
            m.moveTo(0, -1)
            m.quadTo(-5, 3, -10, 0)
            m.moveTo(0, -1)
            m.quadTo(5, 3, 10, 0)
            painter.drawPath(m)
            # Little white fang
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#fffdf5"))
            painter.drawPolygon(QPolygonF([
                QPointF(-6, 1), QPointF(-2.5, 1), QPointF(-4, 6)
            ]))

        # 11. Whiskers (3 on each side)
        whisker_pen = QPen(QColor(230, 230, 230, 160), 1.3)
        painter.setPen(whisker_pen)
        for sign in (-1, 1):
            painter.drawLine(QLineF(sign * 10, -8, sign * 34, -12))
            painter.drawLine(QLineF(sign * 10, -5, sign * 36, -5))
            painter.drawLine(QLineF(sign * 10, -2, sign * 34, 3))

        # Sweat drop when overheating
        if heat > 0:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(120, 195, 255, 230))
            painter.drawEllipse(QRectF(24, -40, 6, 8))

        # 12. Fluffy Front Paws (with fur tufts)
        paw_color = fur
        if pattern == "socks":
            paw_color = pat_color
        elif pattern == "siamese_points" and points_color:
            paw_color = points_color

        if dragging:
            self._draw_dangling_limbs(painter, fur, fur_dark, paw_color)
        elif typing_active:
            self._draw_typing_paws(painter, fur, fur_dark, paw_color)
        else:
            for px in (-13, 13):
                self._fur_blob(painter, px, 44, 9, 8, fur_dark, tuft_len=3, n=12)
                self._fur_blob(painter, px, 44, 7, 6, paw_color, tuft_len=2, n=10)
            toe_pen = QPen(fur_dark, 1.2)
            painter.setPen(toe_pen)
            painter.drawLine(QLineF(-13, 42, -13, 48))
            painter.drawLine(QLineF(13, 42, 13, 48))

        # Thinking bubbles
        if thinking:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 255, 255, 235))
            painter.drawEllipse(QRectF(18, -52, 5, 5))
            painter.drawEllipse(QRectF(24, -60, 8, 8))
            painter.drawEllipse(QRectF(32, -72, 11, 11))

    def _draw_typing_paws(self, painter: QPainter, fur: QColor, fur_dark: QColor,
                          paw_fill: QColor) -> None:
        """Draw a mini keyboard and two paws alternating on the left/right keys."""
        down_left = self.typing_paw

        # Keyboard base plate
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(40, 42, 54))
        painter.drawRoundedRect(QRectF(-24, 52, 48, 14), 3, 3)

        def draw_key(kcx: float, pressed: bool) -> None:
            top = 55 + (2 if pressed else 0)
            painter.setBrush(QColor(70, 72, 86))
            painter.drawRoundedRect(QRectF(kcx - 8, top, 16, 8), 2, 2)
            painter.setBrush(QColor(110, 112, 128) if pressed else QColor(155, 157, 173))
            painter.drawRoundedRect(QRectF(kcx - 7, top - 1, 14, 5), 2, 2)

        draw_key(-12, down_left)
        draw_key(12, not down_left)

        l_paw_y = 48 if down_left else 40
        r_paw_y = 40 if down_left else 48

        arm_pen = QPen(fur, 9, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(arm_pen)
        painter.drawLine(QLineF(-11, 14, -12, l_paw_y))
        painter.drawLine(QLineF(11, 14, 12, r_paw_y))

        self._fur_blob(painter, -12, l_paw_y, 8, 7, fur_dark, tuft_len=3, n=11)
        self._fur_blob(painter, -12, l_paw_y, 6, 5, paw_fill, tuft_len=2, n=9)
        self._fur_blob(painter, 12, r_paw_y, 8, 7, fur_dark, tuft_len=3, n=11)
        self._fur_blob(painter, 12, r_paw_y, 6, 5, paw_fill, tuft_len=2, n=9)

    def _draw_dangling_limbs(self, painter: QPainter, fur: QColor,
                             fur_dark: QColor, paw_fill: QColor) -> None:
        """Draw limbs and paws hanging loosely while the cat is carried."""
        limb_pen = QPen(fur, 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(limb_pen)
        painter.drawLine(QLineF(-10, 6, -13, 42))
        painter.drawLine(QLineF(10, 6, 13, 44))
        painter.drawLine(QLineF(-7, 30, -9, 52))
        painter.drawLine(QLineF(7, 30, 10, 54))

        for px, py in [(-13, 42), (13, 44), (-9, 52), (10, 54)]:
            self._fur_blob(painter, px, py, 6, 6, paw_fill, tuft_len=2, n=9)

        # Scruff tuft at the top
        self._fur_blob(painter, 0, -50, 7, 9, fur_dark, tuft_len=4, n=10)

    def quit_app(self) -> None:
        """Shut down listeners and close app."""
        try:
            self.keyboard_listener.stop()
            self.scroll_listener.stop()
        except Exception:
            pass
        if hasattr(self, 'hud') and self.hud:
            self.hud.close()
        if hasattr(self, 'chat_dialog') and self.chat_dialog:
            self.chat_dialog.close()
        self.bubble.close()
        self.close()
        sys.exit(0)
