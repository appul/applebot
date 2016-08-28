class BlockCommandError(Exception):
    """Raise to block command execution in the 'command_received' event or the callback of the command."""
    pass


class EventNotFoundError(Exception):
    """Raise when an event cannot be found."""
    pass
