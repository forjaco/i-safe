import io
import logging
from PIL import UnidentifiedImageError
from PIL import Image, ExifTags, ImageFile
from typing import Dict, Any
from app.core.config import settings

logger = logging.getLogger("ISafe.OSINT")
Image.MAX_IMAGE_PIXELS = settings.IMAGE_MAX_PIXELS
ImageFile.LOAD_TRUNCATED_IMAGES = False

FORMAT_BY_MIME_TYPE = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
}

class ImageAnalyzerService:
    @staticmethod
    def analyze_privacy_risks(filename: str, content_type: str, file_bytes: bytes) -> Dict[str, Any]:
        issues = []
        is_safe = True
        expected_format = FORMAT_BY_MIME_TYPE.get(content_type)

        if not file_bytes:
            raise ValueError("O arquivo enviado está vazio.")

        if len(file_bytes) > settings.IMAGE_MAX_FILE_SIZE_BYTES:
            limit_mb = settings.IMAGE_MAX_FILE_SIZE_BYTES // (1024 * 1024)
            raise ValueError(f"O arquivo excede o limite de segurança de {limit_mb}MB.")

        if content_type not in settings.image_allowed_mime_types:
            raise ValueError("Mimetype não aceito. Apenas JPG e PNG são permitidos.")

        try:
            img = Image.open(io.BytesIO(file_bytes))
            img.verify()
            if img.format != expected_format:
                raise ValueError("O conteúdo do arquivo não corresponde ao mimetype informado.")
        except ValueError:
            raise
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
            logger.warning("Tentativa de upload de arquivo malformado ou corrompido bloqueada.")
            raise ValueError("Não foi possível validar o arquivo de imagem com segurança.")

        try:
            img = Image.open(io.BytesIO(file_bytes))
            img.load()
            if img.format != expected_format:
                raise ValueError("O conteúdo do arquivo não corresponde ao mimetype informado.")
            if img.width <= 0 or img.height <= 0:
                raise ValueError("A imagem enviada é inválida.")
            if img.width * img.height > settings.IMAGE_MAX_PIXELS:
                raise ValueError("A imagem excede o limite seguro de resolução.")
        except ValueError:
            raise
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
            logger.warning("Falha ao reprocessar a imagem validada para análise EXIF.")
            raise ValueError("Não foi possível validar o arquivo de imagem com segurança.")

        exif_data = img.getexif() if hasattr(img, "getexif") else None

        has_gps = False
        metadata_found = False

        if exif_data:
            metadata_found = len(exif_data) > 0
            for tag_id in exif_data.keys():
                tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                if tag_name == "GPSInfo":
                    has_gps = True
                    break

        if has_gps:
            is_safe = False
            issues.append(
                "ALERTA DE PRIVACIDADE CRÍTICO: Esta imagem contém metadados de localização embutidos (Coordenadas GPS ativas). "
                "Cibercriminosos podem extrair a latitude e longitude exatas de onde esta foto foi tirada. "
                "Recomendamos que limpe ou desabilite a marcação de fotos com localização no seu aplicativo de câmera nativo."
            )

        return {
            "filename": filename,
            "is_safe": is_safe,
            "privacy_alerts": issues,
            "size_bytes": len(file_bytes),
            "metadata_found": metadata_found,
            "sanitization_available": metadata_found,
        }

    @staticmethod
    def sanitize_image(file_bytes: bytes, content_type: str) -> bytes:
        if content_type not in settings.image_allowed_mime_types:
            raise ValueError("Mimetype não aceito. Apenas JPG e PNG são permitidos.")

        ImageAnalyzerService.analyze_privacy_risks("sanitization-input", content_type, file_bytes)

        img = Image.open(io.BytesIO(file_bytes))
        img.load()
        sanitized = Image.frombytes(img.mode, img.size, img.tobytes())

        output = io.BytesIO()
        image_format = "JPEG" if content_type == "image/jpeg" else "PNG"
        save_kwargs = {"format": image_format}

        if image_format == "JPEG":
            save_kwargs["quality"] = 95
            save_kwargs["optimize"] = True

        sanitized.save(output, **save_kwargs)
        return output.getvalue()
