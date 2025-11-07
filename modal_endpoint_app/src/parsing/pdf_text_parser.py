# src/parsing/pdf_text_parser.py
from pathlib import Path
from typing import Tuple, List, Tuple as Tup
import fitz


class PDFExtractor:
    @staticmethod
    def extract_pdf_text(
        pdf_path: Path,
    ) -> Tuple[str, List[Tuple[str, Tup[float, float, float, float]]]]:
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            err_msg = f"<<ERROR OPENING PDF {pdf_path.name}: {e}>>"
            return err_msg, []

        text_pages: List[str] = []
        words_with_bboxes: List[Tuple[str, Tup[float, float, float, float]]] = []

        try:
            for page_index, page in enumerate(doc):
                # Collect page text
                page_text = page.get_text("text")
                if page_text:
                    text_pages.append(page_text.strip())

                # Collect words + bboxes from the first page only
                if page_index == 0 and not words_with_bboxes:
                    words = page.get_text("words") or []

                    pdf_w = float(page.rect.width)
                    pdf_h = float(page.rect.height)

                    if pdf_w <= 0 or pdf_h <= 0:
                        # Fallback: return raw PDF coordinates if page size is invalid
                        for (x0, y0, x1, y1, wtext, *_rest) in words:
                            words_with_bboxes.append((wtext, (x0, y0, x1, y1)))
                    else:
                        inv_w = 1.0 / pdf_w
                        inv_h = 1.0 / pdf_h
                        for (x0, y0, x1, y1, wtext, *_rest) in words:
                            nx0 = max(0.0, min(1.0, x0 * inv_w))
                            ny0 = max(0.0, min(1.0, y0 * inv_h))
                            nx1 = max(0.0, min(1.0, x1 * inv_w))
                            ny1 = max(0.0, min(1.0, y1 * inv_h))
                            words_with_bboxes.append((wtext, (nx0, ny0, nx1, ny1)))
        finally:
            doc.close()

        text_content = "\n\n--- PAGE BREAK ---\n\n".join(text_pages).strip()
        return text_content, words_with_bboxes
