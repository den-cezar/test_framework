"""
Error hierarchy for the new test framework.
"""


class FrameworkError(Exception):
    """
    Base class for errors raised by the framework itself (not by the system under test).
    """


class ConfigError(FrameworkError):
    """
    Invalid or missing framework configuration.
    """


class AuthError(FrameworkError):
    """
    Failure to obtain credentials from the identity provider.
    """
