import base64
import json
import os
import time
import uuid

import jwt
import pytest
import requests

from backend.bao_mat import tao_khoa_thiet_bi

API = os.getenv("API_URL", "http://127.0.0.1:8000")
MAT_KHAU = "MatKhau@123"
HEADER_KHOA = "X-Khoa-Thiet-Bi"

# Ham tro giup
def goi(phuong_thuc, duong_dan, token=None, khoa=None, **kwargs):
    tieu_de = {}

    if token:
        tieu_de["Authorization"] = f"Bearer {token}"

    if khoa is not None:
        tieu_de[HEADER_KHOA] = khoa

    return requests.request(
        phuong_thuc,
        API + duong_dan,
        headers=tieu_de,
        timeout=10,
        **kwargs
    )


def tao_nguoi_dung():
    email = f"test_{uuid.uuid4().hex[:10]}@example.com"

    r = goi("POST", "/api/dang-ky", json={
        "ho_ten": "Nguoi Test",
        "email": email,
        "mat_khau": MAT_KHAU
    })
    assert r.status_code == 200, r.text

    r = goi("POST", "/api/dang-nhap", json={
        "email": email,
        "mat_khau": MAT_KHAU
    })
    assert r.status_code == 200, r.text

    return r.json()["access_token"]


def gui_du_lieu_online(ma_thiet_bi, muc_thuc_an=100, muc_nuoc=100):
    return goi(
        "POST", "/api/du-lieu-thiet-bi",
        khoa=tao_khoa_thiet_bi(ma_thiet_bi),
        json={
            "ma_thiet_bi": ma_thiet_bi,
            "muc_thuc_an": muc_thuc_an,
            "muc_nuoc": muc_nuoc,
            "trang_thai_thiet_bi": "DANG_KET_NOI"
        }
    )

# Fixture
@pytest.fixture(scope="session", autouse=True)
def kiem_tra_server():
    try:
        requests.get(API + "/", timeout=5)
    except requests.exceptions.RequestException:
        pytest.skip(f"Backend chua chay o {API}", allow_module_level=True)


@pytest.fixture(scope="session")
def token_a():
    return tao_nguoi_dung()


@pytest.fixture(scope="session")
def token_b():
    return tao_nguoi_dung()


@pytest.fixture(scope="session")
def du_lieu_a(token_a):
    """Thu cung + thiet bi cua nguoi dung A (ma_nguoi_dung bi server bo qua)."""
    r = goi("POST", "/api/thu-cung", token=token_a, json={
        "ma_nguoi_dung": 0,
        "ten_thu_cung": "Pet Test",
        "loai": "Cho"
    })
    assert r.status_code == 200, r.text
    ma_thu_cung = r.json()["ma_thu_cung"]

    r = goi("POST", "/api/thiet-bi", token=token_a, json={
        "ma_nguoi_dung": 0,
        "ten_thiet_bi": "Thiet bi test",
        "ma_thiet_bi_iot": "test-" + uuid.uuid4().hex[:12]
    })
    assert r.status_code == 200, r.text
    ma_thiet_bi = r.json()["ma_thiet_bi"]

    return {
        "ma_thu_cung": ma_thu_cung,
        "ma_thiet_bi": ma_thiet_bi,
        "khoa": tao_khoa_thiet_bi(ma_thiet_bi)
    }

# TC01 - Goi API khong dang nhap
@pytest.mark.parametrize("duong_dan", [
    "/api/thu-cung",
    "/api/thiet-bi",
    "/api/lich-cho-an",
    "/api/lich-su-cho-an",
    "/api/canh-bao",
    "/api/toi",
])
def test_01_khong_token_bi_tu_choi(duong_dan):
    assert goi("GET", duong_dan).status_code == 401

# TC02 - Token gia / bi sua
def _token_sua_payload(token_that, ma_nguoi_dung_moi):
    """Giu nguyen chu ky nhung doi 'sub' trong payload."""
    dau, payload, chu_ky = token_that.split(".")
    payload += "=" * (-len(payload) % 4)
    du_lieu = json.loads(base64.urlsafe_b64decode(payload))
    du_lieu["sub"] = str(ma_nguoi_dung_moi)
    payload_moi = base64.urlsafe_b64encode(
        json.dumps(du_lieu).encode()
    ).rstrip(b"=").decode()
    return f"{dau}.{payload_moi}.{chu_ky}"


def test_02_token_gia_bi_tu_choi(token_a):
    ma = goi("GET", "/api/toi", token=token_a).json()["ma_nguoi_dung"]
    het_han = int(time.time()) + 3600

    token_sai_khoa = jwt.encode(
        {"sub": str(ma), "exp": het_han}, "khoa-doan-bua", algorithm="HS256"
    )
    token_none = jwt.encode(
        {"sub": str(ma), "exp": het_han}, None, algorithm="none"
    )
    token_sua = _token_sua_payload(token_a, ma + 1)

    for token in (token_sai_khoa, token_none, token_sua, "khong-phai-jwt"):
        assert goi("GET", "/api/toi", token=token).status_code == 401

# TC03 - Truy cap du lieu cua nguoi khac (IDOR)
def test_03_khong_truy_cap_cheo_tai_khoan(token_a, token_b, du_lieu_a):
    pet = f"/api/thu-cung/{du_lieu_a['ma_thu_cung']}"
    tb = f"/api/thiet-bi/{du_lieu_a['ma_thiet_bi']}"

    bi_chan = (403, 404)

    assert goi("GET", pet, token=token_b).status_code in bi_chan
    assert goi("PUT", pet, token=token_b,
               json={"ten_thu_cung": "hacked"}).status_code in bi_chan
    assert goi("DELETE", pet, token=token_b).status_code in bi_chan
    assert goi("GET", tb, token=token_b).status_code in bi_chan
    assert goi("DELETE", tb, token=token_b).status_code in bi_chan

    r = goi("POST", "/api/cho-an-ngay", token=token_b, json={
        "ma_thu_cung": du_lieu_a["ma_thu_cung"],
        "ma_thiet_bi": du_lieu_a["ma_thiet_bi"],
        "luong_thuc_an": 10
    })
    assert r.status_code in bi_chan

    # Du lieu cua A van con nguyen, ten khong bi doi
    r = goi("GET", pet, token=token_a)
    assert r.status_code == 200
    assert r.json()["ten_thu_cung"] == "Pet Test"

    # B khong thay thu cung cua A trong danh sach cua minh
    ds = goi("GET", "/api/thu-cung", token=token_b).json()
    assert all(t["ma_thu_cung"] != du_lieu_a["ma_thu_cung"] for t in ds)

# TC04 - Thiet bi IoT dung sai khoa
def test_04_khoa_thiet_bi(du_lieu_a):
    ma = du_lieu_a["ma_thiet_bi"]
    khoa_dung = du_lieu_a["khoa"]
    khoa_thiet_bi_khac = tao_khoa_thiet_bi(ma + 1)

    # Doi chung: khoa dung thi duoc
    assert goi("GET", f"/api/iot/thiet-bi/{ma}",
               khoa=khoa_dung).status_code == 200

    thu = {
        "GET": f"/api/lenh-cho-an/{ma}",
        "GET_IOT": f"/api/iot/thiet-bi/{ma}",
    }

    for khoa in (None, "", "khoa-sai", khoa_thiet_bi_khac):
        assert goi("GET", thu["GET"], khoa=khoa).status_code == 401
        assert goi("GET", thu["GET_IOT"], khoa=khoa).status_code == 401

        r = goi("POST", "/api/du-lieu-thiet-bi", khoa=khoa, json={
            "ma_thiet_bi": ma,
            "muc_thuc_an": 10,
            "muc_nuoc": 10,
            "trang_thai_thiet_bi": "DANG_KET_NOI"
        })
        assert r.status_code == 401

# TC05 - Du lieu dau vao ngoai khoang cho phep
@pytest.mark.parametrize("thuc_an,nuoc", [(150, 50), (-5, 50), (50, 101), (50, -1)])
def test_05a_cam_bien_ngoai_khoang(du_lieu_a, thuc_an, nuoc):
    r = gui_du_lieu_online(du_lieu_a["ma_thiet_bi"], thuc_an, nuoc)
    assert r.status_code == 400


@pytest.mark.parametrize("luong", [-5, 0, 501, 99999])
def test_05b_luong_cho_an_khong_hop_le(token_a, du_lieu_a, luong):
    assert gui_du_lieu_online(du_lieu_a["ma_thiet_bi"]).status_code == 200

    r = goi("POST", "/api/cho-an-ngay", token=token_a, json={
        "ma_thu_cung": du_lieu_a["ma_thu_cung"],
        "ma_thiet_bi": du_lieu_a["ma_thiet_bi"],
        "luong_thuc_an": luong
    })
    assert r.status_code == 400
    assert "Luong" in r.json()["detail"]

# TC06 - SQL injection va mat khau yeu khi dang ky / dang nhap
def test_06a_sql_injection_dang_nhap():
    for email in ("' OR '1'='1", "admin'--", "x@x.com' OR 1=1 --"):
        r = goi("POST", "/api/dang-nhap",
                json={"email": email, "mat_khau": "bat-ky"})
        assert r.status_code == 401   # khong phai 200, cung khong phai 500


def test_06b_dang_ky_du_lieu_yeu():
    r = goi("POST", "/api/dang-ky", json={
        "ho_ten": "A", "email": "khong-phai-email", "mat_khau": MAT_KHAU
    })
    assert r.status_code == 400

    r = goi("POST", "/api/dang-ky", json={
        "ho_ten": "A", "email": f"{uuid.uuid4().hex[:8]}@example.com",
        "mat_khau": "123"
    })
    assert r.status_code == 400


def test_06c_sai_mat_khau_khong_lo_thong_tin():
    email = f"test_{uuid.uuid4().hex[:10]}@example.com"
    goi("POST", "/api/dang-ky", json={
        "ho_ten": "A", "email": email, "mat_khau": MAT_KHAU
    })

    sai_mk = goi("POST", "/api/dang-nhap",
                 json={"email": email, "mat_khau": "sai-mat-khau"})
    khong_ton_tai = goi("POST", "/api/dang-nhap", json={
        "email": f"khongco_{uuid.uuid4().hex[:6]}@example.com",
        "mat_khau": "sai-mat-khau"
    })

    # Hai truong hop tra cung ma loi va cung thong bao (khong do duoc email)
    assert sai_mk.status_code == khong_ton_tai.status_code == 401
    assert sai_mk.json() == khong_ton_tai.json()

# TC07 - Khong cho tao lenh cho an trung khi lenh cu chua xu ly
def test_07_khong_tao_lenh_trung(token_a, du_lieu_a):
    assert gui_du_lieu_online(du_lieu_a["ma_thiet_bi"]).status_code == 200

    thong_tin = {
        "ma_thu_cung": du_lieu_a["ma_thu_cung"],
        "ma_thiet_bi": du_lieu_a["ma_thiet_bi"],
        "luong_thuc_an": 10
    }

    lan_1 = goi("POST", "/api/cho-an-ngay", token=token_a, json=thong_tin)
    lan_2 = goi("POST", "/api/cho-an-ngay", token=token_a, json=thong_tin)

    assert lan_1.status_code == 200, lan_1.text
    assert lan_2.status_code == 400