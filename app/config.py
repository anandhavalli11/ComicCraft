import os
from pathlib import Path

from dotenv import load_dotenv


# ---------------------------------------------------------
# Load .env
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


# ---------------------------------------------------------
# Application configuration
# ---------------------------------------------------------

APP_NAME = os.getenv(
    "APP_NAME",
    "ComicCraft - AI Comic Story Creator"
)

APP_VERSION = os.getenv(
    "APP_VERSION",
    "1.0.0"
)

DEBUG = os.getenv(
    "DEBUG",
    "true"
).lower() == "true"


# ---------------------------------------------------------
# Gemini configuration
# ---------------------------------------------------------

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    ""
)

GEMINI_TEXT_MODEL = os.getenv(
    "GEMINI_TEXT_MODEL",
    "gemini-2.5-flash"
)

GEMINI_IMAGE_MODEL = os.getenv(
    "GEMINI_IMAGE_MODEL",
    "gemini-2.5-flash-image"
)


# ---------------------------------------------------------
# Image configuration
# ---------------------------------------------------------

IMAGE_PROVIDER = os.getenv(
    "IMAGE_PROVIDER",
    "gemini"
).lower()

HF_TOKEN = os.getenv(
    "HF_TOKEN",
    ""
)

HF_IMAGE_MODEL = os.getenv(
    "HF_IMAGE_MODEL",
    "stabilityai/stable-diffusion-xl-base-1.0"
)


# ---------------------------------------------------------
# Application folders
# ---------------------------------------------------------

GENERATED_DIR = BASE_DIR / "generated"

IMAGES_DIR = GENERATED_DIR / "images"

COMICS_DIR = GENERATED_DIR / "comics"


# Make sure directories exist

IMAGES_DIR.mkdir(
    parents=True,
    exist_ok=True
)

COMICS_DIR.mkdir(
    parents=True,
    exist_ok=True
)