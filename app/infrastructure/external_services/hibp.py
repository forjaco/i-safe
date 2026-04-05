import httpx
import asyncio
import logging
from typing import List
from pydantic import BaseModel, EmailStr, ValidationError
from app.core.config import settings
from app.core.errors import ServiceUnavailableError
from app.core.logging_utils import log_event

# Configuração de Logs Padrão (Sem expor no front-end os traces)
# IMPORTANTE: Em produção, o logger não deve imprimir no console simples se não configurado, e deve guardar os dados para auditoria.
logger = logging.getLogger("ISafe.OSINT")

class LeakResult(BaseModel):
    is_leaked: bool
    sites: List[str]
    data_types: List[str]

class EmailInput(BaseModel):
    email: EmailStr  # Validação estrita pela RFC 5322, evita injeção.

class HIBPClient:
    def __init__(self, api_key: str, timeout_seconds: float = 10.0):
        self.api_key = api_key
        self.headers = {
            "hibp-api-key": self.api_key,
            "user-agent": "ISafe-OSINT-App"
        }
        self.base_url = "https://haveibeenpwned.com/api/v3/breachedaccount/"
        self.timeout_seconds = timeout_seconds

    async def check_email(self, email: str) -> LeakResult:
        try:
            valid_email_obj = EmailInput(email=email)
            safe_email = valid_email_obj.email
        except ValidationError:
            log_event(logger, logging.WARNING, "hibp_validation_failed")
            raise ValueError("O endereço de e-mail fornecido possui um formato inválido.")

        url = f"{self.base_url}{safe_email}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await self._request_with_retry(client, url)

            if response.status_code == 404:
                return LeakResult(is_leaked=False, sites=[], data_types=[])

            if response.status_code == 200:
                dados = response.json()
                sites_vazados = [breach.get("Name") for breach in dados if "Name" in breach]
                data_types = sorted(
                    {
                        data_class
                        for breach in dados
                        for data_class in breach.get("DataClasses", [])
                        if isinstance(data_class, str)
                    }
                )
                return LeakResult(is_leaked=True, sites=sites_vazados, data_types=data_types or ["email"])

            if response.status_code == 429:
                log_event(logger, logging.ERROR, "hibp_rate_limit")
                raise ServiceUnavailableError("Serviço externo indisponível.")

            if response.status_code == 401:
                log_event(logger, logging.ERROR, "hibp_unauthorized")
                raise ServiceUnavailableError("Serviço externo indisponível.")

            log_event(logger, logging.ERROR, "hibp_unexpected_status", status_code=response.status_code)
            raise ServiceUnavailableError("Serviço externo indisponível.")

        except httpx.TimeoutException:
            log_event(logger, logging.ERROR, "hibp_timeout")
            raise ServiceUnavailableError("Serviço de monitoramento indisponível.")

        except httpx.RequestError:
            log_event(logger, logging.ERROR, "hibp_request_error")
            raise ServiceUnavailableError("Serviço de monitoramento indisponível.")

        except ValueError as ve:
            raise ve

        except ServiceUnavailableError:
            raise

        except Exception as exc:
            log_event(logger, logging.ERROR, "hibp_internal_error")
            raise ServiceUnavailableError("Serviço indisponível no momento.") from exc

    async def _request_with_retry(self, client: httpx.AsyncClient, url: str) -> httpx.Response:
        last_error: Exception | None = None
        attempts = settings.HIBP_MAX_RETRIES + 1
        for attempt in range(1, attempts + 1):
            try:
                return await client.get(url, headers=self.headers)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_error = exc
                if attempt >= attempts:
                    break
                log_event(logger, logging.WARNING, "hibp_retrying", attempt=attempt)
                await asyncio.sleep(settings.HIBP_RETRY_BACKOFF_SECONDS * attempt)
        assert last_error is not None
        raise last_error
