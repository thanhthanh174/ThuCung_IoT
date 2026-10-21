from sqlalchemy.orm import Session

from backend import models


NGUONG_THUC_AN_THAP = 50
NGUONG_NUOC_THAP = 20

def tao_canh_bao_neu_chua_co(
    db: Session,
    ma_thiet_bi: int,
    loai_canh_bao: str,
    noi_dung: str
):
    # Neu da co canh bao cung loai chua doc thi khong tao them
    da_co = (
        db.query(models.CanhBao)
        .filter(
            models.CanhBao.ma_thiet_bi == ma_thiet_bi,
            models.CanhBao.loai_canh_bao == loai_canh_bao,
            models.CanhBao.da_doc == False
        )
        .first()
    )

    if da_co is not None:
        return False

    db.add(
        models.CanhBao(
            ma_thiet_bi=ma_thiet_bi,
            loai_canh_bao=loai_canh_bao,
            noi_dung=noi_dung
        )
    )
    db.flush()

    return True


def dong_canh_bao(
    db: Session,
    ma_thiet_bi: int,
    cac_loai: list
):
    # Tu dong danh dau da doc khi van de da het
    (
        db.query(models.CanhBao)
        .filter(
            models.CanhBao.ma_thiet_bi == ma_thiet_bi,
            models.CanhBao.loai_canh_bao.in_(cac_loai),
            models.CanhBao.da_doc == False
        )
        .update(
            {"da_doc": True},
            synchronize_session=False
        )
    )


def kiem_tra_canh_bao_thuc_an(
    db: Session,
    thiet_bi
):
    """
    Goi moi khi muc thuc an thay doi.
    Ham nay KHONG commit, noi goi tu commit.
    Tra ve danh sach canh bao MOI vua tao.
    """

    moi = []

    muc = thiet_bi.muc_thuc_an
    ma = thiet_bi.ma_thiet_bi

    if muc <= 0:
        if tao_canh_bao_neu_chua_co(
            db, ma, "HET_THUC_AN",
            "Thiet bi da het thuc an, hay nap them."
        ):
            moi.append("Canh bao: Thiet bi da het thuc an.")

        dong_canh_bao(db, ma, ["THUC_AN_THAP"])

    elif muc < NGUONG_THUC_AN_THAP:
        if tao_canh_bao_neu_chua_co(
            db, ma, "THUC_AN_THAP",
            f"Muc thuc an con {muc:g} phan tram, sap het."
        ):
            moi.append("Canh bao: Muc thuc an thap.")

        dong_canh_bao(db, ma, ["HET_THUC_AN"])

    else:
        dong_canh_bao(
            db, ma, ["THUC_AN_THAP", "HET_THUC_AN"]
        )

    return moi

def bao_mat_ket_noi(db: Session, thiet_bi):
    """Tao canh bao mat ket noi (khong tao trung). Tra ve True neu vua tao moi."""
    return tao_canh_bao_neu_chua_co(
        db,
        thiet_bi.ma_thiet_bi,
        "MAT_KET_NOI",
        "Thiet bi mat ket noi, khong nhan duoc tin hieu."
    )


def da_ket_noi_lai(db: Session, thiet_bi):
    """Thiet bi online tro lai: tu dong dong canh bao mat ket noi."""
    dong_canh_bao(db, thiet_bi.ma_thiet_bi, ["MAT_KET_NOI"])