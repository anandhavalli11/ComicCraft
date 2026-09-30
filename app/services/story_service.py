import json
import re
from typing import List, Any

from google import genai

from app.config import (
    GEMINI_API_KEY,
    GEMINI_TEXT_MODEL,
)

from app.schemas import (
    ComicRequest,
    Panel,
)


class StoryService:
    """
    ComicCraft story generation service.

    Uses Gemini when available.
    Falls back to a deterministic local storyboard
    when Gemini is unavailable.
    """

    def __init__(self):

        self.client = None

        if GEMINI_API_KEY:

            try:

                self.client = genai.Client(
                    api_key=GEMINI_API_KEY
                )

            except Exception as exc:

                print(
                    "Gemini client initialization failed:",
                    exc
                )

                self.client = None

    # =====================================================
    # Public method
    # =====================================================

    def generate_storyboard(
        self,
        request: ComicRequest
    ) -> List[Panel]:

        """
        Generate a structured comic storyboard.

        Gemini is attempted first.
        If Gemini fails, local fallback generation is used.
        """

        if self.client is not None:

            try:

                panels = self._generate_with_gemini(
                    request
                )

                if panels:

                    return panels

            except Exception as exc:

                print(
                    "Story generation error:",
                    exc
                )

        print(
            "Using local storyboard fallback."
        )

        return self._fallback_storyboard(
            request
        )

    # =====================================================
    # Gemini generation
    # =====================================================

    def _generate_with_gemini(
        self,
        request: ComicRequest
    ) -> List[Panel]:

        panel_count = request.panel_count

        prompt = f"""
You are the story-writing engine for ComicCraft,
an AI comic story creator.

Create a complete, engaging comic storyboard.

USER INPUT
----------

Story idea:
{request.story}

Main character:
{request.character}

Setting:
{request.setting}

Tone:
{request.tone}

Art style:
{request.art_style}

Number of panels:
{panel_count}

STORY REQUIREMENTS
------------------

Create exactly {panel_count} panels.

The story must have a clear progression:

1. Beginning / introduction
2. Discovery or development
3. Conflict or challenge
4. Turning point
5. Resolution / ending

If there are fewer than 5 panels, combine stages naturally.

If there are more than 5 panels, expand the middle
of the story with additional discoveries,
challenges or character moments.

Keep the same main character throughout the story.

The story should feel like a real comic rather than
a list of unrelated events.

Each panel should contain:

- panel_number
- title
- scene
- narration
- dialogue
- image_prompt

IMAGE PROMPT REQUIREMENTS
-------------------------

Each image_prompt must describe:

- the main character
- character appearance
- character action
- facial expression
- environment
- lighting
- camera/view
- important objects
- art style

Maintain character consistency between panels.

Do NOT put dialogue, captions, speech bubbles,
watermarks, logos, or written text inside the image.

JSON FORMAT
-----------

Return ONLY valid JSON.

Do not write markdown.
Do not use ```json.
Do not add explanations.

Use exactly this structure:

{{
    "panels": [
        {{
            "panel_number": 1,
            "title": "Panel title",
            "scene": "Detailed scene description.",
            "narration": "Short narration.",
            "dialogue": "Character dialogue.",
            "image_prompt": "Detailed visual prompt."
        }}
    ]
}}

Return exactly {panel_count} panels.
"""

        response = self.client.models.generate_content(
            model=GEMINI_TEXT_MODEL,
            contents=prompt
        )

        text = self._extract_response_text(
            response
        )

        if not text:

            raise ValueError(
                "Gemini returned an empty response."
            )

        data = self._parse_json(
            text
        )

        if not isinstance(data, dict):

            raise ValueError(
                "Gemini response is not a JSON object."
            )

        raw_panels = data.get(
            "panels"
        )

        if not isinstance(
            raw_panels,
            list
        ):

            raise ValueError(
                "Gemini response does not contain a valid panels list."
            )

        panels = []

        for index, item in enumerate(
            raw_panels[:panel_count],
            start=1
        ):

            if not isinstance(
                item,
                dict
            ):
                continue

            panel = Panel(
                panel_number=self._safe_int(
                    item.get(
                        "panel_number",
                        index
                    ),
                    index
                ),
                title=self._clean_text(
                    item.get(
                        "title",
                        f"Panel {index}"
                    )
                ),
                scene=self._clean_text(
                    item.get(
                        "scene",
                        ""
                    )
                ),
                narration=self._clean_text(
                    item.get(
                        "narration",
                        ""
                    )
                ),
                dialogue=self._clean_text(
                    item.get(
                        "dialogue",
                        ""
                    )
                ),
                image_prompt=self._clean_text(
                    item.get(
                        "image_prompt",
                        ""
                    )
                )
            )

            panels.append(
                panel
            )

        if len(panels) != panel_count:

            raise ValueError(
                f"Gemini returned {len(panels)} panels "
                f"instead of {panel_count}."
            )

        return panels

    # =====================================================
    # Response text extraction
    # =====================================================

    def _extract_response_text(
        self,
        response: Any
    ) -> str:

        # -----------------------------------------------
        # Standard Gemini response
        # -----------------------------------------------

        text = getattr(
            response,
            "text",
            None
        )

        if text:

            return str(
                text
            ).strip()

        # -----------------------------------------------
        # Fallback: inspect candidates
        # -----------------------------------------------

        candidates = getattr(
            response,
            "candidates",
            None
        )

        if candidates:

            for candidate in candidates:

                content = getattr(
                    candidate,
                    "content",
                    None
                )

                if not content:
                    continue

                parts = getattr(
                    content,
                    "parts",
                    None
                )

                if not parts:
                    continue

                collected = []

                for part in parts:

                    part_text = getattr(
                        part,
                        "text",
                        None
                    )

                    if part_text:

                        collected.append(
                            str(part_text)
                        )

                if collected:

                    return "\n".join(
                        collected
                    ).strip()

        return ""

    # =====================================================
    # JSON parser
    # =====================================================

    def _parse_json(
        self,
        text: str
    ) -> Any:

        cleaned = text.strip()

        # -----------------------------------------------
        # Remove markdown code fences
        # -----------------------------------------------

        cleaned = re.sub(
            r"^```(?:json)?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE
        )

        cleaned = re.sub(
            r"\s*```$",
            "",
            cleaned
        )

        cleaned = cleaned.strip()

        # -----------------------------------------------
        # Direct JSON parsing
        # -----------------------------------------------

        try:

            return json.loads(
                cleaned
            )

        except json.JSONDecodeError:
            pass

        # -----------------------------------------------
        # Extract JSON object
        # -----------------------------------------------

        start = cleaned.find(
            "{"
        )

        end = cleaned.rfind(
            "}"
        )

        if start != -1 and end != -1:

            candidate = cleaned[
                start:end + 1
            ]

            try:

                return json.loads(
                    candidate
                )

            except json.JSONDecodeError:
                pass

        raise ValueError(
            "Could not parse Gemini response as JSON."
        )

    # =====================================================
    # Fallback storyboard
    # =====================================================

    def _fallback_storyboard(
        self,
        request: ComicRequest
    ) -> List[Panel]:

        count = request.panel_count

        character = request.character.strip()

        setting = request.setting.strip()

        story = request.story.strip()

        tone = request.tone.strip()

        art_style = request.art_style.strip()

        # -------------------------------------------------
        # Character description
        # -------------------------------------------------

        character_description = (
            f"{character}, the main character"
        )

        # -------------------------------------------------
        # Story stages
        # -------------------------------------------------

        stages = [
            {
                "title": "The Beginning",
                "scene": (
                    f"{character} begins the adventure "
                    f"in {setting}."
                ),
                "narration": (
                    f"{character} starts the journey "
                    f"with curiosity and determination."
                ),
                "dialogue": (
                    f"{character}: "
                    f'"This adventure is going to be amazing!"'
                ),
                "action": (
                    f"{character} enters {setting}, "
                    f"looking around with excitement."
                )
            },
            {
                "title": "A Strange Discovery",
                "scene": (
                    f"{character} notices something unusual "
                    f"while exploring {setting}."
                ),
                "narration": (
                    f"Something unexpected catches "
                    f"{character}'s attention."
                ),
                "dialogue": (
                    f"{character}: "
                    f'"What could this be?"'
                ),
                "action": (
                    f"{character} discovers a mysterious "
                    f"object hidden in the environment."
                )
            },
            {
                "title": "The Challenge",
                "scene": (
                    f"{character} encounters a difficult "
                    f"challenge in {setting}."
                ),
                "narration": (
                    f"The journey suddenly becomes "
                    f"more difficult."
                ),
                "dialogue": (
                    f"{character}: "
                    f'"I have to keep going!"'
                ),
                "action": (
                    f"{character} faces the challenge "
                    f"bravely and searches for a solution."
                )
            },
            {
                "title": "The Turning Point",
                "scene": (
                    f"{character} discovers a clever way "
                    f"to overcome the challenge."
                ),
                "narration": (
                    f"A new idea gives "
                    f"{character} hope."
                ),
                "dialogue": (
                    f"{character}: "
                    f'"I know what I need to do!"'
                ),
                "action": (
                    f"{character} uses courage and creativity "
                    f"to solve the problem."
                )
            },
            {
                "title": "The Resolution",
                "scene": (
                    f"{character} successfully completes "
                    f"the adventure in {setting}."
                ),
                "narration": (
                    f"After overcoming the challenge, "
                    f"{character} reaches the end of the journey."
                ),
                "dialogue": (
                    f"{character}: "
                    f'"We did it!"'
                ),
                "action": (
                    f"{character} smiles proudly while "
                    f"looking across the beautiful surroundings."
                )
            },
            {
                "title": "A New Beginning",
                "scene": (
                    f"{character} discovers that the adventure "
                    f"may not be over yet."
                ),
                "narration": (
                    f"Just when everything seems finished, "
                    f"a new mystery appears."
                ),
                "dialogue": (
                    f"{character}: "
                    f'"Looks like there is more to discover."'
                ),
                "action": (
                    f"{character} looks toward a mysterious "
                    f"path leading deeper into {setting}."
                )
            },
            {
                "title": "The Hidden Secret",
                "scene": (
                    f"{character} uncovers a hidden secret "
                    f"inside {setting}."
                ),
                "narration": (
                    f"The discovery reveals a surprising "
                    f"new part of the adventure."
                ),
                "dialogue": (
                    f"{character}: "
                    f'"I never expected to find this!"'
                ),
                "action": (
                    f"{character} carefully examines a hidden "
                    f"magical object."
                )
            },
            {
                "title": "The Journey Continues",
                "scene": (
                    f"{character} continues exploring "
                    f"{setting} with renewed confidence."
                ),
                "narration": (
                    f"The adventure continues with "
                    f"new possibilities ahead."
                ),
                "dialogue": (
                    f"{character}: "
                    f'"There is still so much to explore!"'
                ),
                "action": (
                    f"{character} walks toward the horizon "
                    f"ready for the next adventure."
                )
            }
        ]

        selected = stages[
            :count
        ]

        # -------------------------------------------------
        # Ensure enough stages
        # -------------------------------------------------

        while len(selected) < count:

            index = len(selected)

            selected.append(
                stages[
                    index % len(stages)
                ]
            )

        # -------------------------------------------------
        # Create Panel objects
        # -------------------------------------------------

        panels = []

        for index, stage in enumerate(
            selected,
            start=1
        ):

            image_prompt = (
                f"Create a {art_style} comic panel. "
                f"Main character: {character_description}. "
                f"Character appearance must remain consistent "
                f"with previous panels. "
                f"Setting: {setting}. "
                f"Tone: {tone}. "
                f"Story context: {story}. "
                f"Action: {stage['action']} "
                f"Scene: {stage['scene']} "
                f"Show expressive facial emotions, "
                f"clear character pose, cinematic composition, "
                f"beautiful lighting, detailed environment, "
                f"high-quality comic illustration. "
                f"No text, no captions, no speech bubbles, "
                f"no watermark, no logo."
            )

            panels.append(
                Panel(
                    panel_number=index,
                    title=stage["title"],
                    scene=stage["scene"],
                    narration=stage["narration"],
                    dialogue=stage["dialogue"],
                    image_prompt=image_prompt
                )
            )

        return panels

    # =====================================================
    # Helpers
    # =====================================================

    @staticmethod
    def _clean_text(
        value: Any
    ) -> str:

        if value is None:

            return ""

        return str(
            value
        ).strip()

    @staticmethod
    def _safe_int(
        value: Any,
        default: int
    ) -> int:

        try:

            return int(
                value
            )

        except (
            TypeError,
            ValueError
        ):

            return default