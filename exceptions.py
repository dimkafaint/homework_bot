class WrongStatus(Exception):
    """Вызывается при неверном статусе."""
    pass

class JsonError(Exception):
    """Вызывается при ошибках JSON"""
    pass