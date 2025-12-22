import asyncio
import logging

logger = logging.getLogger(__name__)

class EventBus:
    def __init__(self):
        self._subscribers = {}
        self._queue = asyncio.Queue()

    async def publish(self, event_type, data):
        logger.debug(f"Publishing event: {event_type}")
        await self._queue.put((event_type, data))

    def subscribe(self, event_type, callback):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    async def process_events(self):
        while True:
            event_type, data = await self._queue.get()
            if event_type in self._subscribers:
                for callback in self._subscribers[event_type]:
                    # Run each callback in its own task so they don't block the bus
                    asyncio.create_task(self._run_callback(callback, event_type, data))
            self._queue.task_done()

    async def _run_callback(self, callback, event_type, data):
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(data)
            else:
                callback(data)
        except Exception as e:
            logger.error(f"Error processing event {event_type} in {callback.__name__}: {e}", exc_info=True)
