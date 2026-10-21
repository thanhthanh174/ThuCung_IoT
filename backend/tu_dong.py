import traceback
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from backend.canh_bao import kiem_tra_canh_bao_thuc_an, bao_mat_ket_noi
from backend.database import SessionLocal
from backend.models import LichChoAn, LichSuChoAn, ThietBi


def thuc_hien_cho_an_tu_dong():
    db: Session = SessionLocal()

    try:
        gio_hien_tai = datetime.now().strftime("%H:%M")

        lich_cho_an = (
            db.query(LichChoAn)
            .filter(
                LichChoAn.gio_cho_an == gio_hien_tai,
                LichChoAn.dang_hoat_dong == True
            )
            .all()
        )

        for lich in lich_cho_an:
            thiet_bi = (
                db.query(ThietBi)
                .filter(
                    ThietBi.ma_thiet_bi == lich.ma_thiet_bi
                )
                .first()
            )

            print(f"[LICH] {gio_hien_tai} - co {len(lich_cho_an)} lich khop")

            if thiet_bi is None:
                continue

            if thiet_bi.muc_thuc_an < lich.luong_thuc_an:
                print(
                    f"[CANH BAO] Thiet bi {thiet_bi.ma_thiet_bi} "
                    f"khong du thuc an."
                )
                continue

            if thiet_bi.muc_thuc_an < lich.luong_thuc_an:
                print(
                    f"[CANH BAO] Thiet bi {thiet_bi.ma_thiet_bi} "
                    f"khong du thuc an."
                )
                kiem_tra_canh_bao_thuc_an(db, thiet_bi)   
                continue

            thiet_bi.muc_thuc_an -= lich.luong_thuc_an

            kiem_tra_canh_bao_thuc_an(db, thiet_bi)      

            lich_su = LichSuChoAn(
                ma_thu_cung=lich.ma_thu_cung,
                ma_thiet_bi=lich.ma_thiet_bi,
                luong_thuc_an=lich.luong_thuc_an,
                hinh_thuc="TU_DONG",
                trang_thai="THANH_CONG"
            )

            db.add(lich_su)

            print(
                f"[TU DONG] Cho thu cung {lich.ma_thu_cung} "
                f"an {lich.luong_thuc_an}g."
            )

        db.commit()

    except Exception as loi:
        db.rollback()
        print("[LOI] Cho an tu dong:", loi)
        traceback.print_exc()

    finally:
        db.close()

NGUONG_MAT_KET_NOI_GIAY = 30


def kiem_tra_mat_ket_noi():
    db: Session = SessionLocal()

    try:
        moc = datetime.now() - timedelta(
            seconds=NGUONG_MAT_KET_NOI_GIAY
        )

        danh_sach = (
            db.query(ThietBi)
            .filter(ThietBi.trang_thai == "DANG_KET_NOI")
            .all()
        )

        for thiet_bi in danh_sach:
            if (
                thiet_bi.lan_ket_noi_cuoi is None
                or thiet_bi.lan_ket_noi_cuoi < moc
            ):
                thiet_bi.trang_thai = "NGAT_KET_NOI"
                bao_mat_ket_noi(db, thiet_bi)

                print(
                    f"[MAT KET NOI] Thiet bi {thiet_bi.ma_thiet_bi} "
                    f"khong gui tin hieu qua "
                    f"{NGUONG_MAT_KET_NOI_GIAY} giay."
                )

        db.commit()

    except Exception as loi:
        db.rollback()
        print("[LOI] Kiem tra mat ket noi:", loi)

    finally:
        db.close()
bo_lap_lich = BackgroundScheduler()


def khoi_dong_bo_lap_lich():
    bo_lap_lich.add_job(
        thuc_hien_cho_an_tu_dong,
        "cron",
        second=0,
        id="cho_an_tu_dong",
        replace_existing=True,
        misfire_grace_time=30
    )

    bo_lap_lich.add_job(
        kiem_tra_mat_ket_noi,
        "interval",
        seconds=10,
        id="kiem_tra_mat_ket_noi",
        replace_existing=True
    )
    
    bo_lap_lich.start()

    print("Bo lap lich cho an tu dong da khoi dong.")