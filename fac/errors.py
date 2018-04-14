class BaseError(Exception):
    pass


class AuthError(BaseError):
    pass


class OwnershipError(AuthError):
    pass


class ModNotFoundError(BaseError):
    def __init__(self, mod):
        super().__init__("Mod not found: %s" % mod)
