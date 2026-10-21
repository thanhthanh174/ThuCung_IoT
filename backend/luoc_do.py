import re
from datetime import date
from pydantic import BaseModel
from typing import Optional
from pydantic import BaseModel, field_validator


class ThuCungTao(BaseModel):
    ma_nguoi_dung: int
    ten_thu_cung: str
    loai: str
    giong: Optional[str] = None
    gioi_tinh: Optional[str] = None
    ngay_sinh: Optional[date] = None
    can_nang: Optional[float] = None
    anh: Optional[str] = None
    ghi_chu: Optional[str] = None


class ThuCungCapNhat(BaseModel):
    ten_thu_cung: Optional[str] = None
    loai: Optional[str] = None
    giong: Optional[str] = None
    gioi_tinh: Optional[str] = None
    ngay_sinh: Optional[date] = None
    can_nang: Optional[float] = None
    anh: Optional[str] = None
    ghi_chu: Optional[str] = None
class NguoiDungTao(BaseModel):
    ho_ten: str
    email: str
    mat_khau: str
class ThietBiTao(BaseModel):
    ma_nguoi_dung: int
    ten_thiet_bi: str
    ma_thiet_bi_iot: str
    trang_thai: Optional[str] = "NGAT_KET_NOI"
    muc_thuc_an: Optional[float] = 100
    muc_nuoc: Optional[float] = 100


class ThietBiCapNhat(BaseModel):
    ten_thiet_bi: Optional[str] = None
    trang_thai: Optional[str] = None
    muc_thuc_an: Optional[float] = None
    muc_nuoc: Optional[float] = None
def kiem_tra_gio(gia_tri):
    if gia_tri is None:
        return gia_tri

    if not re.fullmatch(
        r"([01]\d|2[0-3]):[0-5]\d",
        gia_tri
    ):
        raise ValueError(
            "Gio phai co dang HH:MM, vi du 07:30"
        )

    return gia_tri


class LichChoAnTao(BaseModel):
    ma_thu_cung: int
    ma_thiet_bi: int
    gio_cho_an: str
    luong_thuc_an: float
    dang_hoat_dong: Optional[bool] = True

    @field_validator("gio_cho_an")
    @classmethod
    def gio_hop_le(cls, gia_tri):
        return kiem_tra_gio(gia_tri)


class LichChoAnCapNhat(BaseModel):
    gio_cho_an: Optional[str] = None
    luong_thuc_an: Optional[float] = None
    dang_hoat_dong: Optional[bool] = None

    @field_validator("gio_cho_an")
    @classmethod
    def gio_hop_le(cls, gia_tri):
        return kiem_tra_gio(gia_tri)
class ChoAnNgayTao(BaseModel):
    ma_thu_cung: int
    ma_thiet_bi: int
    luong_thuc_an: float


class LichSuChoAnTao(BaseModel):
    ma_thu_cung: int
    ma_thiet_bi: int
    luong_thuc_an: float
    hinh_thuc: str
    trang_thai: Optional[str] = "THANH_CONG"
class DuLieuThietBiTao(BaseModel):

    ma_thiet_bi: int

    muc_thuc_an: float

    muc_nuoc: float

    trang_thai_thiet_bi: str

class DangNhap(BaseModel):
    email: str
    mat_khau: str