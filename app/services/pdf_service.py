import uuid
from pathlib import Path
from typing import List

from fpdf import FPDF

from app.config import COMICS_DIR
from app.schemas import Panel


class ComicPDF(FPDF):

    def header(self):

        self.set_font(
            "Helvetica",
            "B",
            18
        )

        self.cell(
            0,
            10,
            "ComicCraft",
            align="C"
        )

        self.ln(15)


class PDFService:

    def create_pdf(
        self,
        title: str,
        panels: List[Panel]
    ) -> str:

        filename = (
            f"comic_"
            f"{uuid.uuid4().hex}.pdf"
        )

        path = COMICS_DIR / filename

        pdf = ComicPDF(
            orientation="P",
            unit="mm",
            format="A4"
        )

        pdf.set_auto_page_break(
            auto=True,
            margin=15
        )

        pdf.set_margins(
            left=15,
            top=15,
            right=15
        )

        pdf.add_page()

        # ------------------------------------------------
        # Title
        # ------------------------------------------------

        pdf.set_font(
            "Helvetica",
            "B",
            24
        )

        pdf.set_x(pdf.l_margin)

        pdf.multi_cell(
            pdf.epw,
            15,
            title,
            align="C"
        )

        pdf.ln(5)

        # ------------------------------------------------
        # Panels
        # ------------------------------------------------

        for panel in panels:

            # Make sure cursor is at the left margin
            pdf.set_x(pdf.l_margin)

            pdf.set_font(
                "Helvetica",
                "B",
                16
            )

            pdf.multi_cell(
                pdf.epw,
                10,
                f"Panel {panel.panel_number}: "
                f"{panel.title}"
            )

            # ------------------------------------------------
            # Image
            # ------------------------------------------------

            if panel.image_url:

                image_path = self._url_to_path(
                    panel.image_url
                )

                if image_path.exists():

                    pdf.set_x(pdf.l_margin)

                    pdf.image(
                        str(image_path),
                        w=min(170, pdf.epw)
                    )

                    pdf.ln(5)

            # ------------------------------------------------
            # Scene
            # ------------------------------------------------

            pdf.set_x(pdf.l_margin)

            pdf.set_font(
                "Helvetica",
                "",
                11
            )

            pdf.multi_cell(
                pdf.epw,
                7,
                f"Scene: {panel.scene}"
            )

            # ------------------------------------------------
            # Narration
            # ------------------------------------------------

            pdf.set_x(pdf.l_margin)

            pdf.multi_cell(
                pdf.epw,
                7,
                f"Narration: {panel.narration}"
            )

            # ------------------------------------------------
            # Dialogue
            # ------------------------------------------------

            pdf.set_x(pdf.l_margin)

            pdf.multi_cell(
                pdf.epw,
                7,
                f"Dialogue: {panel.dialogue}"
            )

            pdf.ln(10)

        pdf.output(str(path))

        return f"/generated/comics/{filename}"

    # ----------------------------------------------------
    # Convert URL to local path
    # ----------------------------------------------------

    def _url_to_path(
        self,
        url: str
    ) -> Path:

        relative = url.lstrip("/")

        base = (
            Path(__file__)
            .resolve()
            .parent
            .parent
            .parent
        )

        return base / relative