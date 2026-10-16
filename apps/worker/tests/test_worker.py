"""Unit tests for background worker process."""

import asyncio
from unittest.mock import patch

import pytest
from apps.worker.src.worker import main, run_worker


@pytest.mark.asyncio
async def test_run_worker_cancellation() -> None:
    """Verify run_worker handles cancellation gracefully."""
    task = asyncio.create_task(run_worker())
    await asyncio.sleep(0.05)
    task.cancel()
    # run_worker catches CancelledError and terminates cleanly
    await task
    assert task.done()


def test_main_handles_interrupt() -> None:
    """Verify main terminates gracefully on KeyboardInterrupt."""
    with patch("apps.worker.src.worker.asyncio.run", side_effect=KeyboardInterrupt) as mock_run:
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
        if mock_run.call_args:
            coro = mock_run.call_args[0][0]
            coro.close()
