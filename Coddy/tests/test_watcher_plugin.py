import unittest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from watchdog.events import FileModifiedEvent
from core.file_watcher import ProactiveEventHandler

class TestWatcherPlugin(unittest.TestCase):

    @patch('core.file_watcher.asyncio.run_coroutine_threadsafe')
    def test_proactive_event_handler_dispatches_async_task(self, mock_run_coroutine_threadsafe):
        """
        Tests that the event handler correctly dispatches a coroutine 
        to the event loop upon a file modification event.
        """
        mock_loop = MagicMock()
        handler = ProactiveEventHandler(loop=mock_loop)

        # Mock the async handler method to avoid actual execution
        handler.handle_file_modification = AsyncMock()

        # Use a mock event with a spec to better emulate the real object
        mock_event = MagicMock(spec=FileModifiedEvent, is_directory=False, src_path="/fake/path/to/file.py")
        handler.on_modified(mock_event)

        # Assert that the async task was submitted to the event loop
        mock_run_coroutine_threadsafe.assert_called_once()

        # Check that the mock was called to create the coroutine with the correct path
        handler.handle_file_modification.assert_called_once_with("/fake/path/to/file.py")

        # And check that the correct loop was passed to run_coroutine_threadsafe
        _coro, loop = mock_run_coroutine_threadsafe.call_args[0]
        self.assertIs(loop, mock_loop)

    @patch('core.file_watcher.logging')
    def test_handle_file_modification_logs_correctly(self, mock_logging):
        """
        Tests the async handle_file_modification method to ensure it logs correctly.
        """
        async def run_test():
            loop = asyncio.get_running_loop()
            handler = ProactiveEventHandler(loop=loop)
            
            test_path = "/fake/path/to/another_file.py"
            await handler.handle_file_modification(test_path)
            
            mock_logging.info.assert_any_call(f"File modified: {test_path}")
            mock_logging.info.assert_any_call(f"Analyzed {test_path}. [Proactive suggestion logic would run here]")

        asyncio.run(run_test())

    def test_proactive_event_handler_ignores_directories(self):
        """
        Tests that the event handler ignores events for directories.
        """
        mock_loop = MagicMock()
        handler = ProactiveEventHandler(loop=mock_loop)
        
        mock_event = MagicMock(spec=FileModifiedEvent, is_directory=True, src_path="/fake/path/to/directory/")
        handler.on_modified(mock_event)
        mock_loop.run_coroutine_threadsafe.assert_not_called()