class APIException(Exception):
    def __init__(self, error_code: str):
        self.error_code = error_code
