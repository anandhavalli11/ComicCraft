import uuid
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.config import (
    GEMINI_API_KEY,
    GEMINI_IMAGE_MODEL,
    HF_TOKEN,
    HF_IMAGE_MODEL,
    IMAGE_PROVIDER,
    IMAGES_DIR,
)


class ImageGenerationError(Exception):
    pass


class ImageService:

    def __init__(self):

        self.gemini_client = None
        self.hf_client = None

        self.gemini_failed = False
        self.hf_failed = False

        # =================================================
        # Gemini
        # =================================================

        if GEMINI_API_KEY:

            try:

                from google import genai

                self.gemini_client = genai.Client(
                    api_key=GEMINI_API_KEY
                )

                print(
                    "Gemini image service initialized."
                )

            except Exception as exc:

                print(
                    "Gemini image client initialization failed:",
                    exc
                )

        else:

            print(
                "No Gemini API key found."
            )

        # =================================================
        # Hugging Face
        # =================================================

        if HF_TOKEN:

            try:

                from huggingface_hub import InferenceClient

                self.hf_client = InferenceClient(
                    provider="auto",
                    api_key=HF_TOKEN
                )

                print(
                    "Hugging Face image service initialized."
                )

            except Exception as exc:

                print(
                    "Hugging Face initialization failed:",
                    exc
                )

        else:

            print(
                "No Hugging Face token found."
            )

    # =====================================================
    # MAIN IMAGE GENERATION
    # =====================================================

    def generate_image(
        self,
        prompt: str,
        panel_number: int
    ) -> str:

        # -------------------------------------------------
        # Gemini
        # -------------------------------------------------

        if (
            IMAGE_PROVIDER.lower() == "gemini"
            and self.gemini_client
            and not self.gemini_failed
        ):

            try:

                return self._generate_gemini_image(
                    prompt,
                    panel_number
                )

            except Exception as exc:

                print(
                    "Gemini image generation failed:",
                    exc
                )

                self.gemini_failed = True

        # -------------------------------------------------
        # Hugging Face
        # -------------------------------------------------

        if (
            IMAGE_PROVIDER.lower() == "huggingface"
            and self.hf_client
            and not self.hf_failed
        ):

            try:

                return self._generate_huggingface_image(
                    prompt,
                    panel_number
                )

            except Exception as exc:

                print(
                    "Hugging Face image generation failed:",
                    exc
                )

                self.hf_failed = True

        # -------------------------------------------------
        # LOCAL GENERATOR
        # -------------------------------------------------

        return self._create_local_comic_panel(
            prompt,
            panel_number
        )

    # =====================================================
    # GEMINI
    # =====================================================

    def _generate_gemini_image(
        self,
        prompt: str,
        panel_number: int
    ) -> str:

        full_prompt = f"""
Create a high-quality comic panel illustration.

{prompt}

Visual requirements:

- consistent main character
- expressive facial expression
- dynamic pose
- detailed environment
- cinematic composition
- professional comic illustration
- clean line art
- rich visual storytelling
- no captions
- no speech bubbles
- no written text
- no watermark
- no logo
"""

        response = (
            self.gemini_client
            .models
            .generate_content(
                model=GEMINI_IMAGE_MODEL,
                contents=full_prompt
            )
        )

        for part in response.parts:

            inline_data = getattr(
                part,
                "inline_data",
                None
            )

            if inline_data:

                image_bytes = inline_data.data

                filename = (
                    f"panel_{panel_number}_"
                    f"{uuid.uuid4().hex}.png"
                )

                path = (
                    IMAGES_DIR /
                    filename
                )

                with open(
                    path,
                    "wb"
                ) as file:

                    file.write(
                        image_bytes
                    )

                return (
                    f"/generated/images/"
                    f"{filename}"
                )

        raise ImageGenerationError(
            "Gemini returned no image."
        )

    # =====================================================
    # HUGGING FACE
    # =====================================================

    def _generate_huggingface_image(
        self,
        prompt: str,
        panel_number: int
    ) -> str:

        image = self.hf_client.text_to_image(
            prompt,
            model=HF_IMAGE_MODEL
        )

        filename = (
            f"panel_{panel_number}_"
            f"{uuid.uuid4().hex}.png"
        )

        path = (
            IMAGES_DIR /
            filename
        )

        image.save(path)

        return (
            f"/generated/images/"
            f"{filename}"
        )

    # =====================================================
    # LOCAL COMIC GENERATOR
    # =====================================================

    def _create_local_comic_panel(
        self,
        prompt: str,
        panel_number: int
    ) -> str:

        width = 1200
        height = 850

        image = Image.new(
            "RGB",
            (width, height),
            "#EAF4FF"
        )

        draw = ImageDraw.Draw(image)

        # -------------------------------------------------
        # Fonts
        # -------------------------------------------------

        title_font = self._font(
            34,
            bold=True
        )

        stage_font = self._font(
            27,
            bold=True
        )

        text_font = self._font(
            20
        )

        # -------------------------------------------------
        # Detect scene
        # -------------------------------------------------

        scene_type = self._detect_scene(
            prompt,
            panel_number
        )

        # -------------------------------------------------
        # Border
        # -------------------------------------------------

        draw.rectangle(
            [
                15,
                15,
                width - 15,
                height - 15
            ],
            outline="black",
            width=8
        )

        draw.rectangle(
            [
                30,
                30,
                width - 30,
                height - 30
            ],
            outline="black",
            width=3
        )

        # -------------------------------------------------
        # Header
        # -------------------------------------------------

        draw.rectangle(
            [
                40,
                40,
                width - 40,
                105
            ],
            fill="#222222"
        )

        draw.text(
            (65, 55),
            f"COMICCRAFT  •  PANEL {panel_number}",
            fill="white",
            font=title_font
        )

        # -------------------------------------------------
        # Scene area
        # -------------------------------------------------

        left = 60
        top = 130
        right = width - 60
        bottom = 620

        # Background according to scene
        self._draw_background(
            draw,
            scene_type,
            left,
            top,
            right,
            bottom
        )

        # -------------------------------------------------
        # Scene-specific objects
        # -------------------------------------------------

        if scene_type == "beginning":

            self._draw_beginning_scene(
                draw
            )

        elif scene_type == "discovery":

            self._draw_discovery_scene(
                draw
            )

        elif scene_type == "challenge":

            self._draw_challenge_scene(
                draw
            )

        elif scene_type == "turning":

            self._draw_turning_scene(
                draw
            )

        elif scene_type == "resolution":

            self._draw_resolution_scene(
                draw
            )

        else:

            self._draw_beginning_scene(
                draw
            )

        # -------------------------------------------------
        # Main character
        # -------------------------------------------------

        character_x = 600
        character_y = 425

        self._draw_fox(
            draw,
            character_x,
            character_y,
            scene_type
        )

        # -------------------------------------------------
        # Stage label
        # -------------------------------------------------

        labels = {
            "beginning": "THE BEGINNING",
            "discovery": "A STRANGE DISCOVERY",
            "challenge": "THE CHALLENGE",
            "turning": "THE TURNING POINT",
            "resolution": "THE RESOLUTION"
        }

        label = labels.get(
            scene_type,
            "ADVENTURE"
        )

        draw.rounded_rectangle(
            [
                70,
                145,
                365,
                195
            ],
            radius=12,
            fill="white",
            outline="black",
            width=3
        )

        draw.text(
            (90, 157),
            label,
            fill="black",
            font=stage_font
        )

        # -------------------------------------------------
        # Story description
        # -------------------------------------------------

        description = self._extract_scene_text(
            prompt
        )

        draw.rounded_rectangle(
            [
                60,
                650,
                width - 60,
                790
            ],
            radius=18,
            fill="white",
            outline="black",
            width=4
        )

        draw.text(
            (85, 670),
            "SCENE",
            fill="black",
            font=stage_font
        )

        lines = self._wrap_text(
            description,
            82
        )

        y = 710

        for line in lines[:3]:

            draw.text(
                (85, y),
                line,
                fill="black",
                font=text_font
            )

            y += 26

        # -------------------------------------------------
        # Save
        # -------------------------------------------------

        filename = (
            f"panel_{panel_number}_"
            f"{uuid.uuid4().hex}.png"
        )

        path = (
            IMAGES_DIR /
            filename
        )

        image.save(
            path,
            "PNG"
        )

        return (
            f"/generated/images/"
            f"{filename}"
        )

    # =====================================================
    # SCENE DETECTION
    # =====================================================

    def _detect_scene(
        self,
        prompt: str,
        panel_number: int
    ) -> str:

        text = prompt.lower()

        # Panel number gives us a reliable fallback.

        if (
            "beginning" in text
            or "starts the journey" in text
            or "enters" in text
        ):

            return "beginning"

        if (
            "discovery" in text
            or "discovers" in text
            or "mysterious object" in text
            or "unusual" in text
        ):

            return "discovery"

        if (
            "challenge" in text
            or "difficult" in text
            or "obstacle" in text
            or "danger" in text
        ):

            return "challenge"

        if (
            "turning point" in text
            or "clever way" in text
            or "solution" in text
            or "solve" in text
        ):

            return "turning"

        if (
            "resolution" in text
            or "successfully" in text
            or "completes" in text
            or "end of the journey" in text
        ):

            return "resolution"

        # Reliable panel fallback

        stages = {
            1: "beginning",
            2: "discovery",
            3: "challenge",
            4: "turning",
            5: "resolution"
        }

        return stages.get(
            panel_number,
            "beginning"
        )

    # =====================================================
    # BACKGROUND
    # =====================================================

    def _draw_background(
        self,
        draw,
        scene_type,
        left,
        top,
        right,
        bottom
    ):

        if scene_type == "discovery":

            sky = "#D9F1FF"
            ground = "#A9D68B"

        elif scene_type == "challenge":

            sky = "#B8C6D9"
            ground = "#7D8F6D"

        elif scene_type == "turning":

            sky = "#DDE7FF"
            ground = "#9DCB8A"

        elif scene_type == "resolution":

            sky = "#FFDFA3"
            ground = "#A8D58A"

        else:

            sky = "#BFE5FF"
            ground = "#9FD27F"

        # Sky

        draw.rectangle(
            [
                left,
                top,
                right,
                470
            ],
            fill=sky
        )

        # Ground

        draw.polygon(
            [
                (left, 450),
                (300, 405),
                (600, 450),
                (900, 400),
                (right, 445),
                (right, bottom),
                (left, bottom)
            ],
            fill=ground,
            outline="black"
        )

        # Sun

        draw.ellipse(
            [
                950,
                165,
                1040,
                255
            ],
            fill="#FFD34E",
            outline="black",
            width=3
        )

        # Clouds

        self._cloud(
            draw,
            150,
            185
        )

        self._cloud(
            draw,
            650,
            175
        )

        # Trees

        self._tree(
            draw,
            130,
            310
        )

        self._tree(
            draw,
            1050,
            300
        )

    # =====================================================
    # BEGINNING SCENE
    # =====================================================

    def _draw_beginning_scene(
        self,
        draw
    ):

        # Forest path

        draw.polygon(
            [
                (520, 450),
                (680, 450),
                (830, 620),
                (370, 620)
            ],
            fill="#D9B879",
            outline="black"
        )

        # Small sign

        draw.rectangle(
            [
                260,
                365,
                370,
                430
            ],
            fill="#B47B45",
            outline="black",
            width=3
        )

        draw.line(
            [
                315,
                430,
                315,
                500
            ],
            fill="black",
            width=8
        )

    # =====================================================
    # DISCOVERY SCENE
    # =====================================================

    def _draw_discovery_scene(
        self,
        draw
    ):

        # Glowing mysterious object

        draw.ellipse(
            [
                790,
                330,
                950,
                490
            ],
            fill="#FFF27A",
            outline="black",
            width=5
        )

        # Glow rings

        draw.ellipse(
            [
                750,
                290,
                990,
                530
            ],
            outline="#FFF27A",
            width=6
        )

        draw.ellipse(
            [
                715,
                255,
                1025,
                565
            ],
            outline="#FFF27A",
            width=4
        )

        # Sparkles

        self._sparkle(
            draw,
            760,
            280
        )

        self._sparkle(
            draw,
            1000,
            300
        )

        self._sparkle(
            draw,
            740,
            510
        )

    # =====================================================
    # CHALLENGE SCENE
    # =====================================================

    def _draw_challenge_scene(
        self,
        draw
    ):

        # Large obstacle

        draw.polygon(
            [
                (780, 350),
                (930, 270),
                (1080, 360),
                (1020, 520),
                (820, 520)
            ],
            fill="#777777",
            outline="black"
        )

        # Cracks

        draw.line(
            [
                880,
                340,
                850,
                410,
                900,
                450
            ],
            fill="black",
            width=5
        )

        draw.line(
            [
                980,
                350,
                950,
                420,
                1000,
                480
            ],
            fill="black",
            width=5
        )

        # Warning marks

        draw.text(
            (250, 280),
            "!",
            fill="#C62828",
            font=self._font(
                80,
                bold=True
            )
        )

        draw.text(
            (330, 250),
            "!",
            fill="#C62828",
            font=self._font(
                60,
                bold=True
            )
        )

    # =====================================================
    # TURNING POINT SCENE
    # =====================================================

    def _draw_turning_scene(
        self,
        draw
    ):

        # Bridge/path to solution

        draw.polygon(
            [
                (250, 480),
                (410, 420),
                (900, 330),
                (1000, 400),
                (430, 520)
            ],
            fill="#C6A66B",
            outline="black"
        )

        # Light beam

        draw.polygon(
            [
                (620, 180),
                (760, 180),
                (900, 470),
                (500, 470)
            ],
            fill="#FFF1A8"
        )

        # Idea spark

        self._sparkle(
            draw,
            690,
            240
        )

    # =====================================================
    # RESOLUTION SCENE
    # =====================================================

    def _draw_resolution_scene(
        self,
        draw
    ):

        # Celebration rays

        for angle_x in range(
            250,
            1050,
            100
        ):

            draw.line(
                [
                    650,
                    220,
                    angle_x,
                    140
                ],
                fill="#E8B84A",
                width=4
            )

        # Flowers

        self._flower(
            draw,
            260,
            510
        )

        self._flower(
            draw,
            350,
            530
        )

        self._flower(
            draw,
            980,
            500
        )

        # Celebration stars

        self._sparkle(
            draw,
            420,
            230
        )

        self._sparkle(
            draw,
            900,
            230
        )

    # =====================================================
    # FOX CHARACTER
    # =====================================================

    def _draw_fox(
        self,
        draw,
        x,
        y,
        scene_type
    ):

        # Body

        draw.ellipse(
            [
                x - 75,
                y - 5,
                x + 75,
                y + 140
            ],
            fill="#E88745",
            outline="black",
            width=5
        )

        # Head

        draw.ellipse(
            [
                x - 90,
                y - 145,
                x + 90,
                y + 35
            ],
            fill="#F0A05A",
            outline="black",
            width=5
        )

        # Ears

        draw.polygon(
            [
                (x - 65, y - 105),
                (x - 110, y - 175),
                (x - 35, y - 135)
            ],
            fill="#E88745",
            outline="black"
        )

        draw.polygon(
            [
                (x + 65, y - 105),
                (x + 110, y - 175),
                (x + 35, y - 135)
            ],
            fill="#E88745",
            outline="black"
        )

        # Inner ears

        draw.polygon(
            [
                (x - 70, y - 125),
                (x - 95, y - 155),
                (x - 55, y - 140)
            ],
            fill="#F6C2A0"
        )

        draw.polygon(
            [
                (x + 70, y - 125),
                (x + 95, y - 155),
                (x + 55, y - 140)
            ],
            fill="#F6C2A0"
        )

        # Eyes

        draw.ellipse(
            [
                x - 55,
                y - 85,
                x - 28,
                y - 55
            ],
            fill="black"
        )

        draw.ellipse(
            [
                x + 28,
                y - 85,
                x + 55,
                y - 55
            ],
            fill="black"
        )

        # Eye highlights

        draw.ellipse(
            [
                x - 48,
                y - 79,
                x - 41,
                y - 72
            ],
            fill="white"
        )

        draw.ellipse(
            [
                x + 35,
                y - 79,
                x + 42,
                y - 72
            ],
            fill="white"
        )

        # Nose

        draw.ellipse(
            [
                x - 14,
                y - 38,
                x + 14,
                y - 10
            ],
            fill="black"
        )

        # Expression

        if scene_type == "challenge":

            # Worried eyebrows

            draw.line(
                [
                    x - 55,
                    y - 100,
                    x - 25,
                    y - 92
                ],
                fill="black",
                width=5
            )

            draw.line(
                [
                    x + 25,
                    y - 92,
                    x + 55,
                    y - 100
                ],
                fill="black",
                width=5
            )

            # Worried mouth

            draw.arc(
                [
                    x - 35,
                    y - 15,
                    x + 35,
                    y + 40
                ],
                180,
                360,
                fill="black",
                width=5
            )

        elif scene_type in [
            "turning",
            "resolution"
        ]:

            # Happy smile

            draw.arc(
                [
                    x - 38,
                    y - 35,
                    x + 38,
                    y + 30
                ],
                10,
                170,
                fill="black",
                width=5
            )

        else:

            # Normal smile

            draw.arc(
                [
                    x - 30,
                    y - 30,
                    x + 30,
                    y + 25
                ],
                10,
                170,
                fill="black",
                width=4
            )

        # Arms

        if scene_type == "resolution":

            # Raised arms

            draw.line(
                [
                    x - 55,
                    y + 40,
                    x - 135,
                    y - 30
                ],
                fill="black",
                width=12
            )

            draw.line(
                [
                    x + 55,
                    y + 40,
                    x + 135,
                    y - 30
                ],
                fill="black",
                width=12
            )

        elif scene_type == "discovery":

            # One arm pointing

            draw.line(
                [
                    x + 55,
                    y + 35,
                    x + 145,
                    y - 35
                ],
                fill="black",
                width=12
            )

            draw.line(
                [
                    x - 55,
                    y + 35,
                    x - 110,
                    y + 90
                ],
                fill="black",
                width=12
            )

        elif scene_type == "challenge":

            # Defensive pose

            draw.line(
                [
                    x - 55,
                    y + 35,
                    x - 135,
                    y + 20
                ],
                fill="black",
                width=12
            )

            draw.line(
                [
                    x + 55,
                    y + 35,
                    x + 135,
                    y + 20
                ],
                fill="black",
                width=12
            )

        else:

            # Normal walking pose

            draw.line(
                [
                    x - 55,
                    y + 35,
                    x - 130,
                    y + 85
                ],
                fill="black",
                width=12
            )

            draw.line(
                [
                    x + 55,
                    y + 35,
                    x + 130,
                    y - 10
                ],
                fill="black",
                width=12
            )

        # Legs

        draw.line(
            [
                x - 35,
                y + 115,
                x - 65,
                y + 205
            ],
            fill="black",
            width=14
        )

        draw.line(
            [
                x + 35,
                y + 115,
                x + 70,
                y + 205
            ],
            fill="black",
            width=14
        )

        # Tail

        draw.arc(
            [
                x + 60,
                y + 20,
                x + 200,
                y + 175
            ],
            250,
            110,
            fill="#E88745",
            width=22
        )

    # =====================================================
    # TREE
    # =====================================================

    def _tree(
        self,
        draw,
        x,
        y
    ):

        draw.rectangle(
            [
                x - 18,
                y,
                x + 18,
                y + 180
            ],
            fill="#76502E",
            outline="black",
            width=3
        )

        draw.ellipse(
            [
                x - 75,
                y - 70,
                x + 75,
                y + 70
            ],
            fill="#6EA052",
            outline="black",
            width=4
        )

        draw.ellipse(
            [
                x - 105,
                y - 20,
                x + 45,
                y + 90
            ],
            fill="#78A95A",
            outline="black",
            width=4
        )

        draw.ellipse(
            [
                x - 5,
                y - 20,
                x + 105,
                y + 90
            ],
            fill="#78A95A",
            outline="black",
            width=4
        )

    # =====================================================
    # CLOUD
    # =====================================================

    def _cloud(
        self,
        draw,
        x,
        y
    ):

        draw.ellipse(
            [
                x,
                y,
                x + 90,
                y + 50
            ],
            fill="white",
            outline="black",
            width=3
        )

        draw.ellipse(
            [
                x + 35,
                y - 25,
                x + 125,
                y + 50
            ],
            fill="white",
            outline="black",
            width=3
        )

        draw.ellipse(
            [
                x + 80,
                y,
                x + 170,
                y + 50
            ],
            fill="white",
            outline="black",
            width=3
        )

    # =====================================================
    # SPARKLE
    # =====================================================

    def _sparkle(
        self,
        draw,
        x,
        y
    ):

        draw.line(
            [
                x - 25,
                y,
                x + 25,
                y
            ],
            fill="#F5C542",
            width=5
        )

        draw.line(
            [
                x,
                y - 25,
                x,
                y + 25
            ],
            fill="#F5C542",
            width=5
        )

        draw.line(
            [
                x - 15,
                y - 15,
                x + 15,
                y + 15
            ],
            fill="#F5C542",
            width=3
        )

        draw.line(
            [
                x + 15,
                y - 15,
                x - 15,
                y + 15
            ],
            fill="#F5C542",
            width=3
        )

    # =====================================================
    # FLOWER
    # =====================================================

    def _flower(
        self,
        draw,
        x,
        y
    ):

        draw.line(
            [
                x,
                y,
                x,
                y + 70
            ],
            fill="#4D8B42",
            width=6
        )

        for dx, dy in [
            (-18, 0),
            (18, 0),
            (0, -18),
            (0, 18)
        ]:

            draw.ellipse(
                [
                    x + dx - 14,
                    y + dy - 14,
                    x + dx + 14,
                    y + dy + 14
                ],
                fill="#F28B82",
                outline="black",
                width=2
            )

        draw.ellipse(
            [
                x - 8,
                y - 8,
                x + 8,
                y + 8
            ],
            fill="#FFD34E",
            outline="black"
        )

    # =====================================================
    # EXTRACT TEXT
    # =====================================================

    def _extract_scene_text(
        self,
        prompt: str
    ) -> str:

        text = re.sub(
            r"\s+",
            " ",
            prompt
        ).strip()

        # Remove unnecessary AI instruction text
        # from the visible scene box.

        for marker in [
            "Create a cartoon comic panel.",
            "Create a realistic comic panel.",
            "Create a comic panel."
        ]:

            text = text.replace(
                marker,
                ""
            )

        if len(text) > 220:

            text = (
                text[:217]
                + "..."
            )

        return text.strip()

    # =====================================================
    # WRAP TEXT
    # =====================================================

    def _wrap_text(
        self,
        text: str,
        width: int
    ):

        words = text.split()

        lines = []

        current = ""

        for word in words:

            test = (
                current + " " + word
            ).strip()

            if len(test) <= width:

                current = test

            else:

                if current:

                    lines.append(
                        current
                    )

                current = word

        if current:

            lines.append(
                current
            )

        return lines

    # =====================================================
    # FONT
    # =====================================================

    def _font(
        self,
        size: int,
        bold: bool = False
    ):

        if bold:

            fonts = [
                "C:/Windows/Fonts/arialbd.ttf",
                "C:/Windows/Fonts/calibrib.ttf"
            ]

        else:

            fonts = [
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/calibri.ttf"
            ]

        for font_path in fonts:

            if Path(font_path).exists():

                try:

                    return ImageFont.truetype(
                        font_path,
                        size
                    )

                except Exception:
                    pass

        return ImageFont.load_default()