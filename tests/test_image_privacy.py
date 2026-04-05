import io

from PIL import Image
import pytest

from app.application.use_cases.image_analyzer import ImageAnalyzerService


def build_jpeg_bytes() -> bytes:
    image = Image.new("RGB", (16, 16), (255, 0, 0))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def test_image_privacy_analysis_detects_clean_image():
    file_bytes = build_jpeg_bytes()

    result = ImageAnalyzerService.analyze_privacy_risks("clean.jpg", "image/jpeg", file_bytes)

    assert result["is_safe"] is True
    assert result["privacy_alerts"] == []
    assert result["metadata_found"] is False


def test_image_sanitization_returns_valid_image_bytes():
    file_bytes = build_jpeg_bytes()

    sanitized = ImageAnalyzerService.sanitize_image(file_bytes, "image/jpeg")
    result = ImageAnalyzerService.analyze_privacy_risks("sanitized.jpg", "image/jpeg", sanitized)

    assert isinstance(sanitized, bytes)
    assert len(sanitized) > 0
    assert result["is_safe"] is True


def test_image_privacy_rejects_truncated_payload():
    file_bytes = build_jpeg_bytes()[:20]

    with pytest.raises(ValueError):
        ImageAnalyzerService.analyze_privacy_risks("broken.jpg", "image/jpeg", file_bytes)


def test_image_privacy_rejects_mimetype_mismatch():
    file_bytes = build_jpeg_bytes()

    with pytest.raises(ValueError):
        ImageAnalyzerService.analyze_privacy_risks("fake.png", "image/png", file_bytes)


def test_image_privacy_rejects_oversized_payload(monkeypatch):
    monkeypatch.setattr("app.application.use_cases.image_analyzer.settings.IMAGE_MAX_FILE_SIZE_BYTES", 10)
    file_bytes = build_jpeg_bytes()

    with pytest.raises(ValueError):
        ImageAnalyzerService.analyze_privacy_risks("large.jpg", "image/jpeg", file_bytes)
