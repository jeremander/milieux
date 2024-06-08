class MilieuxError(ValueError):
    """Custom class for errors meant to be handled gracefully."""

class UserInputError(MilieuxError):
    """Error for invalid user input."""

class ConfigNotFoundError(MilieuxError):
    """Error for when the user's config file cannot be found."""

class EnvError(MilieuxError):
    """Error related to an environment."""

class EnvironmentExistsError(EnvError):
    """Error for when an environment already exists."""

class NoSuchEnvironmentError(EnvError):
    """Error for when an environment does not exist."""
    def __init__(self, env_name: str) -> None:
        self.env_name = env_name
        super().__init__(f'No environment named {env_name!r}')

class NoSuchDistributionError(EnvError):
    """Error for when a distribution does not exist."""
    def __init__(self, distro_name: str) -> None:
        self.distro_name = distro_name
        super().__init__(f'No distribution named {distro_name!r}')

class NoPackagesError(MilieuxError):
    """Error for when no packages are provided."""
