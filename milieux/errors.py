class MilieuxError(ValueError):
    """Custom class for errors meant to be handled gracefully."""

class UserInputError(MilieuxError):
    """Error for invalid user input."""

class EnvironmentExistsError(MilieuxError):
    """Error for when an environment already exists."""

class NoSuchEnvironmentError(MilieuxError):
    """Error for when an environment does not exist."""

class NoPackagesError(MilieuxError):
    """Error for when no packages are provided."""

class ConfigNotFoundError(MilieuxError):
    """Error for when the user's config file cannot be found."""
