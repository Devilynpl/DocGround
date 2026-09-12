"""Generator syntetycznego, realistycznego trudnego korpusu biznesowego:
- Raporty finansowe z wieloma tabelami bilansowymi i RZiS
- Ogólne Warunki Ubezpieczenia (OWU) z numerowanymi artykułami i wyłączeniami odpowiedzialności
- Regulaminy promocji i cenniki wersjonowane (v1 vs v2)
- Specyfikacje techniczne API z kodami błędów i tabelami parametrów
"""

import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from docground.config import RAW_DATA_DIR


def generate_all_documents():
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()

    # Stylistyka
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=12
    )
    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=6
    )
    legal_style = ParagraphStyle(
        'LegalBody',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1A202C"),
        spaceAfter=4
    )

    # -------------------------------------------------------------
    # 1. Raport Finansowy FinTech Q3 2025 (raport_finansowy_q3_2025.pdf)
    # -------------------------------------------------------------
    doc1_path = RAW_DATA_DIR / "raport_finansowy_q3_2025.pdf"
    doc1 = SimpleDocTemplate(str(doc1_path), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    story1 = []

    # Strona 1
    story1.append(Paragraph("Grupa Kapitałowa NovaPay S.A. - Skonsolidowany Raport za Q3 2025", title_style))
    story1.append(Paragraph("<b>1. Wprowadzenie i Podsumowanie Operacyjne</b>", h2_style))
    story1.append(Paragraph(
        "W trzecim kwartale 2025 roku Grupa NovaPay odnotowała dynamiczny wzrost wolumenu transakcji bezgotówkowych. "
        "Łączny wolumen obsłużonych płatności osiągnął rekordowy poziom 14,8 mld PLN w porównaniu do 11,2 mld PLN w analogicznym okresie roku 2024. "
        "Kluczowym motorem wzrostu było wdrożenie nowego protokołu płatności odroczonych BNPL v3 oraz ekspansja na rynki CEE. "
        "Wskaźnik retencji klientów korporacyjnych wyniósł 97,4%, co potwierdza wysoką stabilność portfela.",
        body_style
    ))
    story1.append(Spacer(1, 10))
    story1.append(Paragraph("<b>Tabela 1: Główne wskaźniki finansowe i operacyjne (w mln PLN)</b>", h2_style))
    
    t1_data = [
        ["Wskaźnik / Pozycja", "Q1 2025", "Q2 2025", "Q3 2025", "Zmiana r/r (%)"],
        ["Przychody ze sprzedaży", "142.5", "158.2", "184.6", "+29.5%"],
        ["Koszty operacyjne (OPEX)", "98.1", "104.3", "116.8", "+19.1%"],
        ["EBITDA skorygowana", "44.4", "53.9", "67.8", "+52.7%"],
        ["Zysk operacyjny (EBIT)", "36.2", "45.1", "58.4", "+61.3%"],
        ["Zysk netto", "28.5", "35.8", "46.2", "+62.1%"],
        ["Marża netto (%)", "20.0%", "22.6%", "25.0%", "+5.0 pp"]
    ]
    t1 = Table(t1_data, colWidths=[200, 75, 75, 75, 95])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#F7FAFC"), colors.white])
    ]))
    story1.append(t1)
    story1.append(Spacer(1, 15))
    story1.append(Paragraph(
        "Koszty badań i rozwoju (R&D) wyniosły w Q3 2025 kwotę 18,4 mln PLN i były alokowane głównie w rozwój silnika antyfraudowego FraudGuard AI.",
        body_style
    ))
    story1.append(PageBreak())

    # Strona 2
    story1.append(Paragraph("<b>2. Struktura Segmentowa i Bilanse Ryzyka</b>", h2_style))
    story1.append(Paragraph(
        "Działalność Grupy dzieli się na trzy główne segmenty operacyjne: Płatności E-commerce, Terminale POS dla sieci detalicznych oraz Usługi Chmurowe BaaS (Banking-as-a-Service).",
        body_style
    ))
    story1.append(Spacer(1, 10))
    story1.append(Paragraph("<b>Tabela 2: Rozbicie przychodów według segmentów geograficznych (w mln PLN)</b>", h2_style))
    t2_data = [
        ["Rynek / Region", "Q3 2024", "Q3 2025", "Udział w przychodach (%)"],
        ["Polska (Rynek domowy)", "98.4", "118.2", "64.0%"],
        ["Czechy i Słowacja", "24.1", "35.6", "19.3%"],
        ["Rumunia i Węgry", "12.3", "21.4", "11.6%"],
        ["Pozostałe kraje CEE", "7.7", "9.4", "5.1%"],
        ["RAZEM", "142.5", "184.6", "100.0%"]
    ]
    t2 = Table(t2_data, colWidths=[200, 100, 100, 120])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2C5282")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#E2E8F0")),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold')
    ]))
    story1.append(t2)
    story1.append(Spacer(1, 15))
    story1.append(Paragraph(
        "Zobowiązania długoterminowe Grupy na dzień 30 września 2025 wyniosły 112,0 mln PLN, w tym kredyt konsorcjalny w wysokości 85,0 mln PLN o zmiennym oprocentowaniu WIBOR 3M + 1.85% marży bankowej.",
        body_style
    ))
    doc1.build(story1)

    # -------------------------------------------------------------
    # 2. Ogólne Warunki Ubezpieczenia Sprzętu i OC (owu_bezpieczny_biznes_2025.pdf)
    # -------------------------------------------------------------
    doc2_path = RAW_DATA_DIR / "owu_bezpieczny_biznes_2025.pdf"
    doc2 = SimpleDocTemplate(str(doc2_path), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    story2 = []

    # Strona 1
    story2.append(Paragraph("Ogólne Warunki Ubezpieczenia „Bezpieczny Biznes Plus” (OWU/BB/2025)", title_style))
    story2.append(Paragraph("<b>Rozdział I. Przedmiot i Zakres Ubezpieczenia</b>", h2_style))
    story2.append(Paragraph(
        "<b>§ 1. Postanowienia ogólne</b><br/>"
        "1. Niniejsze Ogólne Warunki Ubezpieczenia, zwane dalej OWU, mają zastosowanie do umów ubezpieczenia zawieranych przez Towarzystwo Ubezpieczeń Aethelgard S.A. z podmiotami prowadzącymi działalność gospodarczą.<br/>"
        "2. Ubezpieczeniem objęty jest sprzęt elektroniczny stacjonarny i przenośny (laptopy, smartfony, serwery) wykorzystywany bezpośrednio do prowadzenia działalności określonej w polisie.<br/>"
        "3. Ochrona ubezpieczeniowa obowiązuje na terytorium Rzeczypospolitej Polskiej, a w odniesieniu do sprzętu przenośnego – na terytorium całego świata, z zastrzeżeniem § 4 ust. 3.",
        legal_style
    ))
    story2.append(Paragraph(
        "<b>§ 2. Sumy gwarancyjne i limity odpowiedzialności</b><br/>"
        "1. Górną granicę odpowiedzialności Ubezpieczyciela za wszystkie zdarzenia w okresie ubezpieczenia stanowi Suma Ubezpieczenia określona w polisie.<br/>"
        "2. W odniesieniu do pojedynczego zdarzenia kradzieży z włamaniem sprzętu mobilnego z pojazdu, limit odpowiedzialności wynosi maksymalnie 25 000 PLN na jedno zdarzenie i 50 000 PLN w rocznym okresie ubezpieczenia.",
        legal_style
    ))
    story2.append(Spacer(1, 10))
    story2.append(Paragraph("<b>Tabela 1: Udziały własne i franszyzy redukcyjne</b>", h2_style))
    owu_t1 = [
        ["Grupa ryzyka", "Franszyza redukcyjna (udział własny)", "Karencja", "Maksymalny czas zgłoszenia"],
        ["Zalanie sprzętu elektronicznego", "500 PLN lub 10% szkody", "14 dni", "3 dni robocze"],
        ["Kradzież z włamaniem (lokal)", "Brak (0 PLN)", "Brak", "24 godziny od ujawnienia"],
        ["Kradzież z pojazdu", "1 500 PLN", "30 dni", "24 godziny od ujawnienia"],
        ["Awaria płyty głównej / przepięcie", "300 PLN", "Brak", "5 dni roboczych"]
    ]
    t_owu = Table(owu_t1, colWidths=[150, 140, 70, 160])
    t_owu.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#742A2A")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTSIZE', (0,0), (-1,0), 8.5),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#FFF5F5"), colors.white])
    ]))
    story2.append(t_owu)
    story2.append(PageBreak())

    # Strona 2
    story2.append(Paragraph("<b>Rozdział II. Wyłączenia Odpowiedzialności i Procedury Zgłoszeniowe</b>", h2_style))
    story2.append(Paragraph(
        "<b>§ 4. Wyłączenia bezwzględne</b><br/>"
        "1. Ubezpieczyciel nie odpowiada za szkody powstałe w wyniku:<br/>"
        "&nbsp;&nbsp;a) rażącego niedbalstwa Ubezpieczającego lub osób, za które ponosi odpowiedzialność, w szczególności pozostawienia sprzętu bez nadzoru w pojeździe na widocznym miejscu;<br/>"
        "&nbsp;&nbsp;b) cyberataków, oprogramowania typu ransomware, utraty lub uszkodzenia danych cyfrowych (odrębna polisa Cyber Shield);<br/>"
        "&nbsp;&nbsp;c) zużycia eksploatacyjnego, utraty pojemności akumulatorów, zarysowań obudowy niewpływających na funkcjonalność techniczną;<br/>"
        "&nbsp;&nbsp;d) działań wojennych, stanu wyjątkowego, zamieszek lub konfiskaty mienia przez organy celne.<br/>"
        "2. W przypadku niewykonania obowiązkowej kopii zapasowej danych min. raz na 7 dni, odszkodowanie za koszty odtworzenia oprogramowania zostaje zredukowane o 50%.<br/>"
        "3. Zgłoszenie szkody po przekroczeniu 7 dni kalendarzowych od zdarzenia powoduje odmowę wypłaty odszkodowania na mocy art. 827 Kodeksu Cywilnego.",
        legal_style
    ))
    doc2.build(story2)

    # -------------------------------------------------------------
    # 3. Cennik Usług Chmurowych v1 (cennik_cloud_v1_2024.pdf)
    # -------------------------------------------------------------
    doc3_path = RAW_DATA_DIR / "cennik_cloud_v1_2024.pdf"
    doc3 = SimpleDocTemplate(str(doc3_path), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    story3 = []
    story3.append(Paragraph("Oficjalny Cennik Usług Chmurowych CloudStack Enterprise - Wersja 1.4 (Obowiązuje od 01.01.2024)", title_style))
    story3.append(Paragraph("Dokument archiwalny zastąpiony nową taryfą od 2025 roku. Poniższe stawki dotyczą wyłącznie umów podpisanych w 2024 r.", body_style))
    story3.append(Spacer(1, 10))
    story3.append(Paragraph("<b>Tabela Opłat Abonamentowych (Cennik 2024 v1.4)</b>", h2_style))
    v1_data = [
        ["Plan / Zasób", "RAM / vCPU", "Pojemność SSD NVMe", "Cena miesięczna (PLN netto)", "Cena za nadmiarowy transfer (1 TB)"],
        ["Standard Cloud VM", "8 GB / 4 vCPU", "100 GB", "149 PLN", "25 PLN"],
        ["Business Scale VM", "32 GB / 8 vCPU", "500 GB", "499 PLN", "20 PLN"],
        ["HighMemory Dedicated", "128 GB / 16 vCPU", "2 000 GB", "1 499 PLN", "15 PLN"],
        ["Managed PostgreSQL", "16 GB / 4 vCPU", "250 GB", "320 PLN", "25 PLN"]
    ]
    t3 = Table(v1_data, colWidths=[130, 95, 110, 110, 110])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4A5568")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTSIZE', (0,0), (-1,0), 8.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('ALIGN', (1,0), (-1,-1), 'CENTER')
    ]))
    story3.append(t3)
    story3.append(Spacer(1, 15))
    story3.append(Paragraph("Roczny SLA wynosi 99,9% z gwarantowanym czasem reakcji Support L2 do 4 godzin w dni robocze.", body_style))
    doc3.build(story3)

    # -------------------------------------------------------------
    # 4. Cennik Usług Chmurowych v2 (cennik_cloud_v2_2025.pdf) - Aktualny
    # -------------------------------------------------------------
    doc4_path = RAW_DATA_DIR / "cennik_cloud_v2_2025.pdf"
    doc4 = SimpleDocTemplate(str(doc4_path), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    story4 = []
    story4.append(Paragraph("Oficjalny Cennik Usług Chmurowych CloudStack Enterprise - Wersja 2.0 (Obowiązuje od 01.01.2025)", title_style))
    story4.append(Paragraph("<b>Aktualna taryfa cenowa.</b> Zastępuje wersję 1.4. Wszystkie nowe subskrypcje rozliczane są według niniejszych stawek.", body_style))
    story4.append(Spacer(1, 10))
    story4.append(Paragraph("<b>Tabela Opłat Abonamentowych (Cennik 2025 v2.0)</b>", h2_style))
    v2_data = [
        ["Plan / Zasób", "RAM / vCPU", "Pojemność SSD NVMe", "Cena miesięczna (PLN netto)", "Cena za nadmiarowy transfer (1 TB)"],
        ["Standard Cloud VM", "8 GB / 4 vCPU", "150 GB", "189 PLN", "19 PLN"],
        ["Business Scale VM", "32 GB / 8 vCPU", "600 GB", "589 PLN", "15 PLN"],
        ["HighMemory Dedicated", "128 GB / 16 vCPU", "2 500 GB", "1 799 PLN", "10 PLN"],
        ["Managed PostgreSQL", "32 GB / 8 vCPU", "500 GB", "450 PLN", "19 PLN"],
        ["AI Inference GPU Node", "64 GB / 8 vCPU + A10G", "1 000 GB", "2 890 PLN", "10 PLN"]
    ]
    t4 = Table(v2_data, colWidths=[130, 110, 100, 110, 110])
    t4.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2C7A7B")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTSIZE', (0,0), (-1,0), 8.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('ALIGN', (1,0), (-1,-1), 'CENTER')
    ]))
    story4.append(t4)
    story4.append(Spacer(1, 15))
    story4.append(Paragraph("Roczny SLA został podniesiony do 99,99% w klastrach Multi-AZ z gwarantowanym czasem reakcji Support L2 do 30 minut 24/7/365.", body_style))
    doc4.build(story4)

    # -------------------------------------------------------------
    # 5. Specyfikacja Techniczna API i Kody Błędów (api_gateway_spec_v3.pdf)
    # -------------------------------------------------------------
    doc5_path = RAW_DATA_DIR / "api_gateway_spec_v3.pdf"
    doc5 = SimpleDocTemplate(str(doc5_path), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    story5 = []
    story5.append(Paragraph("NovaPay REST API Gateway v3.2 - Technical Specification", title_style))
    story5.append(Paragraph("<b>Section 1: Authentication and Rate Limiting</b>", h2_style))
    story5.append(Paragraph(
        "All API requests must be authenticated using an mTLS certificate combined with an HMAC-SHA256 signature in the X-Nova-Signature header. "
        "The default rate limit for production credentials is 2 500 requests per minute per IP CIDR block. "
        "Exceeding this quota triggers an immediate HTTP 429 response.",
        body_style
    ))
    story5.append(Spacer(1, 10))
    story5.append(Paragraph("<b>Table 1: System Error Codes and Troubleshooting Protocol</b>", h2_style))
    api_t1 = [
        ["Error Code", "HTTP Status", "Error Identifier", "Action Required / Description"],
        ["ERR_0x8001", "401 Unauthorized", "INVALID_KEY_ID", "API key not found or expired in KMS"],
        ["ERR_0x8004", "422 Unprocessable", "INSUFFICIENT_FUNDS_RESERVE", "Merchant escrow account balance below required threshold"],
        ["ERR_0x8019", "409 Conflict", "IDEMPOTENCY_KEY_COLLISION", "Same Idempotency-Key used with different payload checksum"],
        ["ERR_0x9102", "503 Unavailable", "CLEARING_CIRCUIT_BREAKER", "External banking clearing house timeout (> 3500ms)"],
        ["ERR_0x9999", "500 Internal", "ENCRYPTION_HSM_FAILURE", "Hardware Security Module synchronization fault"]
    ]
    t5 = Table(api_t1, colWidths=[75, 95, 150, 220])
    t5.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#553C9A")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTSIZE', (0,0), (-1,0), 8.5),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('ALIGN', (0,0), (1,-1), 'CENTER')
    ]))
    story5.append(t5)
    story5.append(Spacer(1, 15))
    story5.append(Paragraph(
        "Retry Policy: For error ERR_0x9102 client libraries MUST implement exponential backoff with full jitter: "
        "t = min(t_max, t_base * 2^attempt) +/- random(0, 500ms). Do NOT retry ERR_0x8004 automatically.",
        body_style
    ))
    doc5.build(story5)

    # -------------------------------------------------------------
    # 6. Procedura Bezpieczeństwa Danych i RODO (sop_cyber_security_pl.pdf)
    # -------------------------------------------------------------
    doc6_path = RAW_DATA_DIR / "sop_cyber_security_pl.pdf"
    doc6 = SimpleDocTemplate(str(doc6_path), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    story6 = []
    story6.append(Paragraph("Standardowa Procedura Operacyjna: Zarządzanie Incydentami Bezpieczeństwa (SOP-SEC-09)", title_style))
    story6.append(Paragraph("<b>1. Klasyfikacja Incydentów Cybernetycznych</b>", h2_style))
    story6.append(Paragraph(
        "Zgodnie z wymogami Dyrektywy NIS2 oraz art. 33 RODO, każdy pracownik mający podejrzenie naruszenia poufności danych "
        "zobowiązany jest do natychmiastowego zgłoszenia incydentu do Zespołu CERT (cert@novapay.example.com lub tel. 555-091-222).",
        body_style
    ))
    story6.append(Spacer(1, 10))
    story6.append(Paragraph("<b>Tabela Poziomów Eskalacji i Czasów Reakcji</b>", h2_style))
    sop_t = [
        ["Poziom Krytyczności", "Opis zagrożenia", "Czas reakcji CERT", "Powiadomienie Prezesa UODO"],
        ["KRYTYCZNY (P1)", "Wyciek niezaszyfrowanych numerów kart płatniczych / PAN", "Maksymalnie 15 minut", "W ciągu 24 godzin"],
        ["WYSOKI (P2)", "Nieautoryzowany dostęp do panelu administracyjnego", "Maksymalnie 45 minut", "W ciągu 72 godzin (jeśli ryzyko)"],
        ["ŚREDNI (P3)", "Infekcja stacji roboczej malwarem bez eksfiltracji danych", "Do 4 godzin", "Nie dotyczy / Raport wewnętrzny"],
        ["NISKI (P4)", "Podejrzany e-mail phishingowy zablokowany przez filtr", "Do 24 godzin", "Nie dotyczy"]
    ]
    t6 = Table(sop_t, colWidths=[90, 170, 110, 160])
    t6.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#9B2C2C")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('ALIGN', (0,0), (0,-1), 'CENTER')
    ]))
    story6.append(t6)
    story6.append(Spacer(1, 15))
    story6.append(Paragraph(
        "Kopie zapasowe baz transakcyjnych podlegają szyfrowaniu AES-256-GCM. Klucze szyfrujące rotowane są w cyklu 90-dniowym z wykorzystaniem modułu Thales Luna HSM.",
        body_style
    ))
    doc6.build(story6)

    print(f"Wygenerowano 6 trudnych dokumentów korpusu biznesowego w {RAW_DATA_DIR}")


if __name__ == "__main__":
    generate_all_documents()
