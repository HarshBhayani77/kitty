import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QCheckBox, QSlider, QComboBox, QPushButton, QTabWidget, 
    QListWidget, QDateTimeEdit, QFormLayout, QGroupBox, QColorDialog
)
from PyQt6.QtCore import Qt, QDateTime, pyqtSignal
from PyQt6.QtGui import QColor

from database.database import DatabaseManager
from core.startup_manager import StartupManager
from core.ai_manager import AIManager

class SettingsWindow(QWidget):
    """The central user interface configuration window for customization, sizing, skins, and AI API."""
    
    settings_saved = pyqtSignal()  # Emitted when settings are saved and need reload

    PROVIDER_PRESETS = {
        "Google Gemini": {
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
            "model": "gemini-3.1-flash-lite-preview",
            "needs_key": True
        },
        "OpenAI": {
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o-mini",
            "needs_key": True
        },
        "Groq": {
            "base_url": "https://api.groq.com/openai/v1",
            "model": "llama-3.3-70b-versatile",
            "needs_key": True
        },
        "DeepSeek": {
            "base_url": "https://api.deepseek.com/v1",
            "model": "deepseek-chat",
            "needs_key": True
        },
        "OpenRouter": {
            "base_url": "https://openrouter.ai/api/v1",
            "model": "meta-llama/llama-3.3-70b-instruct",
            "needs_key": True
        },
        "Ollama (Local)": {
            "base_url": "http://localhost:11434/v1",
            "model": "llama3.2",
            "needs_key": False
        },
        "Custom": {
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o-mini",
            "needs_key": True
        }
    }

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        
        self.setWindowTitle("Kitty AI Settings")
        self.setFixedSize(500, 640)
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a2e;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QTabWidget::pane {
                border: 1px solid #e74c3c;
                background: #1a1a2e;
            }
            QTabBar::tab {
                background: #0d0d1a;
                border: 1px solid #333;
                padding: 8px 14px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #1a1a2e;
                border-color: #e74c3c;
                color: #ff7675;
            }
            QPushButton {
                background-color: #e74c3c;
                border: none;
                border-radius: 4px;
                padding: 6px 14px;
                font-weight: bold;
                color: #fff;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QLineEdit, QComboBox, QDateTimeEdit {
                background-color: #0d0d1a;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 6px;
                color: #fff;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #e74c3c;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid rgba(231, 76, 60, 120);
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: #ff7675;
            }
        """)

        # Main Layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(12, 12, 12, 12)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_appearance_tab(), "Appearance & Size")
        self.tabs.addTab(self.create_ai_tab(), "AI & Chat API")
        self.tabs.addTab(self.create_general_tab(), "General")
        self.tabs.addTab(self.create_reminders_tab(), "Reminders")
        main_layout.addWidget(self.tabs)
        
        # Bottom Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.save_btn = QPushButton("Save & Apply")
        self.save_btn.clicked.connect(self.save_all_settings)
        btn_layout.addWidget(self.save_btn)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.setStyleSheet("background-color: #555;")
        self.close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

        # Load values from DB
        self.load_settings()

    def create_appearance_tab(self) -> QWidget:
        """Tab for Pet Size scaling, Preset Skins, and Custom Fur Markings."""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # 1. Pet Size Scaling Section
        size_group = QGroupBox("🐾 Kitty Size Customization")
        size_layout = QVBoxLayout()

        slider_row = QHBoxLayout()
        self.size_label = QLabel("Scale: 65% (Small)")
        self.size_label.setStyleSheet("font-weight: bold; color: #74b9ff;")
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(30, 150)
        self.size_slider.setValue(65)
        self.size_slider.valueChanged.connect(self._on_scale_slider_changed)
        slider_row.addWidget(self.size_slider)
        slider_row.addWidget(self.size_label)
        size_layout.addLayout(slider_row)

        # Quick preset size buttons
        presets_row = QHBoxLayout()
        presets_row.setSpacing(6)
        presets = [("Mini (40%)", 40), ("Tiny (50%)", 50), ("Small (65%)", 65), ("Normal (80%)", 80), ("Large (100%)", 100)]
        for name, val in presets:
            btn = QPushButton(name)
            btn.setStyleSheet("background-color: #2d3436; font-size: 10px; padding: 4px 6px;")
            btn.clicked.connect(lambda checked, v=val: self.size_slider.setValue(v))
            presets_row.addWidget(btn)
        size_layout.addLayout(presets_row)
        size_group.setLayout(size_layout)
        layout.addWidget(size_group)

        # 2. Preset Skin Selector
        skin_group = QGroupBox("🎨 Pet Skin Presets")
        skin_layout = QFormLayout()

        self.skin_combo = QComboBox()
        self.skin_combo.addItems(["black", "orange", "siamese", "mackerel", "calico"])
        self.skin_combo.currentTextChanged.connect(self._on_skin_changed)
        skin_layout.addRow("Select Skin:", self.skin_combo)

        self.skin_desc = QLabel("Black: Sleek dark coat with glowing amber eyes.")
        self.skin_desc.setStyleSheet("font-size: 11px; color: #b2bec3; font-style: italic;")
        skin_layout.addRow("", self.skin_desc)
        skin_group.setLayout(skin_layout)
        layout.addWidget(skin_group)

        # 3. Custom Fur & Markings
        self.custom_fur_group = QGroupBox("✨ Custom Fur & Markings")
        self.custom_fur_group.setCheckable(True)
        self.custom_fur_group.setChecked(False)
        self.custom_fur_group.toggled.connect(self._on_custom_fur_toggled)

        fur_layout = QFormLayout()

        # Body Color with Picker
        self.body_color_input, self.body_color_btn = self._create_color_row("#111111")
        fur_layout.addRow("Body Color:", self._wrap_color_row(self.body_color_input, self.body_color_btn))

        # Belly Color with Picker
        self.belly_color_input, self.belly_color_btn = self._create_color_row("#222222")
        fur_layout.addRow("Belly / Sheen:", self._wrap_color_row(self.belly_color_input, self.belly_color_btn))

        # Eye Color with Picker
        self.eye_color_input, self.eye_color_btn = self._create_color_row("#ffeb3b")
        fur_layout.addRow("Eye Color:", self._wrap_color_row(self.eye_color_input, self.eye_color_btn))

        # Marking Type
        self.marking_type_combo = QComboBox()
        self.marking_type_combo.addItems(["none", "stripes", "spots", "socks"])
        fur_layout.addRow("Marking Type:", self.marking_type_combo)

        # Marking Color with Picker
        self.marking_color_input, self.marking_color_btn = self._create_color_row("#444444")
        fur_layout.addRow("Marking Color:", self._wrap_color_row(self.marking_color_input, self.marking_color_btn))

        self.custom_fur_group.setLayout(fur_layout)
        layout.addWidget(self.custom_fur_group)

        layout.addStretch()
        tab.setLayout(layout)
        return tab

    def _create_color_row(self, initial_hex: str):
        """Helper to create a text field and color preview button."""
        line_edit = QLineEdit(initial_hex)
        line_edit.setFixedWidth(90)
        btn = QPushButton()
        btn.setFixedSize(32, 28)
        self._update_color_btn(btn, initial_hex)
        btn.clicked.connect(lambda: self._pick_color(line_edit, btn))
        line_edit.textChanged.connect(lambda txt: self._update_color_btn(btn, txt))
        return line_edit, btn

    def _wrap_color_row(self, line_edit, btn):
        w = QWidget()
        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(6)
        h.addWidget(btn)
        h.addWidget(line_edit)
        h.addStretch()
        w.setLayout(h)
        return w

    def _update_color_btn(self, btn: QPushButton, hex_str: str):
        if QColor.isValidColor(hex_str.strip()):
            btn.setStyleSheet(f"background-color: {hex_str.strip()}; border: 1px solid #fff; border-radius: 4px;")

    def _pick_color(self, line_edit: QLineEdit, btn: QPushButton):
        curr = line_edit.text().strip()
        initial = QColor(curr) if QColor.isValidColor(curr) else QColor("#111111")
        col = QColorDialog.getColor(initial, self, "Pick Fur/Eye Color")
        if col.isValid():
            hex_val = col.name()
            line_edit.setText(hex_val)
            self._update_color_btn(btn, hex_val)

    def _on_scale_slider_changed(self, val: int):
        self.size_label.setText(f"Scale: {val}%")

    def _on_skin_changed(self, skin: str):
        descs = {
            "black": "Black: Sleek dark coat with glowing amber eyes.",
            "orange": "Orange Tabby: Warm ginger coat with classic tabby stripes & green eyes.",
            "siamese": "Siamese: Cream coat with dark chocolate mask, ears, paws & icy blue eyes.",
            "mackerel": "Mackerel Tabby: Silver-gray coat with fine tiger stripes & bright green eyes.",
            "calico": "Calico: Patchwork white, ginger, and black with warm golden eyes."
        }
        self.skin_desc.setText(descs.get(skin, ""))

    def _on_custom_fur_toggled(self, checked: bool):
        if checked:
            self.skin_desc.setText("Custom Fur enabled: Overrides preset skin colors.")
        else:
            self._on_skin_changed(self.skin_combo.currentText())

    def create_ai_tab(self) -> QWidget:
        """Tab for Cloud/Local LLM Conversation API configuration."""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Enable API Toggle
        self.ai_api_cb = QCheckBox("Enable Cloud / Local LLM for Meow Chat")
        self.ai_api_cb.setStyleSheet("font-weight: bold; font-size: 13px; color: #ff7675;")
        layout.addWidget(self.ai_api_cb)

        desc = QLabel("When enabled, Kitty AI uses real AI completions for chat. If disabled or offline, Kitty uses smart local cat chatter.")
        desc.setStyleSheet("font-size: 11px; color: #b2bec3;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        api_group = QGroupBox("API Connection Configuration")
        form = QFormLayout()

        # Provider Selector
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(list(self.PROVIDER_PRESETS.keys()))
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        form.addRow("Provider:", self.provider_combo)

        # Base URL
        self.base_url_input = QLineEdit("https://api.openai.com/v1")
        form.addRow("API Base URL:", self.base_url_input)

        # Model Name
        self.model_input = QLineEdit("gpt-4o-mini")
        form.addRow("Model Name:", self.model_input)

        # API Key with visibility toggle
        key_layout = QHBoxLayout()
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("sk-... (leave blank for local Ollama)")
        key_layout.addWidget(self.api_key_input)

        self.show_key_btn = QPushButton("👁")
        self.show_key_btn.setFixedWidth(36)
        self.show_key_btn.setStyleSheet("background-color: #2d3436; padding: 4px;")
        self.show_key_btn.clicked.connect(self._toggle_key_visibility)
        key_layout.addWidget(self.show_key_btn)

        form.addRow("API Key:", key_layout)

        # Temperature
        temp_row = QHBoxLayout()
        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setRange(0, 15)  # 0.0 to 1.5
        self.temp_slider.setValue(7)
        self.temp_label = QLabel("0.7 (Creative)")
        self.temp_label.setFixedWidth(90)
        self.temp_slider.valueChanged.connect(lambda v: self.temp_label.setText(f"{v/10.0:.1f}"))
        temp_row.addWidget(self.temp_slider)
        temp_row.addWidget(self.temp_label)
        form.addRow("Temperature:", temp_row)

        api_group.setLayout(form)
        layout.addWidget(api_group)

        # Test Connection button & status
        test_row = QHBoxLayout()
        self.test_btn = QPushButton("🔌 Test API Connection")
        self.test_btn.setStyleSheet("background-color: #0984e3; padding: 8px 14px;")
        self.test_btn.clicked.connect(self.test_api_connection)
        test_row.addWidget(self.test_btn)

        self.test_status_label = QLabel("")
        self.test_status_label.setStyleSheet("font-size: 11px;")
        test_row.addWidget(self.test_status_label)
        test_row.addStretch()
        layout.addLayout(test_row)

        layout.addStretch()
        tab.setLayout(layout)
        return tab

    def _toggle_key_visibility(self):
        if self.api_key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_key_btn.setText("🔒")
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_key_btn.setText("👁")

    def _on_provider_changed(self, provider: str):
        preset = self.PROVIDER_PRESETS.get(provider, self.PROVIDER_PRESETS["OpenAI"])
        self.base_url_input.setText(preset["base_url"])
        self.model_input.setText(preset["model"])
        if not preset["needs_key"]:
            self.api_key_input.setPlaceholderText("No API key required for local Ollama")
        else:
            self.api_key_input.setPlaceholderText("sk-...")

    def test_api_connection(self):
        key = self.api_key_input.text().strip()
        url = self.base_url_input.text().strip()
        model = self.model_input.text().strip()
        self.test_status_label.setText("Testing connection...")
        self.test_status_label.setStyleSheet("color: #74b9ff;")

        success, msg = AIManager.test_connection(key, url, model)
        if success:
            self.test_status_label.setText(f"✅ {msg}")
            self.test_status_label.setStyleSheet("color: #2ecc71; font-weight: bold;")
        else:
            self.test_status_label.setText(f"❌ {msg[:55]}")
            self.test_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")

    def create_general_tab(self) -> QWidget:
        """Create tab for user profile, sound, and autostart."""
        tab = QWidget()
        layout = QFormLayout()
        layout.setSpacing(12)
        
        self.user_name_input = QLineEdit()
        self.user_name_input.setPlaceholderText("Enter your name")
        layout.addRow("Your Name:", self.user_name_input)
        
        self.autostart_cb = QCheckBox("Start Kitty AI on Startup")
        if sys.platform != "win32":
            self.autostart_cb.setEnabled(False)
        layout.addRow("", self.autostart_cb)
        
        self.sound_cb = QCheckBox("Enable Sound Effects")
        layout.addRow("", self.sound_cb)
        
        vol_row = QHBoxLayout()
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.vol_lbl = QLabel("80%")
        self.vol_lbl.setFixedWidth(40)
        self.volume_slider.valueChanged.connect(lambda v: self.vol_lbl.setText(f"{v}%"))
        vol_row.addWidget(self.volume_slider)
        vol_row.addWidget(self.vol_lbl)
        layout.addRow("Volume:", vol_row)

        self.personality_combo = QComboBox()
        self.personality_combo.addItems(["default", "grumpy", "genius"])
        layout.addRow("AI Personality:", self.personality_combo)

        # Stretch interval
        self.stretch_interval_combo = QComboBox()
        self.stretch_interval_combo.addItems(["15", "30", "45", "60", "0 (Disabled)"])
        layout.addRow("Stretch Reminder (mins):", self.stretch_interval_combo)

        tab.setLayout(layout)
        return tab

    def create_reminders_tab(self) -> QWidget:
        """Create tab to add and view reminders."""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Add reminder panel
        add_layout = QHBoxLayout()
        self.reminder_text = QLineEdit()
        self.reminder_text.setPlaceholderText("Reminder task description")
        add_layout.addWidget(self.reminder_text)

        self.reminder_time = QDateTimeEdit(QDateTime.currentDateTime().addSecs(3600))
        self.reminder_time.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        add_layout.addWidget(self.reminder_time)

        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_reminder_item)
        add_layout.addWidget(add_btn)
        
        layout.addLayout(add_layout)

        # Reminder display list
        self.reminder_list = QListWidget()
        layout.addWidget(self.reminder_list)
        
        del_btn = QPushButton("Delete Selected Reminder")
        del_btn.setStyleSheet("background-color: #c0392b;")
        del_btn.clicked.connect(self.delete_selected_reminder)
        layout.addWidget(del_btn)

        tab.setLayout(layout)
        return tab

    def load_settings(self) -> None:
        """Fetch all setting keys from SQLite and bind to widgets."""
        # Autostart
        is_autostart = StartupManager.is_autostart_enabled("KittyAI")
        self.autostart_cb.setChecked(is_autostart)
        
        # Sound & Volume
        sound_val = self.db.get_setting("sound_enabled", "true") == "true"
        self.sound_cb.setChecked(sound_val)
        
        volume_val = int(self.db.get_setting("volume", "80"))
        self.volume_slider.setValue(volume_val)
        self.vol_lbl.setText(f"{volume_val}%")

        # Scale
        scale_val = int(self.db.get_setting("pet_scale", "100"))
        self.size_slider.setValue(scale_val)
        self.size_label.setText(f"Scale: {scale_val}%")
        
        # Skin & Personality
        skin_val = self.db.get_setting("pet_skin", "black")
        self.skin_combo.setCurrentText(skin_val)
        self._on_skin_changed(skin_val)
        
        personality_val = self.db.get_setting("personality_style", "default")
        self.personality_combo.setCurrentText(personality_val)

        stretch_val = self.db.get_setting("stretch_interval", "30")
        self.stretch_interval_combo.setCurrentText(stretch_val)
        
        # Name
        user_name = self.db.get_setting("user_name", "human")
        self.user_name_input.setText(user_name)
        
        # Custom Fur
        custom_fur = self.db.get_setting("custom_fur_enabled", "false") == "true"
        self.custom_fur_group.setChecked(custom_fur)
        
        self.body_color_input.setText(self.db.get_setting("body_color", "#111111"))
        self.belly_color_input.setText(self.db.get_setting("belly_color", "#222222"))
        self.eye_color_input.setText(self.db.get_setting("eye_color", "#ffeb3b"))
        self.marking_type_combo.setCurrentText(self.db.get_setting("pattern_type", "none"))
        self.marking_color_input.setText(self.db.get_setting("pattern_color", "#444444"))

        # AI API Configuration
        ai_enabled = self.db.get_setting("ai_api_enabled", "false") == "true"
        self.ai_api_cb.setChecked(ai_enabled)

        provider = self.db.get_setting("ai_provider", "OpenAI")
        self.provider_combo.setCurrentText(provider)

        self.base_url_input.setText(self.db.get_setting("ai_base_url", "https://api.openai.com/v1"))
        self.model_input.setText(self.db.get_setting("ai_model", "gpt-4o-mini"))
        self.api_key_input.setText(self.db.get_setting("ai_api_key", ""))

        temp_float = float(self.db.get_setting("ai_temperature", "0.7"))
        self.temp_slider.setValue(int(temp_float * 10))
        self.temp_label.setText(f"{temp_float:.1f}")

        # Reload reminders list
        self.reload_reminders_view()

    def reload_reminders_view(self) -> None:
        self.reminder_list.clear()
        reminders = self.db.get_all_reminders()
        for reminder in reminders:
            status = "Completed" if reminder["completed"] else "Active"
            text = f"ID:{reminder['id']} | {reminder['title']} | Due: {reminder['due_time']} [{status}]"
            self.reminder_list.addItem(text)

    def add_reminder_item(self) -> None:
        title = self.reminder_text.text().strip()
        if not title:
            return
        due_str = self.reminder_time.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        self.db.add_reminder(title, due_str)
        self.reminder_text.clear()
        self.reload_reminders_view()

    def delete_selected_reminder(self) -> None:
        current_item = self.reminder_list.currentItem()
        if not current_item:
            return
        text = current_item.text()
        try:
            reminder_id = int(text.split("|")[0].replace("ID:", "").strip())
            self.db.delete_reminder(reminder_id)
            self.reload_reminders_view()
        except Exception as e:
            print(f"Error deleting reminder: {e}")

    def save_all_settings(self) -> None:
        """Save settings values to SQLite database and write Registry changes if needed."""
        # 1. Manage autostart registry key
        autostart_requested = self.autostart_cb.isChecked()
        if autostart_requested:
            StartupManager.enable_autostart("KittyAI")
        else:
            StartupManager.disable_autostart("KittyAI")
            
        # 2. General settings
        self.db.set_setting("sound_enabled", "true" if self.sound_cb.isChecked() else "false")
        self.db.set_setting("volume", str(self.volume_slider.value()))
        self.db.set_setting("pet_scale", str(self.size_slider.value()))
        self.db.set_setting("pet_skin", self.skin_combo.currentText())
        self.db.set_setting("personality_style", self.personality_combo.currentText())
        self.db.set_setting("user_name", self.user_name_input.text().strip() or "human")
        self.db.set_setting("stretch_interval", self.stretch_interval_combo.currentText().split()[0])
        
        # 3. Custom Fur & Markings
        self.db.set_setting("custom_fur_enabled", "true" if self.custom_fur_group.isChecked() else "false")
        self.db.set_setting("body_color", self.body_color_input.text().strip())
        self.db.set_setting("belly_color", self.belly_color_input.text().strip())
        self.db.set_setting("eye_color", self.eye_color_input.text().strip())
        self.db.set_setting("pattern_type", self.marking_type_combo.currentText())
        self.db.set_setting("pattern_color", self.marking_color_input.text().strip())

        # 4. AI API settings
        self.db.set_setting("ai_api_enabled", "true" if self.ai_api_cb.isChecked() else "false")
        self.db.set_setting("ai_provider", self.provider_combo.currentText())
        self.db.set_setting("ai_base_url", self.base_url_input.text().strip())
        self.db.set_setting("ai_model", self.model_input.text().strip())
        self.db.set_setting("ai_api_key", self.api_key_input.text().strip())
        self.db.set_setting("ai_temperature", f"{self.temp_slider.value() / 10.0:.1f}")
        
        self.settings_saved.emit()
        self.close()
