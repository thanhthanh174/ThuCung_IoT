import os
import os
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

API_URL = "http://127.0.0.1:8000"
MA_THIET_BI = 1

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

KHOA_THIET_BI = os.getenv("KHOA_THIET_BI", "")

if not KHOA_THIET_BI:
    print("Canh bao: chua co KHOA_THIET_BI trong iot/.env")

phien = requests.Session()
phien.headers.update({"X-Khoa-Thiet-Bi": KHOA_THIET_BI})

def lay_thong_tin_thiet_bi():
    try:
        response = phien.get(
            f"{API_URL}/api/iot/thiet-bi/{MA_THIET_BI}"
        )

        if response.status_code == 200:
            return response.json()

        print("Khong lay duoc thong tin thiet bi.")
        print("Ma loi:", response.status_code)
        print(response.text)

        return None

    except requests.exceptions.RequestException as loi:
        print("Khong ket noi duoc FastAPI.")
        print("Chi tiet:", loi)

        return None

def gui_du_lieu_cam_bien(
    muc_thuc_an,
    muc_nuoc,
    trang_thai="DANG_KET_NOI"
):
    du_lieu = {
        "ma_thiet_bi": MA_THIET_BI,
        "muc_thuc_an": muc_thuc_an,
        "muc_nuoc": muc_nuoc,
        "trang_thai_thiet_bi": trang_thai
    }

    try:
        response = phien.post(
            f"{API_URL}/api/du-lieu-thiet-bi",
            json=du_lieu
        )

        if response.status_code == 200:
            ket_qua = response.json()

            print()
            print("Da gui du lieu cam bien thanh cong.")

            if "canh_bao" in ket_qua:
                if ket_qua["canh_bao"]:
                    print("Canh bao:")

                    for canh_bao in ket_qua["canh_bao"]:
                        print(f"- {canh_bao}")

                else:
                    print("Khong co canh bao.")

            return ket_qua

        print("Gui du lieu that bai.")
        print("Ma loi:", response.status_code)
        print(response.text)

    except requests.exceptions.RequestException as loi:
        print("Khong ket noi duoc FastAPI.")
        print("Chi tiet:", loi)


# ============================================================
# HIEN THI THONG TIN
# ============================================================

def hien_thi_thong_tin(
    muc_thuc_an,
    muc_nuoc,
    trang_thai
):
    print()
    print("-" * 50)
    print(
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"
    )
    print(f"Thuc an: {muc_thuc_an}%")
    print(f"Nuoc: {muc_nuoc}%")
    print(f"Trang thai thiet bi: {trang_thai}")
    print("-" * 50)
    print()


# ============================================================
# MO PHONG MOTOR NHA THUC AN
# ============================================================

def mo_phong_nha_thuc_an(luong_thuc_an):
    print()
    print("=" * 50)
    print("THIET BI DANG THUC HIEN CHO AN")
    print("=" * 50)

    print(f"Luong thuc an: {luong_thuc_an}g")
    print("Motor dang quay...")

    time.sleep(1)

    print("Khay thuc an dang mo...")

    time.sleep(1)

    print(f"Da nha {luong_thuc_an}g thuc an.")
    print("Cho an thanh cong.")

    print("=" * 50)
    print()


# ============================================================
# KIEM TRA LENH CHO AN TU FASTAPI
# ============================================================

def lay_lenh_cho_an():
    try:
        response = phien.get(
            f"{API_URL}/api/lenh-cho-an/{MA_THIET_BI}"
        )

        if response.status_code == 200:
            return response.json()

        print()
        print("Khong lay duoc lenh cho an.")
        print("Ma loi:", response.status_code)
        print(response.text)

        return None

    except requests.exceptions.RequestException as loi:
        print()
        print("Khong ket noi duoc FastAPI.")
        print("Chi tiet:", loi)

        return None


# ============================================================
# BAO FASTAPI LENH DA HOAN THANH
# ============================================================

def bao_lenh_hoan_thanh(ma_lich_su):
    try:
        response = phien.put(
            f"{API_URL}/api/lenh-cho-an/"
            f"{ma_lich_su}/hoan-thanh"
        )

        if response.status_code == 200:
            ket_qua = response.json()

            print()
            print("FastAPI da ghi nhan cho an thanh cong.")
            print(
                f"Ma lich su: "
                f"{ket_qua['ma_lich_su']}"
            )
            print(
                f"Thuc an con lai: "
                f"{ket_qua['muc_thuc_an_con_lai']}%"
            )

            return ket_qua

        print()
        print("Bao hoan thanh that bai.")
        print("Ma loi:", response.status_code)
        print(response.text)

        return None

    except requests.exceptions.RequestException as loi:
        print()
        print("Khong ket noi duoc FastAPI.")
        print("Chi tiet:", loi)

        return None

def bao_lenh_that_bai(ma_lich_su):
    try:
        phien.put(
            f"{API_URL}/api/lenh-cho-an/"
            f"{ma_lich_su}/that-bai"
        )
        print("Da bao FastAPI: lenh cho an that bai.")

    except requests.exceptions.RequestException as loi:
        print("Khong ket noi duoc FastAPI.")
        print("Chi tiet:", loi)

def chay_tu_dong_nhan_lenh():
    print()
    print("Dang tu dong cho lenh cho an...")
    print("Bam Ctrl + C de dung.")

    try:
        while True:
            lenh = lay_lenh_cho_an()

            if lenh and lenh.get("co_lenh", False):
                xu_ly_lenh_cho_an()

            time.sleep(3)

    except KeyboardInterrupt:
        print()
        print("Da dung che do tu dong.")

def dong_bo_tu_server():
    thiet_bi = lay_thong_tin_thiet_bi()

    if thiet_bi is None:
        return None

    return (
        float(thiet_bi["muc_thuc_an"]),
        float(thiet_bi["muc_nuoc"]),
        thiet_bi["trang_thai"]
    )

# ============================================================
# XU LY LENH CHO AN
# ============================================================

def xu_ly_lenh_cho_an():
    lenh = lay_lenh_cho_an()

    if lenh is None:
        return False

    if not lenh.get("co_lenh", False):
        print()
        print("Hien tai khong co lenh cho an.")
        return False

    ma_lich_su = lenh["ma_lich_su"]
    luong_thuc_an = float(
        lenh["luong_thuc_an"]
    )

    print()
    print("=" * 50)
    print("NHAN DUOC LENH CHO AN TU FASTAPI")
    print("=" * 50)
    print(f"Ma lich su: {ma_lich_su}")
    print(f"Ma thu cung: {lenh['ma_thu_cung']}")
    print(f"Luong thuc an: {luong_thuc_an}g")
    print(f"Trang thai: {lenh['trang_thai']}")
    print("=" * 50)

    # Lay thong tin thiet bi moi nhat
    thiet_bi = lay_thong_tin_thiet_bi()

    if thiet_bi is None:
        return False

    muc_thuc_an = float(
        thiet_bi["muc_thuc_an"]
    )

    muc_nuoc = float(
        thiet_bi["muc_nuoc"]
    )

    trang_thai = thiet_bi["trang_thai"]

    if trang_thai != "DANG_KET_NOI":
        print()
        print("Thiet bi dang ngat ket noi.")
        bao_lenh_that_bai(ma_lich_su)
        return False

    if muc_thuc_an < luong_thuc_an:
        print()
        print("Khong du thuc an de cho an.")
        bao_lenh_that_bai(ma_lich_su)
        return False

    # Mo phong motor
    mo_phong_nha_thuc_an(
        luong_thuc_an
    )

    # Bao FastAPI da cho an thanh cong
    ket_qua = bao_lenh_hoan_thanh(
        ma_lich_su
    )

    if ket_qua is None:
        return False

    # Lay muc thuc an moi
    muc_thuc_an_moi = float(
        ket_qua["muc_thuc_an_con_lai"]
    )

    # Gui lai du lieu cam bien
    gui_du_lieu_cam_bien(
        muc_thuc_an_moi,
        muc_nuoc,
        "DANG_KET_NOI"
    )

    hien_thi_thong_tin(
        muc_thuc_an_moi,
        muc_nuoc,
        "DANG_KET_NOI"
    )

    return True


# ============================================================
# MO PHONG CAM BIEN
# ============================================================

def mo_phong_cam_bien():

    print("=" * 50)
    print("SMART PET STATION - IOT SIMULATOR")
    print("=" * 50)

    thiet_bi = lay_thong_tin_thiet_bi()

    if thiet_bi is None:
        print()
        print("Khong the khoi dong IoT Simulator.")
        print(
            "Hay kiem tra FastAPI co dang chay "
            "hay khong."
        )
        return

    muc_thuc_an = float(
        thiet_bi["muc_thuc_an"]
    )

    muc_nuoc = float(
        thiet_bi["muc_nuoc"]
    )

    trang_thai = thiet_bi["trang_thai"]

    print()
    print(
        f"Thuc an hien tai: "
        f"{muc_thuc_an}%"
    )

    print(
        f"Nuoc hien tai: "
        f"{muc_nuoc}%"
    )

    print(
        f"Trang thai: "
        f"{trang_thai}"
    )

    print()

    while True:

        print("=" * 50)
        print("MENU IOT SIMULATOR")
        print("=" * 50)

        print("1. Giam thuc an")
        print("2. Giam nuoc")
        print("3. Gui trang thai ket noi")
        print("4. Mo phong ngat ket noi")
        print("5. Mo phong cho an")
        print("6. Kiem tra lenh cho an tu FastAPI")
        print("7. Tu dong nhan lenh cho an")
        print("8. Thoat")

        print()

        lua_chon = input(
            "Chon chuc nang: "
        ).strip()

        # ====================================================
        # 1. GIAM THUC AN
        # ====================================================

        if lua_chon == "1":

            try:
                muc_giam = float(
                    input(
                        "Nhap phan tram thuc an "
                        "muon giam: "
                    )
                )

                if muc_giam < 0:
                    print(
                        "So luong khong duoc am."
                    )
                    continue

                muc_thuc_an = max(
                    0,
                    muc_thuc_an - muc_giam
                )

                trang_thai = "DANG_KET_NOI"

                print()
                print(
                    f"Thuc an con lai: "
                    f"{muc_thuc_an}%"
                )

                gui_du_lieu_cam_bien(
                    muc_thuc_an,
                    muc_nuoc,
                    trang_thai
                )

                hien_thi_thong_tin(
                    muc_thuc_an,
                    muc_nuoc,
                    trang_thai
                )

            except ValueError:
                print(
                    "Vui long nhap mot so hop le."
                )

        # ====================================================
        # 2. GIAM NUOC
        # ====================================================

        elif lua_chon == "2":

            try:
                muc_giam = float(
                    input(
                        "Nhap phan tram nuoc "
                        "muon giam: "
                    )
                )

                if muc_giam < 0:
                    print(
                        "So luong khong duoc am."
                    )
                    continue

                muc_nuoc = max(
                    0,
                    muc_nuoc - muc_giam
                )

                trang_thai = "DANG_KET_NOI"

                print()
                print(
                    f"Nuoc con lai: "
                    f"{muc_nuoc}%"
                )

                gui_du_lieu_cam_bien(
                    muc_thuc_an,
                    muc_nuoc,
                    trang_thai
                )

                hien_thi_thong_tin(
                    muc_thuc_an,
                    muc_nuoc,
                    trang_thai
                )

            except ValueError:
                print(
                    "Vui long nhap mot so hop le."
                )

        # ====================================================
        # 3. GUI TRANG THAI KET NOI
        # ====================================================

        elif lua_chon == "3":

            trang_thai = "DANG_KET_NOI"

            gui_du_lieu_cam_bien(
                muc_thuc_an,
                muc_nuoc,
                trang_thai
            )

            print()
            print(
                "Da gui trang thai "
                "DANG_KET_NOI."
            )

            hien_thi_thong_tin(
                muc_thuc_an,
                muc_nuoc,
                trang_thai
            )

        # ====================================================
        # 4. NGAT KET NOI
        # ====================================================

        elif lua_chon == "4":

            trang_thai = "NGAT_KET_NOI"

            gui_du_lieu_cam_bien(
                muc_thuc_an,
                muc_nuoc,
                trang_thai
            )

            print()
            print(
                "Da mo phong thiet bi "
                "NGAT_KET_NOI."
            )

            hien_thi_thong_tin(
                muc_thuc_an,
                muc_nuoc,
                trang_thai
            )

        # ====================================================
        # 5. CHO AN THU CONG TRONG SIMULATOR
        # ====================================================

        elif lua_chon == "5":

            try:
                luong_thuc_an = float(
                    input(
                        "Nhap luong thuc an "
                        "muon nha (g): "
                    )
                )

                if luong_thuc_an <= 0:
                    print(
                        "Luong thuc an phai "
                        "lon hon 0."
                    )
                    continue

                if luong_thuc_an > muc_thuc_an:
                    print()
                    print(
                        "Khong du thuc an "
                        "trong thiet bi."
                    )
                    continue

                mo_phong_nha_thuc_an(
                    luong_thuc_an
                )

                # Mo phong don gian:
                # 1g thuc an = 1% muc thuc an
                muc_thuc_an = max(
                    0,
                    muc_thuc_an - luong_thuc_an
                )

                trang_thai = "DANG_KET_NOI"

                gui_du_lieu_cam_bien(
                    muc_thuc_an,
                    muc_nuoc,
                    trang_thai
                )

                hien_thi_thong_tin(
                    muc_thuc_an,
                    muc_nuoc,
                    trang_thai
                )

            except ValueError:
                print(
                    "Vui long nhap mot so hop le."
                )

        # ====================================================
        # 6. KIEM TRA LENH TU FASTAPI
        # ====================================================

        elif lua_chon == "6":

            xu_ly_lenh_cho_an()
            ket_qua = dong_bo_tu_server()

            if ket_qua is not None:
                muc_thuc_an, muc_nuoc, trang_thai = ket_qua

        elif lua_chon == "7":

            chay_tu_dong_nhan_lenh()

            ket_qua = dong_bo_tu_server()

            if ket_qua is not None:
                muc_thuc_an, muc_nuoc, trang_thai = ket_qua

        # ====================================================
        # 8. THOAT
        # ====================================================

        elif lua_chon == "8":

            print()
            print(
                "Da thoat IoT Simulator."
            )

            break

        else:

            print()
            print(
                "Lua chon khong hop le."
            )

            print(
                "Vui long chon tu 1 den 8."
            )


# ============================================================
# CHAY CHUONG TRINH
# ============================================================

if __name__ == "__main__":
    mo_phong_cam_bien()