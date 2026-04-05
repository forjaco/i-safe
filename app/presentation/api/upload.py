from fastapi import APIRouter, UploadFile, File, HTTPException
import logging

from app.application.use_cases.image_analyzer import ImageAnalyzerService
from app.core.logging_utils import log_event

logger = logging.getLogger("ISafe.OSINT")
router = APIRouter()

@router.post("/upload")
async def scan_image_for_privacy_risks(file: UploadFile = File(...)):
    """
    Recebe um documento de imagem do FrontEnd, processa completamente em memória (in-memory bytes) 
    impedindo a persistência estática de possíveis shells maliciosas. 
    Analisa marcadores de GPS.
    """
    try:
        file_bytes = await file.read()
        content_type = file.content_type
        filename = file.filename

        result = ImageAnalyzerService.analyze_privacy_risks(
            filename=filename,
            content_type=content_type,
            file_bytes=file_bytes
        )

        return result

    except ValueError as ve:
        log_event(logger, logging.WARNING, "privacy_upload_rejected", content_type=file.content_type or "unknown")
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        logger.exception("Falha inexperada ao varrer estrutura da imagem.")
        raise HTTPException(status_code=500, detail="Não foi possível processar a verificação dessa imagem de forma segura no servidor. Tente novamente.")
