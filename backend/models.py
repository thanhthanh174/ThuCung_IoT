from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from backend.database import Base


class NguoiDung(Base):
    __tablename__ = "nguoi_dung"

    ma_nguoi_dung = Column(Integer, primary_key=True, index=True)
    ho_ten = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    mat_khau = Column(String(255), nullable=False)

    thu_cungs = relationship("ThuCung", back_populates="nguoi_dung")
    thiet_bis = relationship("ThietBi", back_populates="nguoi_dung")


class ThuCung(Base):
    __tablename__ = "thu_cung"

    ma_thu_cung = Column(Integer, primary_key=True, index=True)
    ma_nguoi_dung = Column(
        Integer,
        ForeignKey("nguoi_dung.ma_nguoi_dung"),
        nullable=False
    )

    ten_thu_cung = Column(String(100), nullable=False)
    loai = Column(String(50), nullable=False)
    giong = Column(String(100))
    gioi_tinh = Column(String(20))
    ngay_sinh = Column(Date)
    can_nang = Column(Float)
    anh = Column(String(255))
    ghi_chu = Column(String(500))

    nguoi_dung = relationship(
        "NguoiDung",
        back_populates="thu_cungs"
    )

    lich_cho_ans = relationship(
        "LichChoAn",
        back_populates="thu_cung"
    )

    lich_su_cho_ans = relationship(
        "LichSuChoAn",
        back_populates="thu_cung"
    )


class ThietBi(Base):
    __tablename__ = "thiet_bi"

    ma_thiet_bi = Column(
        Integer,
        primary_key=True,
        index=True
    )

    ma_nguoi_dung = Column(
        Integer,
        ForeignKey("nguoi_dung.ma_nguoi_dung"),
        nullable=False
    )

    ten_thiet_bi = Column(
        String(100),
        nullable=False
    )

    ma_thiet_bi_iot = Column(
        String(100),
        unique=True,
        nullable=False
    )

    trang_thai = Column(
        String(30),
        default="NGAT_KET_NOI"
    )

    muc_thuc_an = Column(
        Float,
        default=100
    )

    muc_nuoc = Column(
        Float,
        default=100
    )

    lan_ket_noi_cuoi = Column(DateTime)

    ngay_tao = Column(
        DateTime,
        default=datetime.now
    )

    nguoi_dung = relationship(
        "NguoiDung",
        back_populates="thiet_bis"
    )

    lich_cho_ans = relationship(
        "LichChoAn",
        back_populates="thiet_bi"
    )

    lich_su_cho_ans = relationship(
        "LichSuChoAn",
        back_populates="thiet_bi"
    )

    canh_baos = relationship(
        "CanhBao",
        back_populates="thiet_bi"
    )


class LichChoAn(Base):
    __tablename__ = "lich_cho_an"

    ma_lich = Column(
        Integer,
        primary_key=True,
        index=True
    )

    ma_thu_cung = Column(
        Integer,
        ForeignKey("thu_cung.ma_thu_cung"),
        nullable=False
    )

    ma_thiet_bi = Column(
        Integer,
        ForeignKey("thiet_bi.ma_thiet_bi"),
        nullable=False
    )

    gio_cho_an = Column(
        String(10),
        nullable=False
    )

    luong_thuc_an = Column(
        Float,
        nullable=False
    )

    dang_hoat_dong = Column(
        Boolean,
        default=True
    )

    ngay_tao = Column(
        DateTime,
        default=datetime.now
    )

    thu_cung = relationship(
        "ThuCung",
        back_populates="lich_cho_ans"
    )

    thiet_bi = relationship(
        "ThietBi",
        back_populates="lich_cho_ans"
    )


class LichSuChoAn(Base):
    __tablename__ = "lich_su_cho_an"

    ma_lich_su = Column(
        Integer,
        primary_key=True,
        index=True
    )

    ma_thu_cung = Column(
        Integer,
        ForeignKey("thu_cung.ma_thu_cung"),
        nullable=False
    )

    ma_thiet_bi = Column(
        Integer,
        ForeignKey("thiet_bi.ma_thiet_bi"),
        nullable=False
    )

    thoi_gian_cho_an = Column(
        DateTime,
        default=datetime.now
    )

    luong_thuc_an = Column(
        Float,
        nullable=False
    )

    hinh_thuc = Column(
        String(20),
        nullable=False
    )

    trang_thai = Column(
        String(20),
        default="CHO_XU_LY"
    )

    thu_cung = relationship(
        "ThuCung",
        back_populates="lich_su_cho_ans"
    )

    thiet_bi = relationship(
        "ThietBi",
        back_populates="lich_su_cho_ans"
    )


class DuLieuThietBi(Base):
    __tablename__ = "du_lieu_thiet_bi"

    ma_du_lieu = Column(
        Integer,
        primary_key=True,
        index=True
    )

    ma_thiet_bi = Column(
        Integer,
        ForeignKey("thiet_bi.ma_thiet_bi"),
        nullable=False
    )

    muc_thuc_an = Column(
        Float,
        nullable=False
    )

    muc_nuoc = Column(
        Float,
        nullable=False
    )

    trang_thai_thiet_bi = Column(
        String(30)
    )

    thoi_gian_ghi_nhan = Column(
        DateTime,
        default=datetime.now
    )

    thiet_bi = relationship(
        "ThietBi"
    )


class CanhBao(Base):
    __tablename__ = "canh_bao"

    ma_canh_bao = Column(
        Integer,
        primary_key=True,
        index=True
    )

    ma_thiet_bi = Column(
        Integer,
        ForeignKey("thiet_bi.ma_thiet_bi"),
        nullable=False
    )

    loai_canh_bao = Column(
        String(50),
        nullable=False
    )

    noi_dung = Column(
        String(255),
        nullable=False
    )

    da_doc = Column(
        Boolean,
        default=False
    )

    thoi_gian_tao = Column(
        DateTime,
        default=datetime.now
    )

    thiet_bi = relationship(
        "ThietBi",
        back_populates="canh_baos"
    )