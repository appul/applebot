import inspect
import logging
from collections import OrderedDict
from inspect import Signature

from applebot.exceptions import EventNotFoundError

log = logging.getLogger(__name__)


class EventManager(object):
    def __init__(self):
        self._events = {}
        self._event_type = Event

    def __contains__(self, event):
        return str(event) in self._events

    def __getitem__(self, key):
        return self.get(key)

    def __iter__(self):
        for name, event in self._events.items():
            yield name, event

    def __len__(self):
        return len(self._events)

    def get(self, event, default=None):
        """Get an event from the manager."""
        return self._events.get(str(event), default)

    def add(self, event, handler=None, call_limit=None):
        """Add a new or existing event or handler to the event manager."""
        if handler is not None:
            return self.add_handler(event, handler, call_limit)
        return self.add_event(event)

    async def emit(self, event, *args, **kwargs):
        """Emit an event and call its registered handlers."""
        return await self.get(event).emit(*args, **kwargs)

    def add_event(self, event):
        """Add a new or existing event to the event manager."""
        if not isinstance(event, self._event_type) and not isinstance(event, str):
            raise TypeError('Parameter \'event\' must be of type Event or str')
        if event in self:
            if isinstance(event, self._event_type):
                return self.get(event).combine(event)
            return self.get(event)
        self._events[str(event)] = event if isinstance(event, self._event_type) else self._event_type(event)
        return self.get(event)

    def add_handler(self, event, handler, call_limit=None):
        """Add a new or existing handler to a new or existing event."""
        if event not in self:
            raise EventNotFoundError('Event \'{0}\' doesn\'t exist or hasn\'t been registered to this EventManager.')
        return self.get(event).add(handler, call_limit)


class Event(object):
    def __init__(self, name):
        self.name = name
        self.enabled = True
        self._handlers = OrderedDict()
        self._handler_type = EventHandler
        self._combined_type = CombinedEvent
        self.__signature__ = None

    def __call__(self, *args, **kwargs):
        """Emit and call the handlers of the event."""
        return self.emit(*args, **kwargs)

    def __str__(self):
        return self.name

    def __contains__(self, handler):
        return hash(handler) in self._handlers

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        return self.set(key, value)

    def __delitem__(self, key):
        return self.remove(key)

    def __iter__(self):
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
            sig = inspect.signature(self).bind(*args, **kwargs)
            for handler in self:
                await handler.call(*sig.args, **sig.kwargs)

    def get(self, handler, default=None):
        """Get a handler from the event."""
        return self._handlers.get(hash(handler), default)

    def set(self, key, handler):
        """Set or remove a handler from the event."""
        if handler is None:
            return self.remove(key)
        if hash(key) != hash(handler):
            raise ValueError('The key must match the assigned handler.')
        return self.add(handler)

    def add(self, handler, call_limit=None):
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

    def has(self, handler):
        """Call for membership test."""
        return handler in self

    def clear(self):
        """Remove all the handlers from the event."""
        return self._handlers.clear()

    def enable(self, enabled=True):
        """Enable or set enabled to value."""
        self.enabled = enabled is True

    def disable(self):
        """Disable the event."""
        self.enabled = False

    @property
    def signature(self):
        return inspect.signature(self)

    @signature.setter
    def signature(self, signature):
        self.set_signature(signature)

    def set_signature(self, signature):
        """Set the signature for the event."""
        if signature is None:
            return self.unset_signature()
        if not isinstance(signature, Signature) and not callable(signature):
            raise TypeError('Parameter \'signature\' must be callable or of type Signature')
        self.__signature__ = inspect.signature(signature) if not isinstance(signature, Signature) else signature

    def unset_signature(self):
        """Unset the signature for the event."""
        self.__signature__ = None

    def combine(self, other):
        """Combine with another event and merge handler into a single list."""
        if other is not self:
            self._combined_type(self, other)
        return self


class CombinedEvent(Event):
    def __init__(self, name, *args):
        super().__init__(name)
        self.name = next(iter(args)).name
        self._handlers = OrderedDict()
        for event in args:
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
        self._handler = None
        self._enabled = True
        self.call_limit = call_limit
        self.handler = handler

    def __call__(self, *args, **kwargs):
        """Call the handler."""
        return self.call(*args, **kwargs)

    def __hash__(self):
        """Get a hash by hashing the handler."""
        return hash(self._handler)

    async def call(self, *args, **kwargs):
        """Call the handler."""
        if self.enabled:
            if self.call_limit:
                self.call_limit -= 1
            return await self.handler(*args, **kwargs)
        return None

    def limit(self, limit=1):
        """Set a limit for the amount of times this handler will be called."""
        self.call_limit = limit

    def enable(self, value=True):
        """Enable or set enabled to value."""
        self.enabled = value

    def disable(self):
        """Disable the handler."""
        self.enabled = False

    @property
    def enabled(self):
        """Get enabled status."""
        return self._enabled and (self.call_limit is None or self.call_limit > 0)

    @enabled.setter
    def enabled(self, enabled):
        """Set enabled status."""
        self._enabled = bool(enabled)

    @property
    def handler(self):
        """Get handler."""
        return self._handler

    @handler.setter
    def handler(self, handler):
        """Set handler."""
        if not callable(handler):
            raise TypeError('Parameter \'handler\' must be callable')
        self._handler = handler

    @property
    def __signature__(self):
        return inspect.signature(self.handler)
