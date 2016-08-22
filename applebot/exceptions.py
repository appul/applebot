class BlockCommandException(Exception):
    """Raise to block command execution in the 'command_received' event or the callback of the command."""
    pass
