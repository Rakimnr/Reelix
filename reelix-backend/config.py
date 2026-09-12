import os

GOOGLE_WEB_DETECTION_ENABLED = os.environ.get("GOOGLE_WEB_DETECTION_ENABLED", "false").lower() == "true"
AUDD_ENABLED = os.environ.get("AUDD_ENABLED", "false").lower() == "true"

MAX_EXTERNAL_MOVIE_FRAMES = 1
EXTERNAL_MOVIE_FALLBACK_FRAMES = 1
