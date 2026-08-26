import atexit

from posthog import Posthog

_posthog_client: Posthog | None = None


def setup_posthog(token: str, host: str) -> None:
    global _posthog_client
    _posthog_client = Posthog(token, host=host, enable_exception_autocapture=True)
    atexit.register(_posthog_client.shutdown)


def get_posthog() -> Posthog | None:
    return _posthog_client


def shutdown_posthog() -> None:
    if _posthog_client:
        _posthog_client.shutdown()
