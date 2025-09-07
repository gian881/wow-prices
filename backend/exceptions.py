class EnvNotSetError(Exception):
    """Raised when the environment variables are not set properly."""

    def __init__(self, variables: list[str] | str, *args: object) -> None:
        if isinstance(variables, list):
            self.variable_name = ", ".join(variables)
        else:
            self.variable_name = variables
        message = (
            f"The environment variable(s) '{self.variable_name}' is not set."
        )
        self.message = message
        super().__init__(message, *args)
