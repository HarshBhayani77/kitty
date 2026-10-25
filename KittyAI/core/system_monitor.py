import os
import sys
import time
import subprocess
import psutil
from PyQt6.QtCore import QThread, pyqtSignal

class SystemMonitor(QThread):
    """Background thread that monitors CPU, memory, GPU, disk, battery, and system status."""
    
    # Signal transmitting comprehensive system metrics as a dict
    metrics_updated = pyqtSignal(dict)

    # Static cached GPU info so we avoid running subprocess commands continuously
    _cached_gpu_info = None
    _last_gpu_check = 0.0

    def __init__(self, interval_seconds: int = 3, parent=None):
        super().__init__(parent)
        self.interval_seconds = interval_seconds
        self.running = True

    @classmethod
    def get_gpu_info(cls) -> dict:
        """Query GPU information with caching."""
        now = time.time()
        if cls._cached_gpu_info is not None and (now - cls._last_gpu_check < 30.0):
            return cls._cached_gpu_info

        gpu_info = {"name": "Integrated Graphics", "driver": "", "util": "Active", "temp": "", "mem_used": "", "mem_total": ""}

        # 1. Try nvidia-smi for dedicated NVIDIA GPUs
        try:
            res = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu,temperature.gpu', '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=1.5
            )
            if res.returncode == 0 and res.stdout.strip():
                parts = [p.strip() for p in res.stdout.strip().split(',')]
                gpu_info["name"] = parts[0]
                if len(parts) > 1: gpu_info["driver"] = parts[1]
                if len(parts) > 2: gpu_info["mem_total"] = f"{float(parts[2])/1024:.1f} GB"
                if len(parts) > 3: gpu_info["mem_used"] = f"{float(parts[3])/1024:.1f} GB"
                if len(parts) > 4: gpu_info["util"] = f"{parts[4]}%"
                if len(parts) > 5: gpu_info["temp"] = f"{parts[5]}°C"
                cls._cached_gpu_info = gpu_info
                cls._last_gpu_check = now
                return gpu_info
        except Exception:
            pass

        # 2. Try Windows PowerShell for VideoController
        if sys.platform == "win32":
            try:
                res = subprocess.run(
                    ['powershell', '-NoProfile', '-Command', 'Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name'],
                    capture_output=True, text=True, timeout=2.0
                )
                if res.returncode == 0 and res.stdout.strip():
                    names = [line.strip() for line in res.stdout.strip().split('\n') if line.strip()]
                    if names:
                        gpu_info["name"] = names[0]
                        gpu_info["util"] = "Active"
                        cls._cached_gpu_info = gpu_info
                        cls._last_gpu_check = now
                        return gpu_info
            except Exception:
                pass

        cls._cached_gpu_info = gpu_info
        cls._last_gpu_check = now
        return gpu_info

    @classmethod
    def get_system_snapshot(cls) -> dict:
        """Synchronously collect a comprehensive snapshot of all system statistics."""
        # 1. CPU
        cpu_overall = psutil.cpu_percent(interval=None)
        cpu_phys = psutil.cpu_count(logical=False) or 1
        cpu_log = psutil.cpu_count(logical=True) or 1
        freq = psutil.cpu_freq()
        cpu_ghz = f"{freq.current / 1000.0:.2f} GHz" if freq and freq.current else "N/A"
        
        # 2. RAM
        vmem = psutil.virtual_memory()
        mem_used_gb = vmem.used / (1024 ** 3)
        mem_total_gb = vmem.total / (1024 ** 3)
        mem_avail_gb = vmem.available / (1024 ** 3)
        mem_percent = vmem.percent

        # 3. Disks
        disks = []
        try:
            for part in psutil.disk_partitions(all=False):
                if not part.mountpoint:
                    continue
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    disks.append({
                        "device": part.device,
                        "mount": part.mountpoint,
                        "total_gb": round(usage.total / (1024 ** 3), 1),
                        "used_gb": round(usage.used / (1024 ** 3), 1),
                        "free_gb": round(usage.free / (1024 ** 3), 1),
                        "percent": usage.percent
                    })
                except (PermissionError, OSError):
                    continue
        except Exception:
            pass

        # Fallback disk if empty
        if not disks:
            try:
                root_path = os.path.splitdrive(os.path.abspath('.'))[0] + '\\' if sys.platform == 'win32' else '/'
                u = psutil.disk_usage(root_path)
                disks.append({
                    "device": root_path,
                    "mount": root_path,
                    "total_gb": round(u.total / (1024 ** 3), 1),
                    "used_gb": round(u.used / (1024 ** 3), 1),
                    "free_gb": round(u.free / (1024 ** 3), 1),
                    "percent": u.percent
                })
            except Exception:
                pass

        # 4. GPU
        gpu = cls.get_gpu_info()

        # 5. Battery
        battery_data = {"percent": None, "plugged": None, "status": "No Battery"}
        try:
            batt = psutil.sensors_battery()
            if batt:
                battery_data["percent"] = int(batt.percent)
                battery_data["plugged"] = bool(batt.power_plugged)
                if batt.power_plugged:
                    battery_data["status"] = "Plugged in (AC)"
                else:
                    battery_data["status"] = f"{battery_data['percent']}% On Battery"
        except Exception:
            pass

        # 6. Uptime and processes
        try:
            uptime_secs = int(time.time() - psutil.boot_time())
            hrs = uptime_secs // 3600
            mins = (uptime_secs % 3600) // 60
            uptime_str = f"{hrs}h {mins}m"
        except Exception:
            uptime_str = "Unknown"

        proc_count = len(psutil.pids())

        return {
            "cpu": cpu_overall,
            "cpu_cores_phys": cpu_phys,
            "cpu_cores_log": cpu_log,
            "cpu_ghz": cpu_ghz,
            "memory": mem_percent,
            "memory_percent": mem_percent,
            "memory_used_gb": round(mem_used_gb, 1),
            "memory_total_gb": round(mem_total_gb, 1),
            "memory_avail_gb": round(mem_avail_gb, 1),
            "disks": disks,
            "disk": disks[0]["percent"] if disks else 0.0,
            "gpu": gpu,
            "battery": battery_data,
            "process_count": proc_count,
            "uptime": uptime_str
        }

    def run(self) -> None:
        """Indefinite loop that collects and reports system stats."""
        # Initial priming call so cpu_percent returns an accurate delta
        psutil.cpu_percent(interval=None)

        while self.running:
            try:
                metrics = self.get_system_snapshot()
                self.metrics_updated.emit(metrics)
            except Exception as e:
                print(f"Error gathering system metrics: {e}")
                
            # Sleep in small slices to remain responsive to stop signals
            for _ in range(int(self.interval_seconds * 10)):
                if not self.running:
                    break
                time.sleep(0.1)

    def stop(self) -> None:
        """Gracefully stop the background monitoring loop."""
        self.running = False
        self.wait()
