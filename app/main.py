from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import APP_NAME, APP_VERSION, BASE_DIR
from app.schemas import ComicRequest, ComicResponse
from app.services.story_service import StoryService
from app.services.image_service import ImageService
from app.services.pdf_service import PDFService


# =========================================================
# Application
# =========================================================

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="AI-powered comic story creator using generative AI."
)


# =========================================================
# Paths
# =========================================================

TEMPLATES_DIR = BASE_DIR / "app" / "templates"
STATIC_DIR = BASE_DIR / "app" / "static"
GENERATED_DIR = BASE_DIR / "generated"


# =========================================================
# Static files
# =========================================================

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static"
)

app.mount(
    "/generated",
    StaticFiles(directory=str(GENERATED_DIR)),
    name="generated"
)


# =========================================================
# Templates
# =========================================================

templates = Jinja2Templates(
    directory=str(TEMPLATES_DIR)
)


# =========================================================
# Services
# =========================================================

story_service = StoryService()
image_service = ImageService()
pdf_service = PDFService()


# =========================================================
# Home
# =========================================================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "app_name": APP_NAME,
        }
    )


# =========================================================
# Health
# =========================================================

@app.get("/health")
async def health():

    return {
        "status": "ok",
        "application": APP_NAME,
        "version": APP_VERSION,
    }


# =========================================================
# Generate comic - API
# =========================================================

@app.post(
    "/generate-comic/json",
    response_model=ComicResponse
)
async def generate_comic_json(
    request: ComicRequest
):

    try:

        panels = story_service.generate_storyboard(request)

        for panel in panels:

            panel.image_url = image_service.generate_image(
                panel.image_prompt,
                panel.panel_number
            )

        title = (
            f"{request.character}'s "
            f"Adventure in "
            f"{request.setting}"
        )

        pdf_url = pdf_service.create_pdf(
            title,
            panels
        )

        return ComicResponse(
            title=title,
            story=request.story,
            character=request.character,
            setting=request.setting,
            tone=request.tone,
            art_style=request.art_style,
            panels=panels,
            pdf_url=pdf_url
        )

    except Exception as exc:

        print("Comic generation failed:", exc)

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )


# =========================================================
# Generate comic - Web
# =========================================================

@app.post(
    "/generate-comic",
    response_class=HTMLResponse
)
async def generate_comic(request: Request):

    form = await request.form()

    comic_request = ComicRequest(
        story=form.get("story", ""),
        character=form.get("character", ""),
        setting=form.get("setting", ""),
        tone=form.get("tone", "adventure"),
        art_style=form.get("art_style", "cartoon"),
        panel_count=int(form.get("panel_count", 5))
    )

    try:

        panels = story_service.generate_storyboard(
            comic_request
        )

        for panel in panels:

            panel.image_url = image_service.generate_image(
                panel.image_prompt,
                panel.panel_number
            )

        title = (
            f"{comic_request.character}'s "
            f"Adventure in "
            f"{comic_request.setting}"
        )

        pdf_url = pdf_service.create_pdf(
            title,
            panels
        )

        comic = ComicResponse(
            title=title,
            story=comic_request.story,
            character=comic_request.character,
            setting=comic_request.setting,
            tone=comic_request.tone,
            art_style=comic_request.art_style,
            panels=panels,
            pdf_url=pdf_url
        )

        return templates.TemplateResponse(
            request=request,
            name="comic.html",
            context={
                "request": request,
                "comic": comic
            }
        )

    except Exception as exc:

        print("Web comic generation failed:", exc)

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "request": request,
                "app_name": APP_NAME,
                "error": str(exc)
            }
        )


# =========================================================
# Test image generation
# =========================================================

@app.get("/test-image")
async def test_image():

    try:

        image_url = image_service.generate_image(
            (
                "A brave fox exploring "
                "an enchanted forest, "
                "cartoon comic style"
            ),
            0
        )

        return {
            "success": True,
            "image_url": image_url
        }

    except Exception as exc:

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(exc)
            }
        )