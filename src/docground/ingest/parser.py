"""Layout-Aware Document Parser oparty na pdfplumber:
- Ekstrakcja tabel do natywnego formatu Markdown (z zachowaniem nagłówków i komórek)
- Ekstrakcja czystego tekstu poza obszarami tabel (brak duplikacji)
- Klasyfikacja bloków na text, table, header
- Generowanie obiektów RawBlock zachowujących stronę i współrzędne
"""

import pdfplumber
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from tabulate import tabulate


@dataclass
class RawBlock:
    doc_name: str
    doc_type: str
    page_number: int
    block_type: str  # text, table, header
    content: str
    metadata: Dict[str, Any]


class LayoutAwareParser:
    def __init__(self):
        pass

    def parse_pdf(self, file_path: Path) -> List[RawBlock]:
        file_path = Path(file_path)
        doc_name = file_path.name
        doc_type = file_path.suffix.lstrip(".").lower()
        blocks: List[RawBlock] = []

        with pdfplumber.open(file_path) as pdf:
            for page_idx, page in enumerate(pdf.pages, start=1):
                # 1. Wykrywanie i ekstrakcja tabel
                tables = page.find_tables()
                table_bboxes = [table.bbox for table in tables]

                # Ekstrakcja tabel do natywnego Markdown
                for t_idx, table in enumerate(tables):
                    extracted = table.extract()
                    if not extracted:
                        continue
                    # Oczyszczenie wierszy i wartości None
                    cleaned_rows = []
                    for row in extracted:
                        cleaned_row = [str(c).replace("\n", " ").strip() if c is not None else "" for c in row]
                        if any(cleaned_row):
                            cleaned_rows.append(cleaned_row)

                    if len(cleaned_rows) >= 2:
                        headers = cleaned_rows[0]
                        data = cleaned_rows[1:]
                        md_table = tabulate(data, headers=headers, tablefmt="github")
                    elif len(cleaned_rows) == 1:
                        md_table = tabulate(cleaned_rows, tablefmt="github")
                    else:
                        continue

                    blocks.append(
                        RawBlock(
                            doc_name=doc_name,
                            doc_type=doc_type,
                            page_number=page_idx,
                            block_type="table",
                            content=md_table,
                            metadata={"table_index": t_idx + 1, "bbox": list(table.bbox)}
                        )
                    )

                # 2. Ekstrakcja tekstu poza obszarami tabel (filtering out table bboxes)
                def not_within_tables(obj):
                    def obj_in_bbox(bbox):
                        x0, top, x1, bottom = bbox
                        return (
                            obj.get("x0", 0) >= x0 - 2
                            and obj.get("x1", 0) <= x1 + 2
                            and obj.get("top", 0) >= top - 2
                            and obj.get("bottom", 0) <= bottom + 2
                        )
                    return not any(obj_in_bbox(bbox) for bbox in table_bboxes)

                page_filtered = page.filter(not_within_tables)
                text = page_filtered.extract_text(layout=True)

                if text:
                    # Podział na logiczne akapity
                    raw_paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
                    for p in raw_paragraphs:
                        # Oczyszczenie z nadmiarowych spacji
                        cleaned_p = " ".join([line.strip() for line in p.split("\n") if line.strip()])
                        if len(cleaned_p) < 5:
                            continue
                        
                        is_header = len(cleaned_p) < 80 and (
                            cleaned_p.isupper() or cleaned_p.startswith(("Rozdział", "Tabela", "Section", "Wprowadzenie", "Regulamin"))
                        )

                        blocks.append(
                            RawBlock(
                                doc_name=doc_name,
                                doc_type=doc_type,
                                page_number=page_idx,
                                block_type="header" if is_header else "text",
                                content=cleaned_p,
                                metadata={}
                            )
                        )

        return blocks
