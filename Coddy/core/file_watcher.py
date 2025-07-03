import asyncio
import logging
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

class ProactiveEventHandler(FileSystemEventHandler):
    """
    An event handler that reacts to file modifications and will eventually
    trigger proactive suggestions.
    """
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop

    def on_modified(self, event: FileModifiedEvent):
        """
        Called when a file or directory is modified.
        """
        if event.is_directory:
            return

        # Run the async suggestion logic in the main event loop
        asyncio.run_coroutine_threadsafe(
            self.handle_file_modification(event.src_path),
            self.loop
        )

    async def handle_file_modification(self, path: str):
        """
        Asynchronously handle the file modification event.
        This is where proactive suggestions would be generated.
        """
        logging.info(f"File modified: {path}")
        # Placeholder for proactive suggestion logic
        logging.info(f"Analyzed {path}. [Proactive suggestion logic would run here]")


class FileWatcher:
    """
    Manages the file system observer and event handler.
    """
    def __init__(self, path: str, loop: asyncio.AbstractEventLoop):
        self.path = path
        self.loop = loop
        self.event_handler = ProactiveEventHandler(self.loop)
        self.observer = Observer()

    def start(self):
        """
        Starts the file watcher. It runs in its own thread and will
        block until interrupted.
        """
        self.observer.schedule(self.event_handler, self.path, recursive=True)
        self.observer.start()
        logging.info(f"Started watching directory: {self.path}")
        try:
            while self.observer.is_alive():
                self.observer.join(1)
        finally:
            if self.observer.is_alive():
                self.observer.stop()
                self.observer.join()
            logging.info("Stopped watching.")