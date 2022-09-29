from basicco.type_checking import TypeCheckError

__all__ = ["TypeCheckError", "ValidationError"]


class ValidationError(Exception):
    """Value didn't pass validation."""
