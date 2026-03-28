"""Settings for observability MCP server."""

import os


class ObservabilitySettings:
    """Configuration for VictoriaLogs and VictoriaTraces."""

    def __init__(self) -> None:
        # VictoriaLogs settings
        self.victorialogs_url = os.environ.get(
            "NANOBOT_VICTORIALOGS_URL",
            "http://localhost:42010",
        )
        # VictoriaTraces settings
        self.victoriatraces_url = os.environ.get(
            "NANOBOT_VICTORIATRACES_URL",
            "http://localhost:42011",
        )


def resolve_settings() -> ObservabilitySettings:
    """Load settings from environment."""
    return ObservabilitySettings()
