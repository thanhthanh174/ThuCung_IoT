import hashlib
import hmac
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from backend.cau_hinh import bat_buoc

KHOA_BI_MAT = bat_buoc("KHOA_BI_MAT")
KHOA_GOC_THIET_BI = bat_buoc("KHOA_GOC_THIET_BI")

THUAT_TOAN = "HS256"
THOI_HAN_PHUT = 60


def bam_mat_khau(mat_khau: str) -> str:
    return bcrypt.hashpw(
        mat_khau.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def kiem_tra_mat_khau(mat_khau: str, ban_bam: str) -> bool:
    try:
        return bcrypt.checkpw(
            mat_khau.encode("utf-8"),
            ban_bam.encode("utf-8")
        )
    except ValueError:
        return False


def tao_token(ma_nguoi_dung: int) -> str:
    het_han = datetime.now(timezone.utc) + timedelta(
        minutes=THOI_HAN_PHUT
    )

    return jwt.encode(
        {"sub": str(ma_nguoi_dung), "exp": het_han},
        KHOA_BI_MAT,
        algorithm=THUAT_TOAN
    )


def doc_token(token: str):
    try:
        du_lieu = jwt.decode(
            token,
            KHOA_BI_MAT,
            algorithms=[THUAT_TOAN]
        )
        return int(du_lieu["sub"])

    except (jwt.PyJWTError, KeyError, ValueError):
        return None


# ---------- Khoa rieng cho tung thiet bi IoT ----------

def tao_khoa_thiet_bi(ma_thiet_bi: int) -> str:
    """Khoa cua thiet bi = chu ky HMAC cua ma thiet bi bang khoa goc cua server."""
    return hmac.new(
        KHOA_GOC_THIET_BI.encode("utf-8"),
        f"thiet-bi-{ma_thiet_bi}".encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def kiem_tra_khoa_thiet_bi(ma_thiet_bi: int, khoa) -> bool:
    if not khoa:
        return False

    return hmac.compare_digest(
        tao_khoa_thiet_bi(ma_thiet_bi).encode("utf-8"),
        str(khoa).encode("utf-8")
    )