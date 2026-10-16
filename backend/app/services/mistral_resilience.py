"""Shared tolerance helpers for transient Mistral API failures.

Mistral's API regularly returns:
- 429 ``rate_limited`` (code 1300): per-minute quota exhausted.
- 429 ``backend_out_of_capacity`` (code 3505): not enough serving capacity.
- 5xx / timeouts during incidents.

These are transient: a short exponential backoff retry usually succeeds.
Model-availability problems (403 ``tier_not_allowed``, code 1910) are NOT
transient and must fall through to a different model instead of being retried.

Stdlib only, so this module is importable without third-party dependencies.
"""

import logging
import random
import time
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Substrings (checked case-sensitively against str(exc), then lowercased
# copy) that indicate a transient failure worth retrying.
_RETRYABLE_MARKERS = (
    "429",
    "500",
    "502",
    "503",
    "504",
    "rate_limited",
    "rate limit",
    "rate-limit",
    "backend_out_of_capacity",
    "out_of_capacity",
    "capacity",
    "overloaded",
    "timeout",
    "timed out",
    "temporarily",
    "try again",
    "retry later",
    "code:1300",
    "code\":1300",
    "'1300'",
    '"1300"',
    "code:3505",
    "code\":3505",
    "'3505'",
    '"3505',
    "3505",
    "1300",
)


def is_tier_error(exc: BaseException) -> bool:
    """True when the model is not available on the current Mistral plan."""
    msg = str(exc)
    return "tier_not_allowed" in msg or "1910" in msg or "403" in msg


def is_retryable_mistral_error(exc: BaseException) -> bool:
    """True for transient errors (rate limits, capacity, 5xx, timeouts)."""
    if is_tier_error(exc):
        return False
    lowered = str(exc).lower()
    return any(marker in lowered for marker in _RETRYABLE_MARKERS)


def backoff_delay(attempt: int, base: float = 1.0, cap: float = 8.0) -> float:
    """Exponential backoff with a small jitter: 1s, 2s, 4s, ... capped."""
    return min(cap, base * (2 ** (attempt - 1))) + random.uniform(0, 0.5)


def call_with_retry(
    fn: Callable[[], T],
    *,
    attempts: int = 3,
    base_delay: float = 1.0,
    cap: float = 8.0,
    what: str = "mistral request",
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Call ``fn`` retrying transient Mistral failures with backoff.

    Tier/plan errors and non-transient errors are re-raised immediately
    without sleeping. After ``attempts`` failed tries the last error is raised.
    """
    last_err: BaseException | None = None
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - must classify any SDK error
            last_err = exc
            if is_tier_error(exc) or attempt >= attempts or not is_retryable_mistral_error(exc):
                raise
            delay = backoff_delay(attempt, base_delay, cap)
            logger.warning(
                "%s failed (attempt %d/%d): %s. Retrying in %.1fs",
                what,
                attempt,
                attempts,
                exc,
                delay,
            )
            sleep(delay)
    assert last_err is not None  # for type-checkers; loop always raises or returns
    raise last_err


def user_facing_message(exc: BaseException) -> str:
    """Short, non-technical message safe to show in the chat UI."""
    if is_tier_error(exc):
        return (
            "The configured AI model is not available on the current Mistral plan. "
            "Please set MISTRAL_MODEL to mistral-small-latest and redeploy."
        )
    if is_retryable_mistral_error(exc):
        return (
            "The AI service is busy right now (rate limit / capacity). "
            "Please wait about 30 seconds and try again."
        )
    return "The AI service returned an unexpected error. Please try again in a moment."
