import os
from pathlib import Path

from dotenv import load_dotenv

# Doc file .env o thu muc goc cua project
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def lay(ten: str, mac_dinh: str = "") -> str:
    return os.getenv(ten, mac_dinh)


def bat_buoc(ten: str) -> str:
    gia_tri = os.getenv(ten)

    if not gia_tri:
        raise RuntimeError(
            f"Thieu bien {ten} trong file .env (xem .env.example)"
        )

    return gia_tri