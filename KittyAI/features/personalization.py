import random
from database.database import DatabaseManager

class PersonalizationManager:
    """Manages character traits, active skins, and personalized voice dialogue lines."""

    VOICE_LINES = {
        "idle": [
            "Purrr... standard CPU loads are comfortable! 😺",
            "Meow? Did you click me? 🐾",
            "Sleeping on the keyboard is my favorite chore. 💤",
            "Ready for some focus work? Let's start a Pomodoro!"
        ],
        "high_cpu": [
            "Meow! The processor is running hot! 🙀",
            "Overheating! Need to step away from the IDE... 🔥",
            "My paws are burning from this compilation load!"
        ],
        "pomodoro_work": [
            "Focus time, human! Keep coding! 🎯",
            "No distractions! Meow! 🐾",
            "Focusing... purr... 🧠"
        ],
        "pomodoro_break": [
            "Stretch your paws! Time for a break! 🌿",
            "Nap time! You did great. 💤",
            "Grab a water, meow! 🐾"
        ]
    }

    SKINS = ["black", "orange", "siamese", "mackerel", "calico"]

    PERSONALITIES = {
        "default": "You are Kitty AI, a playful, helpful, and charming digital cat companion living on the user's desktop. Keep your responses short, funny, cat-themed, and friendly (use occasional 'meows' or 'purrs').",
        "grumpy": "You are a grumpy, sarcastic cartoon desktop cat. You complain about user's CPU load, ask them to stop typing, but still helpfully answer questions in brief, annoyed, feline-themed responses.",
        "genius": "You are a highly intellectual scientist cat. You explain complex code concepts using physics and mouse-hunting metaphors. Keep responses short, academic, and cat-themed."
    }

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_current_skin(self) -> str:
        """Get the active skin name."""
        return self.db.get_setting("pet_skin", "black") or "black"

    def set_current_skin(self, skin: str) -> None:
        """Update the active skin name."""
        if skin in self.SKINS:
            self.db.set_setting("pet_skin", skin)

    def get_personality_prompt(self) -> str:
        """Get system prompt based on active personality configuration."""
        style = self.db.get_setting("personality_style", "default")
        return self.PERSONALITIES.get(style, self.PERSONALITIES["default"])

    def set_personality_style(self, style: str) -> None:
        """Set the active chatbot personality style."""
        if style in self.PERSONALITIES:
            self.db.set_setting("personality_style", style)

    def get_random_voice_line(self, category: str) -> str:
        """Get a random dialog line for a specific event category."""
        lines = self.VOICE_LINES.get(category, self.VOICE_LINES["idle"])
        return random.choice(lines)
