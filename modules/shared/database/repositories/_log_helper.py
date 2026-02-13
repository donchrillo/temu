"""
Shared Log Helper - Vermeidet zirkuläre Imports zwischen Repositories und LogService.

Wird von allen Repositories genutzt statt eigener _get_log_service() Funktionen (DRY).
"""


def get_log_service():
    """Lazy import to avoid circular dependency between repositories and log_service."""
    from ...logging.log_service import log_service
    return log_service
