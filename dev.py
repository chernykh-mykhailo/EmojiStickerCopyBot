import sys
import time
import subprocess
import os
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class RestartHandler(FileSystemEventHandler):
    def __init__(self, command):
        self.command = command
        self.process = None
        self.last_restart = 0
        self.restart()

    def restart(self):
        # Debounce: don't restart more than once per second
        now = time.time()
        if now - self.last_restart < 1:
            return
        self.last_restart = now

        if self.process:
            print("🔄 Restarting bot...")
            # On Windows, terminate() might not kill the child process if shell=True
            # We use taskkill to kill the whole process tree
            subprocess.run(f"taskkill /F /T /PID {self.process.pid}", shell=True, capture_output=True)
        
        self.process = subprocess.Popen(self.command, shell=True)

    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(".py") or event.src_path.endswith(".ftl") or event.src_path.endswith(".env"):
            self.restart()

if __name__ == "__main__":
    # Detect venv python
    venv_python = os.path.join(".venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        venv_python = "py" # Fallback to py launcher
        
    cmd = f"{venv_python} src/bot.py"
    
    event_handler = RestartHandler(cmd)
    observer = Observer()
    observer.schedule(event_handler, path="src", recursive=True)
    observer.start()
    
    print(f"👀 Watching for changes in 'src' and running: {cmd}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping watcher...")
        observer.stop()
        if event_handler.process:
            # Force kill the process tree immediately
            subprocess.run(f"taskkill /F /T /PID {event_handler.process.pid}", shell=True, capture_output=True)
    observer.join()
    sys.exit(0)
