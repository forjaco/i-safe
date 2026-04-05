import json
import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.errors import PersistenceUnavailableError
from app.core.logging_utils import log_event
from app.core.security import encrypt_sensitive_data
from app.application.use_cases.calculate_risk_score import CalculateRiskScoreUseCase
from app.application.use_cases.generate_action_recommendations import GenerateActionRecommendationsUseCase
from app.infrastructure.database.models import LeakRecord

logger = logging.getLogger("ISafe.OSINT")


class CheckEmailUseCase:
    @staticmethod
    async def execute(target_email: str, db_session: AsyncSession) -> dict:
        encrypted_target = encrypt_sensitive_data(target_email)
        use_mock = settings.EMAIL_CHECK_USE_MOCK or not settings.HIBP_API_KEY

        if use_mock:
            mock_sites = ["Canva (Mock)", "LinkedIn (2012)"]
            mock_data_types = ["email", "password"]
            encrypted_report = encrypt_sensitive_data(
                json.dumps({"sites": mock_sites, "data_types": mock_data_types})
            )

            await persist_leak_record(
                db_session=db_session,
                encrypted_email=encrypted_target,
                encrypted_report=encrypted_report,
            )

            risk_summary = CalculateRiskScoreUseCase.execute(mock_data_types)
            recommendations = GenerateActionRecommendationsUseCase.execute(mock_data_types)

            return {
                "status": "MOCK_SUCCESS",
                "is_leaked": True,
                "sites": mock_sites,
                "leaked_data_types": mock_data_types,
                "risk_score": risk_summary,
                "recommendations": recommendations,
                "action": "[✔] DADOS CRIPTOGRAFADOS E ENGAVETADOS NO AEGIS.DB (MODO MOCK)",
            }

        from app.infrastructure.external_services.hibp import HIBPClient

        client = HIBPClient(api_key=settings.HIBP_API_KEY, timeout_seconds=settings.HIBP_TIMEOUT_SECONDS)
        result = await client.check_email(target_email)
        encrypted_report = encrypt_sensitive_data(
            json.dumps({"sites": result.sites, "data_types": result.data_types})
        )

        await persist_leak_record(
            db_session=db_session,
            encrypted_email=encrypted_target,
            encrypted_report=encrypted_report,
        )

        risk_summary = CalculateRiskScoreUseCase.execute(result.data_types)
        recommendations = GenerateActionRecommendationsUseCase.execute(result.data_types)

        return {
            "status": "SUCCESS",
            "is_leaked": result.is_leaked,
            "sites": result.sites,
            "leaked_data_types": result.data_types,
            "risk_score": risk_summary,
            "recommendations": recommendations,
            "action": "[✔] DADOS CRIPTOGRAFADOS E ENGAVETADOS NO AEGIS.DB",
        }


async def persist_leak_record(db_session: AsyncSession, encrypted_email: str, encrypted_report: str) -> None:
    if not settings.OSINT_PERSIST_RESULTS:
        log_event(
            logger,
            logging.WARNING,
            "osint_persistence_disabled",
            mode="diagnostic",
            reason="runtime_async_sqlite_unavailable",
        )
        return

    new_record = LeakRecord(encrypted_email=encrypted_email, encrypted_report=encrypted_report)
    db_session.add(new_record)
    try:
        await db_session.commit()
    except SQLAlchemyError as exc:
        log_event(logger, logging.ERROR, "osint_persistence_unavailable", driver="sqlalchemy_async")
        raise PersistenceUnavailableError("Persistência indisponível.") from exc
