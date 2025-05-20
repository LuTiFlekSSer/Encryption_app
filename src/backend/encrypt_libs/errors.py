class AddTaskError(Exception):
    def __init__(self, *args):
        if args:
            self.mes = args[0]
        else:
            self.mes = None

    def __str__(self):
        if self.mes is not None:
            return f'{self.mes}'

        return 'AddTaskError has been raised'

class FunctionNotFoundError(Exception):
    def __init__(self, *args):
        if args:
            self.mes = args[0]
        else:
            self.mes = None

    def __str__(self):
        if self.mes is not None:
            return f'{self.mes}'

        return 'FunctionNotFoundError has been raised'

class InvalidKeyError(Exception):
    def __init__(self, *args):
        if args:
            self.mes = args[0]
        else:
            self.mes = None

    def __str__(self):
        if self.mes is not None:
            return f'{self.mes}'

        return 'InvalidKeyError has been raised'


class FileError(Exception):
    def __init__(self, *args):
        if args:
            self.mes = args[0]
        else:
            self.mes = None

    def __str__(self):
        if self.mes is not None:
            return f'{self.mes}'

        return 'FileError has been raised'


class SignatureError(Exception):
    def __init__(self, *args):
        if args:
            self.mes = args[0]
        else:
            self.mes = None

    def __str__(self):
        if self.mes is not None:
            return f'{self.mes}'

        return 'SignatureError has been raised'
