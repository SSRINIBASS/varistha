"""Background worker process for asynchronous agent run dispatch."""

import asyncio
import contextlib
import logging
import signal
import sys

logger = logging.getLogger("varistha.worker")


async def run_worker() -> None:
    """Execute the main worker event loop."""
    logger.info("Varistha background worker initialized and ready.")
    stop_event = asyncio.Event()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError, RuntimeError):
            # Non-Unix environments (Windows) do not support add_signal_handler
            loop.add_signal_handler(sig, stop_event.set)

    try:
        while not stop_event.is_set():
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info("Worker received cancellation signal.")
    finally:
        logger.info("Worker shutting down gracefully.")


def main() -> None:
    """Run entry point for worker process."""
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt)
    try:
        asyncio.run(run_worker())
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)


if __name__ == "__main__":
    main()
