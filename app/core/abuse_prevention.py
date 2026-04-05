import hashlib
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Protocol

from fastapi import Request

from app.core.config import settings
from app.core.logging_utils import hash_value, log_event


logger = logging.getLogger("ISafe.Abuse")


@dataclass
class AbuseDecision:
    restricted: bool
    blocked: bool
    reason: str | None = None
    retry_after_seconds: int | None = None


class AbuseStore(Protocol):
    def reset(self) -> None: ...

    def window(self, bucket: str, key: str, now: float, window_seconds: int) -> Deque[float]: ...

    def target_window(
        self,
        bucket: str,
        key: str,
        now: float,
        window_seconds: int,
    ) -> Deque[tuple[float, str]]: ...


class InMemoryAbuseStore:
    def __init__(self):
        self._windows: dict[str, dict[str, Deque[float]]] = defaultdict(lambda: defaultdict(deque))
        self._target_windows: dict[str, dict[str, Deque[tuple[float, str]]]] = defaultdict(
            lambda: defaultdict(deque)
        )

    def reset(self) -> None:
        self._windows.clear()
        self._target_windows.clear()

    def window(self, bucket: str, key: str, now: float, window_seconds: int) -> Deque[float]:
        items = self._windows[bucket][key]
        while items and now - items[0] > window_seconds:
            items.popleft()
        return items

    def target_window(
        self,
        bucket: str,
        key: str,
        now: float,
        window_seconds: int,
    ) -> Deque[tuple[float, str]]:
        items = self._target_windows[bucket][key]
        while items and now - items[0][0] > window_seconds:
            items.popleft()
        return items


class AbusePreventionService:
    def __init__(self, store: AbuseStore | None = None):
        self._store = store or InMemoryAbuseStore()

    def reset(self) -> None:
        self._store.reset()

    def evaluate_osint_request(self, actor_id: str, target_email: str) -> AbuseDecision:
        return self._evaluate_lookup_request(
            actor_id=actor_id,
            target_value=target_email,
            ip_bucket="osint:ip",
            target_bucket="osint:target",
            enum_bucket="osint:enum",
            ip_window_seconds=settings.OSINT_RATE_LIMIT_PER_IP_WINDOW_SECONDS,
            ip_max_requests=settings.OSINT_RATE_LIMIT_PER_IP_MAX_REQUESTS,
            target_window_seconds=settings.OSINT_RATE_LIMIT_PER_TARGET_WINDOW_SECONDS,
            target_max_requests=settings.OSINT_RATE_LIMIT_PER_TARGET_MAX_REQUESTS,
            enum_window_seconds=settings.OSINT_ENUMERATION_WINDOW_SECONDS,
            enum_max_distinct_targets=settings.OSINT_ENUMERATION_MAX_DISTINCT_TARGETS,
            ip_limit_event="blocked_ip_rate_limit",
            target_limit_event="blocked_target_rate_limit",
            enumeration_event="restricted_enumeration_pattern",
            burst_event="suspicious_burst",
        )

    def evaluate_phone_request(self, actor_id: str, target_phone: str) -> AbuseDecision:
        return self._evaluate_lookup_request(
            actor_id=actor_id,
            target_value=target_phone,
            ip_bucket="phone:ip",
            target_bucket="phone:target",
            enum_bucket="phone:enum",
            ip_window_seconds=settings.PHONE_RATE_LIMIT_PER_IP_WINDOW_SECONDS,
            ip_max_requests=settings.PHONE_RATE_LIMIT_PER_IP_MAX_REQUESTS,
            target_window_seconds=settings.PHONE_RATE_LIMIT_PER_TARGET_WINDOW_SECONDS,
            target_max_requests=settings.PHONE_RATE_LIMIT_PER_TARGET_MAX_REQUESTS,
            enum_window_seconds=settings.PHONE_ENUMERATION_WINDOW_SECONDS,
            enum_max_distinct_targets=settings.PHONE_ENUMERATION_MAX_DISTINCT_TARGETS,
            ip_limit_event="phone_blocked_ip_rate_limit",
            target_limit_event="phone_blocked_target_rate_limit",
            enumeration_event="phone_restricted_enumeration_pattern",
            burst_event="phone_suspicious_burst",
        )

    def _evaluate_lookup_request(
        self,
        actor_id: str,
        target_value: str,
        ip_bucket: str,
        target_bucket: str,
        enum_bucket: str,
        ip_window_seconds: int,
        ip_max_requests: int,
        target_window_seconds: int,
        target_max_requests: int,
        enum_window_seconds: int,
        enum_max_distinct_targets: int,
        ip_limit_event: str,
        target_limit_event: str,
        enumeration_event: str,
        burst_event: str,
    ) -> AbuseDecision:
        now = time.monotonic()
        target_hash = self.hash_target(target_value)

        ip_window = self._store.window(
            ip_bucket,
            actor_id,
            now,
            ip_window_seconds,
        )
        target_window = self._store.window(
            target_bucket,
            target_hash,
            now,
            target_window_seconds,
        )
        enum_window = self._store.target_window(
            enum_bucket,
            actor_id,
            now,
            enum_window_seconds,
        )

        if len(ip_window) >= ip_max_requests:
            retry_after = ip_window_seconds
            self._log_event(ip_limit_event, actor_id, target_hash, len(ip_window))
            return AbuseDecision(
                restricted=True,
                blocked=True,
                reason="ip_rate_limit",
                retry_after_seconds=retry_after,
            )

        if len(target_window) >= target_max_requests:
            retry_after = target_window_seconds
            self._log_event(target_limit_event, actor_id, target_hash, len(target_window))
            return AbuseDecision(
                restricted=True,
                blocked=True,
                reason="target_rate_limit",
                retry_after_seconds=retry_after,
            )

        distinct_targets = {entry[1] for entry in enum_window}
        suspicious_enumeration = (
            target_hash not in distinct_targets
            and len(distinct_targets) >= enum_max_distinct_targets
        )

        ip_window.append(now)
        target_window.append(now)
        enum_window.append((now, target_hash))

        if suspicious_enumeration:
            self._log_event(enumeration_event, actor_id, target_hash, len(distinct_targets) + 1)
            return AbuseDecision(restricted=True, blocked=False, reason="enumeration_pattern")

        if len(ip_window) >= max(3, ip_max_requests // 2):
            self._log_event(burst_event, actor_id, target_hash, len(ip_window))

        return AbuseDecision(restricted=False, blocked=False)

    @staticmethod
    def hash_target(target_email: str) -> str:
        return hash_value(target_email)

    @staticmethod
    def actor_id_from_request(request: Request) -> str:
        principal_id = getattr(request.state, "principal_id", None)
        if principal_id:
            return f"principal:{principal_id}"

        forwarded_for = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        client_host = forwarded_for or (request.client.host if request.client else "unknown")
        user_agent = request.headers.get("user-agent", "unknown")
        user_agent_hash = hashlib.sha256(user_agent.encode("utf-8")).hexdigest()[:8]
        return f"ip:{client_host}|ua:{user_agent_hash}"

    def evaluate_auth_login(self, actor_id: str, identifier: str) -> AbuseDecision:
        now = time.monotonic()
        identifier_hash = self.hash_target(identifier)
        ip_window = self._store.window("auth:login:ip", actor_id, now, settings.AUTH_RATE_LIMIT_PER_IP_WINDOW_SECONDS)
        id_window = self._store.window(
            "auth:login:identifier",
            identifier_hash,
            now,
            settings.AUTH_LOGIN_RATE_LIMIT_PER_IDENTIFIER_WINDOW_SECONDS,
        )

        if len(ip_window) >= settings.AUTH_RATE_LIMIT_PER_IP_MAX_REQUESTS:
            retry_after = settings.AUTH_RATE_LIMIT_PER_IP_WINDOW_SECONDS
            self._log_event("auth_login_ip_rate_limit", actor_id, identifier_hash, len(ip_window))
            return AbuseDecision(True, True, "auth_login_ip_rate_limit", retry_after)

        if len(id_window) >= settings.AUTH_LOGIN_RATE_LIMIT_PER_IDENTIFIER_MAX_REQUESTS:
            retry_after = settings.AUTH_LOGIN_RATE_LIMIT_PER_IDENTIFIER_WINDOW_SECONDS
            self._log_event("auth_login_identifier_rate_limit", actor_id, identifier_hash, len(id_window))
            return AbuseDecision(True, True, "auth_login_identifier_rate_limit", retry_after)

        ip_window.append(now)
        id_window.append(now)
        return AbuseDecision(False, False)

    def evaluate_auth_refresh(self, actor_id: str) -> AbuseDecision:
        return self._evaluate_auth_action(
            "auth_refresh_rate_limit",
            "auth:refresh:ip",
            actor_id,
            settings.AUTH_REFRESH_RATE_LIMIT_PER_IP_WINDOW_SECONDS,
            settings.AUTH_REFRESH_RATE_LIMIT_PER_IP_MAX_REQUESTS,
        )

    def evaluate_auth_logout(self, actor_id: str) -> AbuseDecision:
        return self._evaluate_auth_action(
            "auth_logout_rate_limit",
            "auth:logout:ip",
            actor_id,
            settings.AUTH_LOGOUT_RATE_LIMIT_PER_IP_WINDOW_SECONDS,
            settings.AUTH_LOGOUT_RATE_LIMIT_PER_IP_MAX_REQUESTS,
        )

    def _evaluate_auth_action(
        self,
        event: str,
        bucket: str,
        actor_id: str,
        window_seconds: int,
        max_requests: int,
    ) -> AbuseDecision:
        now = time.monotonic()
        ip_window = self._store.window(bucket, actor_id, now, window_seconds)
        if len(ip_window) >= max_requests:
            self._log_event(event, actor_id, "n/a", len(ip_window))
            return AbuseDecision(True, True, event, window_seconds)
        ip_window.append(now)
        return AbuseDecision(False, False)

    def _log_event(self, event: str, actor_id: str, target_hash: str, metric: int) -> None:
        log_event(
            logger,
            logging.WARNING,
            event,
            actor=actor_id,
            target_hash=target_hash,
            metric=metric,
        )


abuse_prevention_service = AbusePreventionService()
