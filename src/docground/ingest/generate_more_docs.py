"""Zaawansowany generator kolejnych dokumentów korpusu biznesowego:
- Regulamin świadczenia usług płatniczych i prowizje (regulamin_platnosci_v2.pdf)
- Instrukcja wdrożenia protokołu FraudGuard AI (instrukcja_fraudguard_v1.pdf)
- Dokumentacja SLA i procedury disaster recovery (sla_disaster_recovery_2025.pdf)
- Raport z audytu bezpieczeństwa PCI-DSS (audyt_pci_dss_2025.pdf)
- Specyfikacja modułu webhooków i retry policy (webhooks_architecture_spec.pdf)
- Regulamin programu partnerskiego i prowizji agencyjnych (regulamin_partner_2025.pdf)
"""

import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from docground.config import RAW_DATA_DIR
from docground.ingest.font_utils import register_polish_fonts


def generate_additional_documents():
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    font_name = register_polish_fonts()
    font_bold = f"{font_name}-Bold" if font_name == "Arial" else "Helvetica-Bold"
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'], fontName=font_bold, fontSize=17, leading=21, textColor=colors.HexColor("#1A365D"), spaceAfter=10
    )
    h2_style = ParagraphStyle(
        'DocH2', parent=styles['Heading2'], fontName=font_bold, fontSize=13, leading=17, textColor=colors.HexColor("#2B6CB0"), spaceBefore=8, spaceAfter=5
    )
    body_style = ParagraphStyle(
        'DocBody', parent=styles['Normal'], fontName=font_name, fontSize=9.5, leading=13.5, textColor=colors.HexColor("#2D3748"), spaceAfter=5
    )
    legal_style = ParagraphStyle(
        'LegalBody', parent=styles['Normal'], fontName=font_name, fontSize=9, leading=13, textColor=colors.HexColor("#1A202C"), spaceAfter=4
    )

    # 7. Regulamin Płatności i Prowizji (regulamin_platnosci_v2.pdf)
    p7 = RAW_DATA_DIR / "regulamin_platnosci_v2.pdf"
    d7 = SimpleDocTemplate(str(p7), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    s7 = [
        Paragraph("Regulamin Świadczenia Usług Płatniczych NovaPay - Taryfa Prowizji v2.2", title_style),
        Paragraph("<b>Rozdział 3. Prowizje i Opłaty Interchange++</b>", h2_style),
        Paragraph(
            "Rozliczenia transakcji kartowych podlegają modelowi IC++ (Interchange Fee + Scheme Fee + Acquirer Margin). "
            "Poniższa tabela przedstawia bazowe stawki marży agenta rozliczeniowego dla poszczególnych kanałów sprzedaży.",
            body_style
        ),
        Spacer(1, 8),
        Table([
            ["Metoda Płatności", "Interchange Fee", "Opłata Organizacji (Scheme)", "Marża NovaPay", "Łączny koszt szacunkowy"],
            ["Karty debetowe Visa/Mastercard (PL)", "0.20%", "0.05% + 0.02 PLN", "0.45% + 0.10 PLN", "0.70% + 0.12 PLN"],
            ["Karty kredytowe Visa/Mastercard (PL)", "0.30%", "0.07% + 0.02 PLN", "0.55% + 0.10 PLN", "0.92% + 0.12 PLN"],
            ["Karty biznesowe / komercyjne", "1.50%", "0.15% + 0.05 PLN", "0.85% + 0.15 PLN", "2.50% + 0.20 PLN"],
            ["BLIK Standard (kod e-commerce)", "0.00%", "0.00 PLN", "0.69% + 0.00 PLN", "0.69%"],
            ["BLIK One-Click", "0.00%", "0.00 PLN", "0.75% + 0.00 PLN", "0.75%"]
        ], colWidths=[150, 90, 110, 100, 90], style=[
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2C5282")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('FONTSIZE', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
            ('ALIGN', (1,0), (-1,-1), 'CENTER')
        ]),
        Spacer(1, 10),
        Paragraph("Miesięczny próg minimalny obrotu zwalniający ze stałej opłaty manipulacyjnej (50 PLN) wynosi 15 000 PLN.", legal_style)
    ]
    d7.build(s7)

    # 8. Instrukcja Wdrożenia FraudGuard AI (instrukcja_fraudguard_v1.pdf)
    p8 = RAW_DATA_DIR / "instrukcja_fraudguard_v1.pdf"
    d8 = SimpleDocTemplate(str(p8), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    s8 = [
        Paragraph("Dokumentacja Wdrożeniowa Modułu Antyfraudowego: FraudGuard AI Engine", title_style),
        Paragraph("<b>1. Wagi Reguł i Progi Punktacji Ryzyka (Risk Score 0-100)</b>", h2_style),
        Paragraph(
            "FraudGuard AI ocenia każdą transakcję w czasie poniżej 45 ms. Wynik punktowy determinuje automatyczną ścieżkę decyzyjną:",
            body_style
        ),
        Spacer(1, 8),
        Table([
            ["Przedział punktowy", "Klasyfikacja Ryzyka", "Automatyczna Akcja", "Wymagane Uwierzytelnienie"],
            ["0 - 25 pkt", "Bardzo niskie", "ACCEPT_IMMEDIATE", "Brak dodatkowego tarcia (frictionless)"],
            ["26 - 60 pkt", "Umiarkowane", "CHALLENGE_3DS2", "Wymuszenie 3D-Secure 2.2 z biometrią"],
            ["61 - 85 pkt", "Wysokie", "MANUAL_REVIEW_QUEUE", "Wstrzymanie wypłaty na 6 godzin do weryfikacji"],
            ["86 - 100 pkt", "Krytyczne / Oszustwo", "HARD_DECLINE_BLOCK", "Blokada karty i powiadomienie banku wydawcy"]
        ], colWidths=[100, 110, 140, 190], style=[
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#7B341E")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('FONTSIZE', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
            ('ALIGN', (0,0), (2,-1), 'CENTER')
        ]),
        Spacer(1, 10),
        Paragraph("Reguła Velocity Check: więcej niż 3 transakcje w ciągu 60 sekund z tego samego adresu IP automatycznie dodaje +45 pkt do oceny ryzyka.", body_style)
    ]
    d8.build(s8)

    # 9. SLA i Disaster Recovery (sla_disaster_recovery_2025.pdf)
    p9 = RAW_DATA_DIR / "sla_disaster_recovery_2025.pdf"
    d9 = SimpleDocTemplate(str(p9), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    s9 = [
        Paragraph("Service Level Agreement (SLA) & Disaster Recovery Framework 2025", title_style),
        Paragraph("<b>1. Wskaźniki RTO i RPO dla Usług Krytycznych</b>", h2_style),
        Paragraph(
            "Infrastruktura NovaPay utrzymywana jest w architekturze Active-Active pomiędzy Data Center w Warszawie (DC1) i Frankfurcie (DC2).",
            body_style
        ),
        Spacer(1, 8),
        Table([
            ["Tier Usługi", "Systemy objęte ochroną", "Recovery Time Objective (RTO)", "Recovery Point Objective (RPO)"],
            ["Tier 1 (Core)", "Silnik autoryzacji kart, bramka BLIK", "Maksymalnie 60 sekund", "0 sekund (replikacja synchroniczna)"],
            ["Tier 2 (Rozliczenia)", "Batch clearing, generowanie wyciągów", "Maksymalnie 4 godziny", "Do 15 minut (snapshot walidacyjny)"],
            ["Tier 3 (Analityka)", "Data Warehouse, raportowanie BI", "Do 24 godzin", "Do 1 godziny"]
        ], colWidths=[100, 170, 140, 130], style=[
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1A365D")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('FONTSIZE', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
            ('ALIGN', (0,0), (0,-1), 'CENTER')
        ]),
        Spacer(1, 10),
        Paragraph("W przypadku niedostępności Tier 1 przekraczającej 0,01% w miesiącu (ponad 4,32 minuty), Klientowi przysługuje kara umowna w wysokości 15% miesięcznej opłaty stałej.", body_style)
    ]
    d9.build(s9)

    # 10. Raport z Audytu PCI-DSS (audyt_pci_dss_2025.pdf)
    p10 = RAW_DATA_DIR / "audyt_pci_dss_2025.pdf"
    d10 = SimpleDocTemplate(str(p10), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    s10 = [
        Paragraph("Podsumowanie Wykonawcze Audytu Zgodności PCI-DSS v4.0 (AOC)", title_style),
        Paragraph("<b>Weryfikacja Wymogów Bezpieczeństwa Środowiska CDE</b>", h2_style),
        Paragraph(
            "Niezależny audytor QSA SecurityLabs Sp. z o.o. przeprowadził kompleksową ocenę systemów przetwarzających dane posiadaczy kart (Cardholder Data Environment).",
            body_style
        ),
        Spacer(1, 8),
        Table([
            ["Sekcja PCI-DSS", "Obszar Weryfikacji", "Status Zgodności", "Uwagi i Zalecenia"],
            ["Wymóg 3", "Ochrona przechowywanych danych kartowych", "ZGODNY (100%)", "Tokenizacja format-preserving AES-256"],
            ["Wymóg 8", "Uwierzytelnianie wieloskładnikowe (MFA)", "ZGODNY (100%)", "Wdrożone klucze FIDO2/WebAuthn dla całego personelu"],
            ["Wymóg 10", "Logowanie i audyt dostępu do zasobów CDE", "ZGODNY Z UWAGĄ", "Wymóg retencji logów przez 365 dni spełniony w AWS S3 Glacier"],
            ["Wymóg 11", "Regularne testy penetracyjne i skanowanie podatności", "ZGODNY (100%)", "Kwartalne skany ASV bez krytycznych podatności"]
        ], colWidths=[90, 160, 120, 170], style=[
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#22543D")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('FONTSIZE', (0,0), (-1,0), 7.5),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
            ('ALIGN', (0,0), (0,-1), 'CENTER')
        ]),
        Spacer(1, 10),
        Paragraph("Certyfikat AOC wydano z datą ważności do 14 października 2026 r. z numerem referencyjnym QSA-PL-2025-8841.", body_style)
    ]
    d10.build(s10)

    # 11. Architektura Webhooków (webhooks_architecture_spec.pdf)
    p11 = RAW_DATA_DIR / "webhooks_architecture_spec.pdf"
    d11 = SimpleDocTemplate(str(p11), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    s11 = [
        Paragraph("Specyfikacja Architektury Webhooków i Kolejki Doręczeń (NovaHook v2)", title_style),
        Paragraph("<b>Harmonogram Ponowień i Format Podpisu Kryptograficznego</b>", h2_style),
        Paragraph(
            "Wszystkie zdarzenia transakcyjne (np. payment.succeeded, refund.created) są wysyłane jako żądania POST z nagłówkiem X-Nova-Signature-V2. "
            "W przypadku braku odpowiedzi HTTP 200/204 w ciągu 5000 ms, system uruchamia automatyczny mechanizm ponowień:",
            body_style
        ),
        Spacer(1, 8),
        Table([
            ["Próba doręczenia", "Opóźnienie (Interval)", "Czas skumulowany od zdarzenia", "Zachowanie po niepowodzeniu"],
            ["Próba 1", "Natychmiast (0s)", "0s", "Zapis błędu w kolejce Dead Letter Queue (DLQ)"],
            ["Próba 2", "15 sekund", "15s", "Ponowienie na alternatywny endpoint (jeśli skonfigurowany)"],
            ["Próba 3", "2 minuty", "2m 15s", "Wysłanie e-maila ostrzegawczego do dewelopera"],
            ["Próba 4", "15 minut", "17m 15s", "Wstrzymanie automatycznych retry dla danego IP"],
            ["Próba 5 (Ostatnia)", "1 godzina", "1h 17m 15s", "Oznaczenie webhooka jako FAILED, przeniesienie do Cold Storage"]
        ], colWidths=[100, 110, 140, 190], style=[
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#44337A")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('FONTSIZE', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
            ('ALIGN', (0,0), (1,-1), 'CENTER')
        ]),
        Spacer(1, 10),
        Paragraph("Podpis obliczany jest algorytmem HMAC-SHA512 z klucza webhook_secret przekazanego w portalu integratora.", body_style)
    ]
    d11.build(s11)

    # 12. Regulamin Programu Partnerskiego (regulamin_partner_2025.pdf)
    p12 = RAW_DATA_DIR / "regulamin_partner_2025.pdf"
    d12 = SimpleDocTemplate(str(p12), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    s12 = [
        Paragraph("Regulamin Programu Partnerskiego i Prowizji Integratorskich 2025", title_style),
        Paragraph("<b>Tabela Progresywnych Bonusów Wolumenowych</b>", h2_style),
        Paragraph(
            "Certyfikowani Partnerzy Technologiczni otrzymują comiesięczny udział w przychodzie (Revenue Share) "
            "wygenerowanym przez pozyskanych i aktywnych sprzedawców.",
            body_style
        ),
        Spacer(1, 8),
        Table([
            ["Poziom Partnerstwa", "Liczba Aktywnych Merchantów", "Miesięczny Wolumen Łączny", "Prowizja Revenue Share (%)"],
            ["Bronze Partner", "1 - 5", "Poniżej 500 000 PLN", "5.0% z marży netto"],
            ["Silver Partner", "6 - 20", "500 000 - 2 000 000 PLN", "10.0% z marży netto"],
            ["Gold Partner", "21 - 50", "2 000 000 - 10 000 000 PLN", "15.0% z marży netto"],
            ["Platinum Strategic", "Powyżej 50", "Powyżej 10 000 000 PLN", "22.5% z marży netto + dedykowany opiekun"]
        ], colWidths=[110, 130, 150, 150], style=[
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#744210")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('FONTSIZE', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
            ('ALIGN', (0,0), (1,-1), 'CENTER')
        ]),
        Spacer(1, 10),
        Paragraph("Wypłata prowizji następuje w terminie do 20. dnia każdego miesiąca na rachunek bankowy Partnera po wystawieniu faktury VAT.", body_style)
    ]
    d12.build(s12)

    print(f"Wygenerowano łącznie 12 trudnych dokumentów korpusu biznesowego w {RAW_DATA_DIR}")


if __name__ == "__main__":
    generate_additional_documents()
