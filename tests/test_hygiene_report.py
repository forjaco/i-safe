from app.application.use_cases.generate_hygiene_report import DigitalHygieneReportGenerator


def test_hygiene_report_escapes_untrusted_html():
    report = DigitalHygieneReportGenerator.generate_html_report(
        '<img src=x onerror=alert(1)>',
        ['password', '<script>alert(1)</script>'],
    )

    assert "<script>alert(1)</script>" not in report
    assert "&LT;SCRIPT&GT;ALERT(1)&LT;/SCRIPT&GT;" in report
    assert "&lt;IMG SRC=X ONERROR=ALERT(1)&gt;" in report
