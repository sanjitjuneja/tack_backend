class CustomResponseError(BaseException):
    def __init__(self, error, message, status):
        self.error = error
        self.message = message
        self.status = status


class TooManyAttemptsError(CustomResponseError):
    pass


class MultipleAccountsError(CustomResponseError):
    pass


class InvalidActionError(CustomResponseError):
    pass
