import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend import models
from backend.bao_mat import (
    bam_mat_khau,
    kiem_tra_mat_khau,
    tao_token,
    doc_token,
    kiem_tra_khoa_thiet_bi
)
from backend.canh_bao import (
    kiem_tra_canh_bao_thuc_an,
    bao_mat_ket_noi,
    da_ket_noi_lai
)
from backend.database import engine, SessionLocal
from backend.luoc_do import (
    NguoiDungTao,
    ThuCungTao,
    ThuCungCapNhat,
    ThietBiTao,
    ThietBiCapNhat,
    LichChoAnTao,
    LichChoAnCapNhat,
    ChoAnNgayTao,
    DuLieuThietBiTao,
    DangNhap
)
from backend.tu_dong import khoi_dong_bo_lap_lich


app = FastAPI(
    title="Smart Pet Station API",
    description="API quan ly tram cham soc thu cung thong minh",
    version="1.0.0"
)

# Chi cho phep cac nguon (web) khai bao trong .env
CORS_ORIGINS = [
    nguon.strip()
    for nguon in os.getenv(
        "CORS_ORIGINS",
        "http://127.0.0.1:5500,http://localhost:5500"
    ).split(",")
    if nguon.strip()
]

# Dung token trong header nen khong can cookie (credentials = False)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Thu muc anh thu cung: ThuCung_IoT/image
THU_MUC_ANH = Path(__file__).resolve().parent.parent / "image"
THU_MUC_ANH.mkdir(exist_ok=True)

app.mount(
    "/image",
    StaticFiles(directory=THU_MUC_ANH),
    name="image"
)

models.Base.metadata.create_all(bind=engine)

khoi_dong_bo_lap_lich()

LUONG_TOI_DA = 500
THOI_GIAN_HET_HAN_GIAY = 30


# =========================================================
# TIEN ICH: DB, DANG NHAP, KIEM TRA QUYEN SO HUU
# =========================================================

def lay_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


bearer = HTTPBearer(auto_error=False)


def loi(ma: int, noi_dung: str):
    return HTTPException(status_code=ma, detail=noi_dung)


def xac_thuc_thiet_bi(ma_thiet_bi: int, khoa):
    """Thiet bi IoT phai gui header X-Khoa-Thiet-Bi dung voi thiet bi do."""
    if not kiem_tra_khoa_thiet_bi(ma_thiet_bi, khoa):
        raise loi(401, "Khoa thiet bi khong hop le.")


def nguoi_dung_hien_tai(
    the: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(lay_db)
):
    if the is None:
        raise loi(401, "Chua dang nhap.")

    ma = doc_token(the.credentials)

    if ma is None:
        raise loi(401, "Token khong hop le hoac da het han.")

    nguoi_dung = (
        db.query(models.NguoiDung)
        .filter(models.NguoiDung.ma_nguoi_dung == ma)
        .first()
    )

    if nguoi_dung is None:
        raise loi(401, "Nguoi dung khong ton tai.")

    return nguoi_dung


def lay_thu_cung_cua_toi(db, nguoi_dung, ma_thu_cung):
    thu_cung = (
        db.query(models.ThuCung)
        .filter(
            models.ThuCung.ma_thu_cung == ma_thu_cung,
            models.ThuCung.ma_nguoi_dung == nguoi_dung.ma_nguoi_dung
        )
        .first()
    )

    if thu_cung is None:
        raise loi(404, "Khong tim thay thu cung.")

    return thu_cung


def lay_thiet_bi_cua_toi(db, nguoi_dung, ma_thiet_bi):
    thiet_bi = (
        db.query(models.ThietBi)
        .filter(
            models.ThietBi.ma_thiet_bi == ma_thiet_bi,
            models.ThietBi.ma_nguoi_dung == nguoi_dung.ma_nguoi_dung
        )
        .first()
    )

    if thiet_bi is None:
        raise loi(404, "Khong tim thay thiet bi.")

    return thiet_bi


def truy_van_cua_toi(db, mo_hinh, nguoi_dung):
    """Cac bang co cot ma_thiet_bi: chi lay du lieu cua thiet bi thuoc ve nguoi dung."""
    return (
        db.query(mo_hinh)
        .join(
            models.ThietBi,
            models.ThietBi.ma_thiet_bi == mo_hinh.ma_thiet_bi
        )
        .filter(
            models.ThietBi.ma_nguoi_dung == nguoi_dung.ma_nguoi_dung
        )
    )


def lay_ban_ghi_cua_toi(db, nguoi_dung, mo_hinh, cot_khoa, gia_tri, ten):
    ban_ghi = (
        truy_van_cua_toi(db, mo_hinh, nguoi_dung)
        .filter(cot_khoa == gia_tri)
        .first()
    )

    if ban_ghi is None:
        raise loi(404, f"Khong tim thay {ten}.")

    return ban_ghi


def kiem_tra_muc(du_lieu: dict):
    for truong in ("muc_thuc_an", "muc_nuoc"):
        gia_tri = du_lieu.get(truong)

        if gia_tri is not None and not 0 <= gia_tri <= 100:
            raise loi(400, "Muc thuc an va muc nuoc phai tu 0 den 100.")


def kiem_tra_luong(luong):
    if luong <= 0 or luong > LUONG_TOI_DA:
        raise loi(
            400,
            f"Luong thuc an phai lon hon 0 va khong qua {LUONG_TOI_DA}."
        )


# =========================================================
# TRANG CHU, KIEM TRA DB
# =========================================================

@app.get("/")
def trang_chu():
    return {"message": "Smart Pet Station API dang hoat dong!"}


@app.get("/test-db")
def test_database(db: Session = Depends(lay_db)):
    try:
        db.execute(models.NguoiDung.__table__.select().limit(1))
        return {"message": "Ket noi PostgreSQL thanh cong!"}

    except Exception:
        # Khong tra chi tiet loi ra ngoai (tranh lo thong tin he thong)
        return {"message": "Ket noi PostgreSQL that bai."}


# =========================================================
# DANG KY, DANG NHAP
# =========================================================

@app.post("/api/dang-ky")
def dang_ky(
    du_lieu: NguoiDungTao,
    db: Session = Depends(lay_db)
):
    email = du_lieu.email.strip().lower()

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise loi(400, "Email khong hop le.")

    if (
        len(du_lieu.mat_khau) < 6
        or len(du_lieu.mat_khau.encode("utf-8")) > 72
    ):
        raise loi(400, "Mat khau phai tu 6 ky tu va khong qua 72 byte.")

    da_co = (
        db.query(models.NguoiDung)
        .filter(func.lower(models.NguoiDung.email) == email)
        .first()
    )

    if da_co:
        raise loi(400, "Email da ton tai.")

    nguoi_dung = models.NguoiDung(
        ho_ten=du_lieu.ho_ten.strip(),
        email=email,
        mat_khau=bam_mat_khau(du_lieu.mat_khau)
    )

    db.add(nguoi_dung)
    db.commit()
    db.refresh(nguoi_dung)

    return {
        "ma_nguoi_dung": nguoi_dung.ma_nguoi_dung,
        "ho_ten": nguoi_dung.ho_ten,
        "email": nguoi_dung.email
    }


@app.post("/api/dang-nhap")
def dang_nhap(
    du_lieu: DangNhap,
    db: Session = Depends(lay_db)
):
    email = du_lieu.email.strip().lower()

    nguoi_dung = (
        db.query(models.NguoiDung)
        .filter(func.lower(models.NguoiDung.email) == email)
        .first()
    )

    if nguoi_dung is None or not kiem_tra_mat_khau(
        du_lieu.mat_khau,
        nguoi_dung.mat_khau
    ):
        raise loi(401, "Email hoac mat khau khong dung.")

    return {
        "access_token": tao_token(nguoi_dung.ma_nguoi_dung),
        "token_type": "bearer"
    }


@app.get("/api/toi")
def thong_tin_cua_toi(nguoi_dung=Depends(nguoi_dung_hien_tai)):
    return {
        "ma_nguoi_dung": nguoi_dung.ma_nguoi_dung,
        "ho_ten": nguoi_dung.ho_ten,
        "email": nguoi_dung.email
    }


# =========================================================
# THU CUNG (chi chu so huu)
# =========================================================

@app.get("/api/thu-cung")
def lay_danh_sach_thu_cung(
    nguoi_dung=Depends(nguoi_dung_hien_tai),
    db: Session = Depends(lay_db)
):
    return (
        db.query(models.ThuCung)
        .filter(models.ThuCung.ma_nguoi_dung == nguoi_dung.ma_nguoi_dung)
        .order_by(models.ThuCung.ma_thu_cung)
        .all()
    )


@app.post("/api/thu-cung")
def them_thu_cung(
    du_lieu: ThuCungTao,
    nguoi_dung=Depends(nguoi_dung_hien_tai),
    db: Session = Depends(lay_db)
):
    # Chu so huu luon la nguoi dang dang nhap, bo qua ma_nguoi_dung client gui
    thu_cung = models.ThuCung(
        ma_nguoi_dung=nguoi_dung.ma_nguoi_dung,
        ten_thu_cung=du_lieu.ten_thu_cung,
        loai=du_lieu.loai,
        giong=du_lieu.giong,
        gioi_tinh=du_lieu.gioi_tinh,
        ngay_sinh=du_lieu.ngay_sinh,
        can_nang=du_lieu.can_nang,
        anh=du_lieu.anh,
        ghi_chu=du_lieu.ghi_chu
    )

    db.add(thu_cung)
    db.commit()
    db.refresh(thu_cung)

    return thu_cung


@app.get("/api/thu-cung/{ma_thu_cung}")
def lay_thu_cung(
    ma_thu_cung: int,
    nguoi_dung=Depends(nguoi_dung_hien_tai),
    db: Session = Depends(lay_db)
):
    return lay_thu_cung_cua_toi(db, nguoi_dung, ma_thu_cung)


@app.put("/api/thu-cung/{ma_thu_cung}")
def cap_nhat_thu_cung(
    ma_thu_cung: int,
    du_lieu: ThuCungCapNhat,
    nguoi_dung=Depends(nguoi_dung_hien_tai),
    db: Session = Depends(lay_db)
):
    thu_cung = lay_thu_cung_cua_toi(db, nguoi_dung, ma_thu_cung)

    cap_nhat = du_lieu.model_dump(exclude_unset=True)
    cap_nhat.pop("ma_nguoi_dung", None)

    for ten_truong, gia_tri in cap_nhat.items():
        setattr(thu_cung, ten_truong, gia_tri)

    db.commit()
    db.refresh(thu_cung)

    return thu_cung


@app.delete("/api/thu-cung/{ma_thu_cung}")
def xoa_thu_cung(
    ma_thu_cung: int,
    nguoi_dung=Depends(nguoi_dung_hien_tai),
    db: Session = Depends(lay_db)
):
    thu_cung = lay_thu_cung_cua_toi(db, nguoi_dung, ma_thu_cung)

    db.delete(thu_cung)
    db.commit()

    return {"message": "Da xoa thu cung thanh cong."}


# =========================================================
# THIET BI (chi chu so huu)
# =========================================================

@app.get("/api/thiet-bi")
def lay_danh_sach_thiet_bi(
    nguoi_dung=Depends(nguoi_dung_hien_tai),
    db: Session = Depends(lay_db)
):
    return (
        db.query(models.ThietBi)
        .filter(models.ThietBi.ma_nguoi_dung == nguoi_dung.ma_nguoi_dung)
        .order_by(models.ThietBi.ma_thiet_bi)
        .all()
    )


@app.post("/api/thiet-bi")
def them_thiet_bi(
    du_lieu: ThietBiTao,
    nguoi_dung=Depends(nguoi_dung_hien_tai),
    db: Session = Depends(lay_db)
):
    kiem_tra_muc({
        "muc_thuc_an": du_lieu.muc_thuc_an,
        "muc_nuoc": du_lieu.muc_nuoc
    })

    thiet_bi_cu = (
        db.query(models.ThietBi)
        .filter(
            models.ThietBi.ma_thiet_bi_iot == du_lieu.ma_thiet_bi_iot
        )
        .first()
    )

    if thiet_bi_cu:
        raise loi(400, "Ma thiet bi IoT da ton tai.")

    thiet_bi = models.ThietBi(
        ma_nguoi_dung=nguoi_dung.ma_nguoi_dung,
        ten_thiet_bi=du_lieu.ten_thiet_bi,
        ma_thiet_bi_iot=du_lieu.ma_thiet_bi_iot,
        trang_thai=du_lieu.trang_thai,
        muc_thuc_an=du_lieu.muc_thuc_an,
        muc_nuoc=du_lieu.muc_nuoc
    )

    db.add(thiet_bi)
    db.commit()
    db.refresh(thiet_bi)

    return thiet_bi


@app.get("/api/thiet-bi/{ma_thiet_bi}")
def lay_thiet_bi(
    ma_thiet_bi: int,
    nguoi_dung=Depends(nguoi_dung_hien_tai),
    db: Session = Depends(lay_db)
):
    return lay_thiet_bi_cua_toi(db, nguoi_dung, ma_thiet_bi)


@app.put("/api/thiet-bi/{ma_thiet_bi}")
def cap_nhat_thiet_bi(
    ma_thiet_bi: int,
    du_lieu: ThietBiCapNhat,
    nguoi_dung=Depends(nguoi_dung_hien_tai),
    db: Session = Depends(lay_db)
):
    thiet_bi = lay_thiet_bi_cua_toi(db, nguoi_dung, ma_thiet_bi)

    cap_nhat = du_lieu.model_dump(exclude_unset=True)
    cap_nhat.pop("ma_nguoi_dung", None)

    kiem_tra_muc(cap_nhat)

    for ten_truong, gia_tri in cap_nhat.items():
        setattr(thiet_bi, ten_truong, gia_tri)

    if "muc_thuc_an" in cap_nhat:
        kiem_tra_canh_bao_thuc_an(db, thiet_bi)

    db.commit()
    db.refresh(thiet_bi)

    return thiet_bi


@app.delete("/api/thiet-bi/{ma_thiet_bi}")
def xoa_thiet_bi(
    ma_thiet_bi: int,
    nguoi_dung=Depends(nguoi_dung_hien_tai),
    db: Session = Depends(lay_db)
):
    thiet_bi = lay_thiet_bi_cua_toi(db, nguoi_dung, ma_thiet_bi)

    db.delete(thiet_bi)
    db.commit()

    return {"message": "Da xoa thiet bi thanh cong."}


# =========================================================
# LICH CHO AN (chi chu so huu)
# =========================================================

@app.get("/api/lich-cho-an")
def lay_danh_sach_lich_cho_an(
    nguoi_dung=Depends(nguoi_dung_hien_tai),
    db: Session = Depends(lay_db)
):
    return truy_van_cua_toi(db, models.LichChoAn, nguoi_dung).all()


@app.post("/api/lich-cho-an")
def them_lich_cho_an(
    du_lieu: LichChoAnTao,
    nguoi_dung=Depends(nguoi_dung_hien_tai),
    db: Session = Depends(lay_db)
):
    lay_thu_cung_cua_toi(db, nguoi_dung, du_lieu.ma_thu_cung)
    lay_thiet_bi_cua_toi(db, nguoi_dung, du_lieu.ma_thiet_bi)
    kiem_tra_luong(du_lieu.luong_thuc_an)

    lich = models.LichChoAn(
        ma_thu_cung=du_lieu.ma_thu_cung,
        ma_thiet_bi=du_lieu.ma_thiet_bi,
        gio_cho_an=du_lieu.gio_cho_an,
        luong_thuc_an=du_lieu.luong_thuc_an,
        dang_hoat_dong=du_lieu.dang_hoat_dong
    )

    db.add(lich)
    db.commit()
    db.refresh(lich)

    return lich


@app.get("/api/lich-cho-an/{ma_lich}")
def lay_lich_cho_an(
    ma_lich: int,
    nguoi_dung=Depends(nguoi_dung_hien_tai),
    db: Session = Depends(lay_db)
):
    return lay_ban_ghi_cua_toi(
        db, nguoi_dung, models.LichChoAn,
        models.LichChoAn.ma_lich, ma_lich, "lich cho an"
    )


@app.put("/api/lich-cho-an/{ma_lich}")
def cap_nhat_lich_cho_an(
    ma_lich: int,
    du_lieu: LichChoAnCapNhat,
    nguoi_dung=Depends(nguoi_dung_hien_tai),
    db: Session = Depends(lay_db)
):
    lich = lay_ban_ghi_cua_toi(
        db, nguoi_dung, models.LichChoAn,
        models.LichChoAn.ma_lich, ma_lich, "lich cho an"
    )

    cap_nhat = du_lieu.model_dump(exclude_unset=True)

    # Khong cho doi sang thu cung/thiet bi cua nguoi khac
    cap_nhat.pop("ma_thu_cung", None)
    cap_nhat.pop("ma_thiet_bi", None)

    if cap_nhat.get("luong_thuc_an") is not None:
        kiem_tra_luong(cap_nhat["luong_thuc_an"])

    for ten_truong, gia_tri in cap_nhat.items():
        setattr(lich, ten_truong, gia_tri)

    db.commit()
    db.refresh(lich)

    return lich


@app.delete("/api/lich-cho-an/{ma_lich}")
def xoa_lich_cho_an(
    ma_lich: int,
    nguoi_dung=Depends(nguoi_dung_hien_tai),
    db: Session = Depends(lay_db)
):
    lich = lay_ban_ghi_cua_toi(
        db, nguoi_dung, models.LichChoAn,
        models.LichChoAn.ma_lich, ma_lich, "lich cho an"
    )

    db.delete(lich)
    db.commit()

    return {"message": "Da xoa lich cho an thanh cong."}


# =========================================================
# CHO AN NGAY (nguoi dung gui lenh)
# =========================================================

def het_han_lenh_cu(db: Session):
    moc = datetime.now() - timedelta(seconds=THOI_GIAN_HET_HAN_GIAY)

    db.query(models.LichSuChoAn).filter(
        models.LichSuChoAn.trang_thai == "CHO_XU_LY",
        models.LichSuChoAn.thoi_gian_cho_an < moc
    ).update(
        {"trang_thai": "HET_HAN"},
        synchronize_session=False
    )

    db.commit()


@app.post("/api/cho-an-ngay")
def cho_an_ngay(
    du_lieu: ChoAnNgayTao,
    nguoi_dung=Depends(nguoi_dung_hien_tai),
    db: Session = Depends(lay_db)
):
    lay_thu_cung_cua_toi(db, nguoi_dung, du_lieu.ma_thu_cung)
    thiet_bi = lay_thiet_bi_cua_toi(db, nguoi_dung, du_lieu.ma_thiet_bi)

    if thiet_bi.trang_thai != "DANG_KET_NOI":
        raise loi(400, "Thiet bi dang ngat ket noi.")

    kiem_tra_luong(du_lieu.luong_thuc_an)

    if thiet_bi.muc_thuc_an < du_lieu.luong_thuc_an:
        raise loi(400, "Khong du thuc an.")

    het_han_lenh_cu(db)

    lenh_dang_cho = (
        db.query(models.LichSuChoAn)
        .filter(
            models.LichSuChoAn.ma_thiet_bi == du_lieu.ma_thiet_bi,
            models.LichSuChoAn.trang_thai == "CHO_XU_LY"
        )
        .first()
    )

    if lenh_dang_cho is not None:
        raise loi(
            400,
            "Dang co lenh cho an chua xu ly, vui long doi thiet bi."
        )

    lich_su = models.LichSuChoAn(
        ma_thu_cung=du_lieu.ma_thu_cung,
        ma_thiet_bi=du_lieu.ma_thiet_bi,
        luong_thuc_an=du_lieu.luong_thuc_an,
        hinh_thuc="THU_CONG",
        trang_thai="CHO_XU_LY"
    )

    db.add(lich_su)
    db.commit()
    db.refresh(lich_su)

    return {
        "message": "Da tao lenh cho an.",
        "ma_lich_su": lich_su.ma_lich_su,
        "ma_thu_cung": lich_su.ma_thu_cung,
        "ma_thiet_bi": lich_su.ma_thiet_bi,
        "luong_thuc_an": lich_su.luong_thuc_an,
        "hinh_thuc": lich_su.hinh_thuc,
        "trang_thai": lich_su.trang_thai
    }


# =========================================================
# API CHO THIET BI IoT (se khoa bang khoa API o dot sau)
# =========================================================

@app.get("/api/lenh-cho-an/{ma_thiet_bi}")
def lay_lenh_cho_an(
    ma_thiet_bi: int,
    khoa: Optional[str] = Header(default=None, alias="X-Khoa-Thiet-Bi"),
    db: Session = Depends(lay_db)
):
    xac_thuc_thiet_bi(ma_thiet_bi, khoa)

    # Moi lan thiet bi hoi lenh la mot "nhip tim": thiet bi con song
    thiet_bi = (
        db.query(models.ThietBi)
        .filter(models.ThietBi.ma_thiet_bi == ma_thiet_bi)
        .first()
    )

    if thiet_bi is not None:
        thiet_bi.lan_ket_noi_cuoi = datetime.now()

        if thiet_bi.trang_thai != "DANG_KET_NOI":
            thiet_bi.trang_thai = "DANG_KET_NOI"
            da_ket_noi_lai(db, thiet_bi)

        db.commit()

    het_han_lenh_cu(db)

    lenh = (
        db.query(models.LichSuChoAn)
        .filter(
            models.LichSuChoAn.ma_thiet_bi == ma_thiet_bi,
            models.LichSuChoAn.trang_thai == "CHO_XU_LY"
        )
        .order_by(models.LichSuChoAn.ma_lich_su.asc())
        .first()
    )

    if lenh is None:
        return {"co_lenh": False}

    return {
        "co_lenh": True,
        "ma_lich_su": lenh.ma_lich_su,
        "ma_thu_cung": lenh.ma_thu_cung,
        "ma_thiet_bi": lenh.ma_thiet_bi,
        "luong_thuc_an": lenh.luong_thuc_an,
        "hinh_thuc": lenh.hinh_thuc,
        "trang_thai": lenh.trang_thai
    }


@app.put("/api/lenh-cho-an/{ma_lich_su}/hoan-thanh")
def hoan_thanh_lenh_cho_an(
    ma_lich_su: int,
    khoa: Optional[str] = Header(default=None, alias="X-Khoa-Thiet-Bi"),
    db: Session = Depends(lay_db)
):
    lenh = (
        db.query(models.LichSuChoAn)
        .filter(models.LichSuChoAn.ma_lich_su == ma_lich_su)
        .first()
    )

    # Cung mot thong bao 401 cho "khong co lenh" va "sai khoa" (khong cho do ma lenh)
    if lenh is None:
        raise loi(401, "Khoa thiet bi khong hop le.")

    xac_thuc_thiet_bi(lenh.ma_thiet_bi, khoa)

    thiet_bi = (
        db.query(models.ThietBi)
        .filter(models.ThietBi.ma_thiet_bi == lenh.ma_thiet_bi)
        .first()
    )

    if thiet_bi is None:
        raise loi(404, "Khong tim thay thiet bi.")

    if lenh.trang_thai != "CHO_XU_LY":
        raise loi(400, "Lenh nay da duoc xu ly.")

    if thiet_bi.muc_thuc_an < lenh.luong_thuc_an:
        lenh.trang_thai = "THAT_BAI"
        db.commit()
        raise loi(400, "Khong du thuc an.")

    thiet_bi.muc_thuc_an -= lenh.luong_thuc_an
    lenh.trang_thai = "THANH_CONG"

    kiem_tra_canh_bao_thuc_an(db, thiet_bi)

    db.commit()
    db.refresh(lenh)

    return {
        "message": "Cho an thanh cong.",
        "ma_lich_su": lenh.ma_lich_su,
        "luong_thuc_an": lenh.luong_thuc_an,
        "trang_thai": lenh.trang_thai,
        "muc_thuc_an_con_lai": thiet_bi.muc_thuc_an
    }


@app.put("/api/lenh-cho-an/{ma_lich_su}/that-bai")
def bao_lenh_cho_an_that_bai(
    ma_lich_su: int,
    khoa: Optional[str] = Header(default=None, alias="X-Khoa-Thiet-Bi"),
    db: Session = Depends(lay_db)
):
    lenh = (
        db.query(models.LichSuChoAn)
        .filter(models.LichSuChoAn.ma_lich_su == ma_lich_su)
        .first()
    )

    if lenh is None:
        raise loi(401, "Khoa thiet bi khong hop le.")

    xac_thuc_thiet_bi(lenh.ma_thiet_bi, khoa)

    if lenh.trang_thai != "CHO_XU_LY":
        raise loi(400, "Lenh nay da duoc xu ly.")

    lenh.trang_thai = "THAT_BAI"
    db.commit()

    return {
        "message": "Da ghi nhan lenh that bai.",
        "ma_lich_su": lenh.ma_lich_su,
        "trang_thai": lenh.trang_thai
    }


@app.post("/api/du-lieu-thiet-bi")
def nhan_du_lieu_thiet_bi(
    du_lieu: DuLieuThietBiTao,
    khoa: Optional[str] = Header(default=None, alias="X-Khoa-Thiet-Bi"),
    db: Session = Depends(lay_db)
):
    xac_thuc_thiet_bi(du_lieu.ma_thiet_bi, khoa)

    thiet_bi = (
        db.query(models.ThietBi)
        .filter(models.ThietBi.ma_thiet_bi == du_lieu.ma_thiet_bi)
        .first()
    )

    if thiet_bi is None:
        raise loi(404, "Khong tim thay thiet bi.")

    if du_lieu.muc_thuc_an < 0 or du_lieu.muc_thuc_an > 100:
        raise loi(400, "Muc thuc an phai tu 0 den 100.")

    if du_lieu.muc_nuoc < 0 or du_lieu.muc_nuoc > 100:
        raise loi(400, "Muc nuoc phai tu 0 den 100.")

    thiet_bi.muc_thuc_an = du_lieu.muc_thuc_an
    thiet_bi.muc_nuoc = du_lieu.muc_nuoc
    thiet_bi.trang_thai = du_lieu.trang_thai_thiet_bi

    if du_lieu.trang_thai_thiet_bi == "DANG_KET_NOI":
        thiet_bi.lan_ket_noi_cuoi = datetime.now()

    du_lieu_moi = models.DuLieuThietBi(
        ma_thiet_bi=du_lieu.ma_thiet_bi,
        muc_thuc_an=du_lieu.muc_thuc_an,
        muc_nuoc=du_lieu.muc_nuoc,
        trang_thai_thiet_bi=du_lieu.trang_thai_thiet_bi
    )

    db.add(du_lieu_moi)

    danh_sach_canh_bao = []

    danh_sach_canh_bao.extend(
        kiem_tra_canh_bao_thuc_an(db, thiet_bi)
    )

    if du_lieu.muc_nuoc < 20:
        db.add(models.CanhBao(
            ma_thiet_bi=du_lieu.ma_thiet_bi,
            loai_canh_bao="NUOC_THAP",
            noi_dung="Muc nuoc dang o muc thap."
        ))
        danh_sach_canh_bao.append("Canh bao: Muc nuoc thap.")

    if du_lieu.trang_thai_thiet_bi == "NGAT_KET_NOI":
        if bao_mat_ket_noi(db, thiet_bi):
            danh_sach_canh_bao.append("Canh bao: Thiet bi mat ket noi.")
    else:
        da_ket_noi_lai(db, thiet_bi)

    db.commit()
    db.refresh(du_lieu_moi)

    return {
        "message": "Da nhan du lieu thiet bi.",
        "ma_du_lieu": du_lieu_moi.ma_du_lieu,
        "muc_thuc_an": du_lieu_moi.muc_thuc_an,
        "muc_nuoc": du_lieu_moi.muc_nuoc,
        "trang_thai_thiet_bi": du_lieu_moi.trang_thai_thiet_bi,
        "canh_bao": danh_sach_canh_bao
    }


@app.get("/api/iot/thiet-bi/{ma_thiet_bi}")
def iot_lay_thiet_bi(
    ma_thiet_bi: int,
    khoa: Optional[str] = Header(default=None, alias="X-Khoa-Thiet-Bi"),
    db: Session = Depends(lay_db)
):
    xac_thuc_thiet_bi(ma_thiet_bi, khoa)

    thiet_bi = (
        db.query(models.ThietBi)
        .filter(models.ThietBi.ma_thiet_bi == ma_thiet_bi)
        .first()
    )

    if thiet_bi is None:
        raise loi(404, "Khong tim thay thiet bi.")

    # Chi tra cac truong thiet bi can, khong tra thong tin chu so huu
    return {
        "ma_thiet_bi": thiet_bi.ma_thiet_bi,
        "ten_thiet_bi": thiet_bi.ten_thiet_bi,
        "ma_thiet_bi_iot": thiet_bi.ma_thiet_bi_iot,
        "trang_thai": thiet_bi.trang_thai,
        "muc_thuc_an": thiet_bi.muc_thuc_an,
        "muc_nuoc": thiet_bi.muc_nuoc
    }


# =========================================================
# LICH SU, DU LIEU CAM BIEN, CANH BAO (chi chu so huu)
# =========================================================

@app.get("/api/lich-su-cho-an")
def lay_danh_sach_lich_su_cho_an(
    nguoi_dung=Depends(nguoi_dung_hien_tai),
    db: Session = Depends(lay_db)
):
    het_han_lenh_cu(db)

    return (
        truy_van_cua_toi(db, models.LichSuChoAn, nguoi_dung)
        .order_by(models.LichSuChoAn.ma_lich_su.desc())
        .all()
    )


@app.get("/api/lich-su-cho-an/{ma_lich_su}")
def lay_lich_su_cho_an(
    ma_lich_su: int,
    nguoi_dung=Depends(nguoi_dung_hien_tai),
    db: Session = Depends(lay_db)
):
    return lay_ban_ghi_cua_toi(
        db, nguoi_dung, models.LichSuChoAn,
        models.LichSuChoAn.ma_lich_su, ma_lich_su, "lich su cho an"
    )


@app.get("/api/du-lieu-thiet-bi")
def lay_du_lieu_thiet_bi(
    nguoi_dung=Depends(nguoi_dung_hien_tai),
    db: Session = Depends(lay_db)
):
    return (
        truy_van_cua_toi(db, models.DuLieuThietBi, nguoi_dung)
        .order_by(models.DuLieuThietBi.ma_du_lieu.desc())
        .limit(200)
        .all()
    )


@app.get("/api/canh-bao")
def lay_danh_sach_canh_bao(
    nguoi_dung=Depends(nguoi_dung_hien_tai),
    db: Session = Depends(lay_db)
):
    return (
        truy_van_cua_toi(db, models.CanhBao, nguoi_dung)
        .order_by(models.CanhBao.ma_canh_bao.desc())
        .all()
    )


@app.get("/api/canh-bao/{ma_canh_bao}")
def lay_canh_bao(
    ma_canh_bao: int,
    nguoi_dung=Depends(nguoi_dung_hien_tai),
    db: Session = Depends(lay_db)
):
    return lay_ban_ghi_cua_toi(
        db, nguoi_dung, models.CanhBao,
        models.CanhBao.ma_canh_bao, ma_canh_bao, "canh bao"
    )


@app.put("/api/canh-bao/{ma_canh_bao}/da-doc")
def danh_dau_canh_bao_da_doc(
    ma_canh_bao: int,
    nguoi_dung=Depends(nguoi_dung_hien_tai),
    db: Session = Depends(lay_db)
):
    canh_bao = lay_ban_ghi_cua_toi(
        db, nguoi_dung, models.CanhBao,
        models.CanhBao.ma_canh_bao, ma_canh_bao, "canh bao"
    )

    canh_bao.da_doc = True

    db.commit()
    db.refresh(canh_bao)

    return {
        "message": "Da danh dau canh bao da doc.",
        "ma_canh_bao": canh_bao.ma_canh_bao,
        "da_doc": canh_bao.da_doc
    }