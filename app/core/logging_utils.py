import contextvars
import hashlib
import logging


request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)


def set_request_id(request_id: str) -> contextvars.Token:
    return request_id_var.set(request_id)


def reset_request_id(token: contextvars.Token) -> None:
    request_id_var.reset(token)


def get_request_id() -> str | None:
    return request_id_var.get()


def hash_value(value: str) -> str:
    normalized = value.strip().lower().encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()[:16]


def log_event(logger: logging.Logger, level: int, event: str, **fields) -> None:
    payload = {"event": event, **fields}
    request_id = get_request_id()
    if request_id:
        payload["request_id"] = request_id
    logger.log(level, " ".join(f"{key}={value}" for key, value in payload.items()))
