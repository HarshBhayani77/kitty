import os
import sys

try:
    import winreg
except ImportError:
    winreg = None

class StartupManager:
    """Handles adding and removing the application from the startup registry list cross-platform."""

    REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"

    @staticmethod
    def enable_autostart(app_name: str) -> bool:
        """Add application to user run startup list if supported."""
        if sys.platform != 'win32' or winreg is None:
            print("Autostart configuration is only supported on Windows.")
            return False
        try:
            # Get path to the currently running script/executable
            if getattr(sys, 'frozen', False):
                app_path = sys.executable
            else:
                app_path = f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'
            
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, 
                StartupManager.REG_PATH, 
                0, 
                winreg.KEY_WRITE
            )
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"Failed to enable autostart: {e}")
            return False

    @staticmethod
    def disable_autostart(app_name: str) -> bool:
        """Remove application from user run startup list if supported."""
        if sys.platform != 'win32' or winreg is None:
            return False
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, 
                StartupManager.REG_PATH, 
                0, 
                winreg.KEY_WRITE
            )
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                # Key already removed
                pass
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"Failed to disable autostart: {e}")
            return False

    @staticmethod
    def is_autostart_enabled(app_name: str) -> bool:
        """Check if application is registered to autostart."""
        if sys.platform != 'win32' or winreg is None:
            return False
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, 
                StartupManager.REG_PATH, 
                0, 
                winreg.KEY_READ
            )
            value, _ = winreg.QueryValueEx(key, app_name)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            print(f"Failed to query autostart registry: {e}")
            return False
