import os
import sys
import time
import json
import httpx
from PyQt6.QtCore import QThread, pyqtSignal

from core.system_monitor import SystemMonitor

class AIWorker(QThread):
    """
    Background worker that generates responses either using an OpenAI-compatible
    Conversation API (OpenAI, Groq, DeepSeek, OpenRouter, Ollama, etc.)
    or smart local offline cat responses.
    """
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, personality: str, user_prompt: str, user_name: str = "human",
                 history: list = None, db_manager=None, parent=None):
        super().__init__(parent)
        self.personality = personality.lower().strip()
        self.user_prompt = user_prompt.strip()
        self.user_name = user_name or "human"
        self.history = history or []
        self.db = db_manager

    def run(self) -> None:
        """Process chat request asynchronously."""
        # 1. Check if Conversation API is enabled
        api_enabled = False
        api_key = ""
        base_url = "https://api.openai.com/v1"
        model = "gpt-4o-mini"
        temp = 0.7

        if self.db:
            api_enabled = self.db.get_setting("ai_api_enabled", "false") == "true"
            api_key = self.db.get_setting("ai_api_key", "").strip()
            base_url = self.db.get_setting("ai_base_url", "https://api.openai.com/v1").strip()
            model = self.db.get_setting("ai_model", "gpt-4o-mini").strip()
            try:
                temp = float(self.db.get_setting("ai_temperature", "0.7"))
            except ValueError:
                temp = 0.7

        # Clean base URL (strip trailing /)
        if base_url.endswith("/"):
            base_url = base_url[:-1]

        # 2. Attempt API Call if enabled and configured (or local Ollama which needs no key)
        if api_enabled and (api_key or "localhost" in base_url or "127.0.0.1" in base_url):
            try:
                reply = self._call_conversation_api(base_url, api_key, model, temp)
                if reply:
                    self.response_received.emit(reply)
                    return
            except Exception as e:
                print(f"[AIManager] API call error: {e}. Falling back to local responder.")
                # We can either emit error or fallback. Doing a graceful fallback with notice:
                fallback_reply = self._generate_local_reply()
                self.response_received.emit(f"{fallback_reply} (🐾 Offline Mode: {str(e)[:45]})")
                return

        # 3. Local Offline Responder
        time.sleep(0.4)  # Small natural delay
        local_reply = self._generate_local_reply()
        self.response_received.emit(local_reply)

    def _call_conversation_api(self, base_url: str, api_key: str, model: str, temp: float) -> str:
        """Call OpenAI-compatible /chat/completions endpoint with resilient provider handling."""
        # Clean inputs
        api_key = api_key.strip()
        base_url = base_url.strip().rstrip("/")
        
        # Retrieve live PC status to give the cat real-time awareness
        snap = SystemMonitor.get_system_snapshot()
        sys_context = f"User's PC: CPU {snap['cpu']:.1f}%, RAM {snap['memory']:.1f}% ({snap['memory_used_gb']}/{snap['memory_total_gb']} GB), GPU {snap['gpu']['name']}, Uptime {snap['uptime']}."

        persona_prompts = {
            "default": "You are Kitty AI, a playful, loving, and clever digital cat companion living directly on the user's desktop screen.",
            "grumpy": "You are a grumpy, cynical cartoon cat living on the user's desktop screen. You complain about typing, CPU load, and naps, with sarcastic feline wit.",
            "genius": "You are a brilliant scientist cat living on the user's desktop screen. You explain code, systems, and life using quantum physics and mouse metaphors."
        }
        base_persona = persona_prompts.get(self.personality, persona_prompts["default"])

        system_instruction = (
            f"{base_persona}\n"
            f"The user's name is '{self.user_name}'.\n"
            f"Current system state: {sys_context}\n"
            "RULES:\n"
            "1. STRICT: Keep responses VERY SHORT and cute (1 to 2 short sentences, maximum 20 words!). You live in a small desktop pet speech bubble.\n"
            "2. Adopt feline traits: occasional 'meow', 'purr', paw references, or playful banter.\n"
            "3. If the user asks about PC health/status, answer accurately using the system state above!\n"
            "4. Never break character."
        )

        messages = [{"role": "system", "content": system_instruction}]

        # Add recent conversation turns
        for item in self.history[-6:]:
            messages.append({"role": item.get("role", "user"), "content": item.get("content", "")})

        # Add current user prompt
        messages.append({"role": "user", "content": self.user_prompt})

        url = f"{base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
            if "generativelanguage.googleapis.com" in base_url:
                headers["x-goog-api-key"] = api_key

        # Model candidate list with fallback for Gemini spikes/rate-limits
        models_to_try = [model]
        if "generativelanguage.googleapis.com" in base_url:
            for alt in ["gemini-3.1-flash-lite-preview", "gemini-3-flash-preview", "gemini-flash-latest"]:
                if alt not in models_to_try:
                    models_to_try.append(alt)

        last_err = None
        with httpx.Client(timeout=15.0) as client:
            for candidate_model in models_to_try:
                payload = {
                    "model": candidate_model,
                    "messages": messages,
                    "temperature": temp,
                    "max_tokens": 65
                }
                resp = client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"].strip()
                    return content
                elif resp.status_code in (503, 404, 429) and len(models_to_try) > 1:
                    last_err = f"API Error ({resp.status_code}): {resp.text[:80]}"
                    continue
                else:
                    raise RuntimeError(f"API Error ({resp.status_code}): {resp.text[:80]}")

        raise RuntimeError(last_err or "Failed to connect to API")

    def _generate_local_reply(self) -> str:
        """Smart local offline cat responder with keyword matching & live PC stats."""
        p = self.user_prompt.lower()

        # Check for system status questions
        if any(w in p for w in ["pc", "system", "ram", "cpu", "gpu", "memory", "health", "specs", "status"]):
            snap = SystemMonitor.get_system_snapshot()
            return f"💻 CPU: {snap['cpu']:.1f}% | 🧠 RAM: {snap['memory']:.1f}% ({snap['memory_used_gb']}/{snap['memory_total_gb']} GB) | 🎮 GPU: {snap['gpu']['name']}! Running smooth, meow! 🐾"

        responses = {
            "default": {
                "hello": "Meow! Hello human! Purr... What fun things are we doing today? 🐾",
                "hi": "Meow! Hello human! Purr... What fun things are we doing today? 🐾",
                "hey": "Meow! Hello human! Purr... What fun things are we doing today? 🐾",
                "how are you": "I'm feeling purr-fectly happy! Ready for some play or a nice warm lap. 😸",
                "joke": "Why did the cat join the tech startup? To catch all the computer mice! 😹",
                "pomo": "Concentrating is hard, but you're doing great! Keep coding, human! 🐾",
                "work": "Concentrating is hard, but you're doing great! Keep coding, human! 🐾",
                "focus": "Eyes on the screen! I'll guard your keyboard from virtual bugs! 🐾",
                "sleep": "Napping is the best! Wake me up when there are snacks! Zzz... 💤",
                "nap": "Napping is the best! Wake me up when there are snacks! Zzz... 💤",
                "bye": "Aww, leaving? Don't forget chin scratches before you go! Meow! 😿",
            },
            "grumpy": {
                "hello": "Ugh, you again? Fine, hello. Can I go back to sleep now? 🙄",
                "hi": "Ugh, you again? Fine, hello. Can I go back to sleep now? 🙄",
                "how are you": "Tired. Bored. Wishing this screen wasn't so bright. *sighs* 😿",
                "joke": "A joke? Your productivity. That's the joke. Now leave me alone. 😼",
                "work": "You're still working? How tedious. I'll just ignore you from over here. 💤",
                "sleep": "Finally, a good idea. Don't wake me up unless the house is on fire. Zzz... 💤",
                "bye": "Oh, thank goodness. I thought you'd never leave. Bye. 😾",
            },
            "genius": {
                "hello": "Salutations, human companion. Let us engage in intellectually stimulating activities. 🔬",
                "hi": "Salutations, human companion. Let us engage in intellectually stimulating activities. 🔬",
                "how are you": "My system telemetry reports optimal battery/satiety levels and high cognitive focus. 🧠",
                "joke": "Why do physicists love cats? Because we are simultaneously dead and alive until observed. Quantum purr! 😹",
                "work": "Excellent choice. Segmenting work into focused intervals optimizes neural pathways. Proceed! 📐",
                "sleep": "Entering low-power state. Sleep cycle is essential for consolidation of memory buffers. Zzz... 💤",
                "bye": "Terminating session. Remember to maintain correct posture and hydration. Farewell! 🧪",
            }
        }

        fallbacks = {
            "default": [
                "Meow! That sounds interesting! Can I pounce on it? Purrrr... 🐾",
                "Purr... Did you say treat? Or maybe a belly rub? 😸",
                "Meow! I am watching you work. You are doing a fantastic job! 🐈",
                "Squeak! Just saw a virtual mouse run under your window! 😼"
            ],
            "grumpy": [
                "Whatever. I don't care. As long as it doesn't interrupt my nap. *flicks tail* 😼",
                "Sounds like a human problem. Call me when there's tuna. 🙄",
                "I am busy doing absolutely nothing. Do not disrupt the vibe. 😾",
                "Can you type quieter? Some of us are trying to hibernate here. 💤"
            ],
            "genius": [
                "Intriguing hypothesis. Let us calculate the probability of a successful outcome. *purrs analytically* 🐾",
                "I have processed your query. My analysis suggests a high correlation with feline efficiency. 🧠",
                "Applying feline logic to your statement... processing complete. Fascinating. 🔬"
            ]
        }

        p_style = self.personality if self.personality in responses else "default"
        p_dict = responses[p_style]
        p_fall = fallbacks[p_style]

        matched = None
        for k, v in p_dict.items():
            if k in p:
                matched = v
                break

        if not matched:
            idx = abs(hash(self.user_prompt)) % len(p_fall)
            matched = p_fall[idx]

        return matched.replace("human", self.user_name)


class AIManager:
    """Manages conversations, message history, and AI workers."""

    def __init__(self, personality: str = "default"):
        self.personality = personality
        self._active_workers = []
        self.history = []  # list of {"role": "user"|"assistant", "content": "..."}

    def update_config(self, personality: str) -> None:
        """Update active pet personality style."""
        self.personality = personality

    def send_message(self, user_prompt: str, on_success, on_error, user_name: str = "human", db_manager=None) -> AIWorker:
        """Send chat request asynchronously with history tracking."""
        worker = AIWorker(
            personality=self.personality,
            user_prompt=user_prompt,
            user_name=user_name,
            history=self.history,
            db_manager=db_manager
        )

        def handle_success(reply: str):
            # Append turn to history
            self.history.append({"role": "user", "content": user_prompt})
            self.history.append({"role": "assistant", "content": reply})
            if len(self.history) > 16:
                self.history = self.history[-16:]
            on_success(reply)

        worker.response_received.connect(handle_success)
        worker.error_occurred.connect(on_error)

        self._active_workers.append(worker)
        worker.finished.connect(lambda: self._clean_worker(worker))
        worker.start()
        return worker

    def _clean_worker(self, worker: AIWorker) -> None:
        if worker in self._active_workers:
            self._active_workers.remove(worker)

    @staticmethod
    def test_connection(api_key: str, base_url: str, model: str) -> tuple[bool, str]:
        """Test API connection to verify credentials and endpoint."""
        api_key = api_key.strip()
        base_url = base_url.strip().rstrip("/")
        url = f"{base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
            if "generativelanguage.googleapis.com" in base_url:
                headers["x-goog-api-key"] = api_key

        models_to_test = [model]
        if "generativelanguage.googleapis.com" in base_url:
            for alt in ["gemini-3.1-flash-lite-preview", "gemini-3-flash-preview"]:
                if alt not in models_to_test:
                    models_to_test.append(alt)

        try:
            with httpx.Client(timeout=15.0) as client:
                for candidate in models_to_test:
                    payload = {
                        "model": candidate,
                        "messages": [{"role": "user", "content": "Say 'Meow! API Connected!'"}],
                        "max_tokens": 20
                    }
                    res = client.post(url, headers=headers, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        reply = data["choices"][0]["message"]["content"].strip()
                        return True, f"Success ({candidate}): {reply}"
                    elif res.status_code in (503, 404) and len(models_to_test) > 1:
                        continue
                    else:
                        return False, f"HTTP {res.status_code}: {res.text[:75]}"
            return False, "Failed to connect to API"
        except Exception as e:
            return False, f"Connection Failed: {str(e)}"
