import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.check_phone import CheckPhoneUseCase
from app.core.abuse_prevention import abuse_prevention_service
from app.core.phone import normalize_phone_number
from app.core.errors import PersistenceUnavailableError, ServiceUnavailableError
from app.core.config import settings
from app.core.logging_utils import log_event
from app.infrastructure.database.db_config import get_db
from app.application.use_cases.check_email import CheckEmailUseCase
from app.presentation.api.auth import get_optional_authenticated_subject

router = APIRouter()
logger = logging.getLogger("ISafe.API")

class EmailRequest(BaseModel):
    # Proteção passiva por tipo no payload contra RCE/SQLi
    email: EmailStr


class PhoneRequest(BaseModel):
    phone: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return normalize_phone_number(value)


def build_restricted_osint_response() -> dict:
    return {
        "status": "RESTRICTED",
        "is_leaked": False,
        "sites": [],
        "leaked_data_types": [],
        "risk_score": {
            "pontuacao_total": 0,
            "nivel_exposicao": "Indisponível",
            "analise_engenharia_social": [],
        },
        "recommendations": [
            {
                "title": "Aguarde antes de tentar novamente",
                "priority": "medium",
                "description": "A consulta foi processada em modo restrito para proteger o serviço contra abuso.",
            }
        ],
        "action": "[!] RESPOSTA RESTRITA PARA PROTEÇÃO CONTRA ABUSO",
    }


@router.post("/check")
async def check_endpoint(payload: EmailRequest, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    """
    [!] ENDPOINT BRUTALISTA DE VARREDURA
    Passa o E-mail de injeção diretamente à camada lógica do Aegis OSINT com Sessão Aberta.
    """
    try:
        authenticated_subject = get_optional_authenticated_subject(request)
        if authenticated_subject:
            request.state.principal_id = authenticated_subject

        actor_id = abuse_prevention_service.actor_id_from_request(request)
        decision = abuse_prevention_service.evaluate_osint_request(actor_id, payload.email)

        if decision.blocked:
            if decision.retry_after_seconds:
                response.headers["Retry-After"] = str(decision.retry_after_seconds)
            response.status_code = status.HTTP_429_TOO_MANY_REQUESTS
            return build_restricted_osint_response()

        if decision.restricted:
            return build_restricted_osint_response()

        if settings.OSINT_ANONYMOUS_RESTRICTED_MODE and not authenticated_subject:
            return build_restricted_osint_response()

        resultado = await CheckEmailUseCase.execute(payload.email, db)
        return resultado
    except PersistenceUnavailableError as exc:
        log_event(logger, logging.ERROR, "osint_persistence_failure")
        raise HTTPException(status_code=503, detail="Serviço indisponível no momento.") from exc
    except ServiceUnavailableError as exc:
        log_event(logger, logging.ERROR, "osint_service_unavailable")
        raise HTTPException(status_code=503, detail="Serviço indisponível no momento.") from exc
    except ValueError as exc:
        log_event(logger, logging.WARNING, "osint_invalid_request")
        raise HTTPException(status_code=400, detail="Entrada inválida para a consulta.") from exc
    except Exception as exc:
        log_event(logger, logging.ERROR, "osint_unhandled_error")
        raise HTTPException(status_code=500, detail=f"[FALHA NA MATRIX] MOTOR DE VARREDURA CORROMPIDO. ERRO INTERNO.") from exc


@router.post("/phone/check")
async def check_phone_endpoint(payload: PhoneRequest, request: Request, response: Response):
    try:
        authenticated_subject = get_optional_authenticated_subject(request)
        if authenticated_subject:
            request.state.principal_id = authenticated_subject

        actor_id = abuse_prevention_service.actor_id_from_request(request)
        decision = abuse_prevention_service.evaluate_phone_request(actor_id, payload.phone)

        if decision.blocked:
            if decision.retry_after_seconds:
                response.headers["Retry-After"] = str(decision.retry_after_seconds)
            response.status_code = status.HTTP_429_TOO_MANY_REQUESTS
            return build_restricted_osint_response()

        if decision.restricted:
            return build_restricted_osint_response()

        if settings.OSINT_ANONYMOUS_RESTRICTED_MODE and not authenticated_subject:
            return build_restricted_osint_response()

        return await CheckPhoneUseCase.execute(payload.phone)
    except ServiceUnavailableError as exc:
        log_event(logger, logging.ERROR, "phone_lookup_unavailable")
        raise HTTPException(status_code=503, detail="Serviço indisponível no momento.") from exc
    except ValueError as exc:
        log_event(logger, logging.WARNING, "phone_lookup_invalid_request")
        raise HTTPException(status_code=400, detail="Entrada inválida para a consulta.") from exc
    except Exception as exc:
        log_event(logger, logging.ERROR, "phone_lookup_unhandled_error")
        raise HTTPException(status_code=500, detail="Erro interno.") from exc
