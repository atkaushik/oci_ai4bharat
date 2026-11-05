from pathlib import Path
from dotenv import load_dotenv

_env_loaded = False

def load_env():
    global _env_loaded
    if not _env_loaded:
        load_dotenv(Path(__file__).resolve().parent / ".env", override=True)
        _env_loaded = True
