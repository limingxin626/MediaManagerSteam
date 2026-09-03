"""Transport-independent application errors."""


class ApplicationError(Exception):
    pass


class NotFoundError(ApplicationError):
    pass


class ConflictError(ApplicationError):
    pass


class ValidationError(ApplicationError):
    pass


class StorageError(ApplicationError):
    pass
