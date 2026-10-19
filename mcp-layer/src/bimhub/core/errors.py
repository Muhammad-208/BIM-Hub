class BimHubError(Exception):
    """Base error. Messages are shown to the agent, so keep them actionable."""


class ConfigError(BimHubError):
    pass


class ProjectNotFound(BimHubError):
    pass


class ScopeError(BimHubError):
    """An agent tried to write outside its discipline / layer."""


class BridgeError(BimHubError):
    """The desktop add-in (Revit, Navisworks, Civil 3D…) is unreachable or returned an error."""
