import asyncio
import logging
from collections import OrderedDict
from typing import Dict, Union, Any

from applebot.exceptions import EventNotFoundError

log = logging.getLogger(__name__)


class EventManager(object):
    def __init__(self):
        self._events = {}  # type: Dict[str, Event]
        self._event_type = Event

    def __contains__(self, event):
        return str(event) in self._events

    def __getitem__(self, key) -> 'Event':
        return self.get(key)

    def __iter__(self) -> 'Event':
        for event in self._events.values():
            yield event

    def __len__(self):
        return len(self._events)

    def get(self, event, default=None) -> 'Event':
        """Get an event from the manager."""
        return self._events.get(str(event), default)

    def add(self, event, handler=None, call_limit=None) -> Union['Event', 'EventHandler']:
        """Add a new or existing event or handler to the event manager."""
        if handler is not None:
            return self.add_handler(event, handler, call_limit)
        return self.add_event(event)

    async def emit(self, event, *args, **kwargs):
        """Emit an event and call its registered handlers."""
        await self.get(event).emit(*args, **kwargs)

    def add_event(self, event) -> 'Event':
        """Add a new or existing event to the event manager."""
        if not isinstance(event, self._event_type) and not isinstance(event, str):
            raise TypeError('Parameter \'event\' must be of type Event or str')
        if event in self:
            if isinstance(event, self._event_type):
                return self.get(event).combine(event)
            return self.get(event)
        self._events[str(event)] = event if isinstance(event, self._event_type) else self._event_type(event)
        return self.get(event)

    def add_handler(self, event, handler, call_limit=None) -> 'EventHandler':
        """Add a new or existing handler to a new or existing event."""
        if event not in self:
            raise EventNotFoundError('Event \'{0}\' doesn\'t exist or hasn\'t been registered to this EventManager.'.format(event))
        return self.get(event).add(handler, call_limit)


class Event(object):
    def __init__(self, name):
        self.name = name  # type: str
        self.enabled = True  # type: bool
        self._handlers = OrderedDict()  # type: OrderedDict[str, EventHandler]
        self._handler_type = EventHandler
        self._combined_type = CombinedEvent

    def __str__(self):
        return self.name

    def __contains__(self, handler):
        return hash(handler) in self._handlers

    def __getitem__(self, key) -> 'EventHandler':
        return self.get(key)

    def __setitem__(self, key, value):
        return self.set(key, value)

    def __delitem__(self, key):
        return self.remove(key)

    def __iter__(self) -> 'EventHandler':
        for handler in self._handlers.values():
            yield handler

    def __len__(self):
        return len(self._handlers)

    def __hash__(self):
        return hash(self.name)

    async def emit(self, *args, **kwargs):
        """Emit and call the handlers of the event."""
        if self.enabled and len(self):
            log.debug('Emitting event: {}'.format(self.name))
            for handler in self:
                await handler.call(*args, **kwargs)

    def get(self, handler, default=None) -> 'EventHandler':
        """Get a handler from the event."""
        return self._handlers.get(hash(handler), default)

    def set(self, key, handler):
        """Set or remove a handler from the event."""
        if handler is None:
            return self.remove(key)
        if hash(key) != hash(handler):
            raise ValueError('The key must match the assigned handler.')
        return self.add(handler)

    def add(self, handler, call_limit=None) -> 'EventHandler':
        """Add a handler to the event."""
        if not isinstance(handler, self._handler_type) and not callable(handler):
            raise TypeError('Parameter \'handler\' must be callable or of type EventHandler')
        if handler not in self:
            self._handlers[hash(handler)] = handler if isinstance(handler, self._handler_type) else self._handler_type(handler)
        self.get(handler).call_limit = call_limit
        return self.get(handler)

    def remove(self, handler):
        """Remove a handler from the event."""
        self._handlers[handler] = None

    def clear(self):
        """Remove all the handlers from the event."""
        self._handlers.clear()

    def enable(self, enabled=True):
        """Enable or set enabled to value."""
        self.enabled = enabled is True

    def disable(self):
        """Disable the event."""
        self.enabled = False

    def combine(self, other) -> 'Event':
        """Combine with another event and merge handler into a single list."""
        if other is not self:
            self._combined_type(self, other)
        return self


class CombinedEvent(Event):
    def __init__(self, event, *others):
        super().__init__(event)
        self.name = event.name  # type: str
        for event in others:
            self._absorb(event)

    def _absorb(self, event):
        self._handlers.update(event._handlers)
        event._handlers = self

    def items(self, *args, **kwargs):
        return self._handlers.items(*args, **kwargs)

    def keys(self, *args, **kwargs):
        return self._handlers.keys(*args, **kwargs)

    def values(self, *args, **kwargs):
        return self._handlers.values(*args, **kwargs)

    def update(self, *args, **kwargs):
        return self._handlers.update(*args, **kwargs)

    def pop(self, *args, **kwargs):
        return self._handlers.pop(*args, **kwargs)


class EventHandler(object):
    def __init__(self, handler, call_limit=None):
        self._handler = None  # type: asyncio.coroutine
        self._enabled = True  # type: bool
        self.call_limit = call_limit  # type: int
        self.handler = handler  # type: asyncio.coroutine

    def __hash__(self):
        """Get a hash by hashing the handler."""
        return hash(self._handler)

    async def call(self, *args, **kwargs) -> Any:
        """Call the handler."""
        if self.enabled:
            if self.call_limit:
                self.call_limit -= 1
            return await self.handler(*args, **kwargs)
        return None

    def limit(self, limit=1):
        """Set a limit for the amount of times this handler will be called."""
        self.call_limit = int(limit)

    def enable(self, value=True):
        """Enable or set enabled to value."""
        self.enabled = value

    def disable(self):
        """Disable the handler."""
        self.enabled = False

    @property
    def enabled(self) -> bool:
        """Get enabled status."""
        return self._enabled and (self.call_limit is None or self.call_limit > 0)

    @enabled.setter
    def enabled(self, enabled):
        """Set enabled status."""
        self._enabled = bool(enabled)

    @property
    def handler(self) -> asyncio.coroutine:
        """Get handler."""
        return self._handler

    @handler.setter
    def handler(self, handler):
        """Set handler."""
        if not callable(handler):
            raise TypeError('Parameter \'handler\' must be callable')
        self._handler = handler
