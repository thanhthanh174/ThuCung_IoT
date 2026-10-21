import pathlib
import re

import requests
from dotenv import dotenv_values

from backend.bao_mat import tao_khoa_thiet_bi

API = "http://127.0.0.1:8000"
DUONG_DAN = f"{API}/api/iot/thiet-bi/1"

khoa_iot = dotenv_values("iot/.env").get("KHOA_THIET_BI") or ""
khoa_dung = tao_khoa_thiet_bi(1)


def thu(ten, khoa):
    tieu_de = {"X-Khoa-Thiet-Bi": khoa} if khoa else {}

    try:
        ket_qua = requests.get(DUONG_DAN, headers=tieu_de, timeout=5)
        print(f"{ten:<28} -> {ket_qua.status_code}")
    except requests.exceptions.RequestException:
        print(f"{ten:<28} -> KHONG KET NOI DUOC BACKEND")


print("=== Goi thu API ===")
thu("[1] Khong gui khoa", "")
thu("[2] Khoa trong iot/.env", khoa_iot)
thu("[3] Khoa tinh tu .env goc", khoa_dung)

print()
print("=== Do dai khoa ===")
print("iot/.env :", len(khoa_iot), khoa_iot[:6])
print("tinh lai :", len(khoa_dung), khoa_dung[:6])

print()
print("=== Kiem tra code simulator ===")

ma_nguon = pathlib.Path("iot/thiet_bi.py").read_text(
    encoding="utf-8", errors="ignore"
)

print(
    "So cho con goi bang requests (khong kem khoa):",
    len(re.findall(r"requests\.(?:get|put|post)\(", ma_nguon))
)
print("Co 'phien = requests.Session()':", "phien = requests.Session()" in ma_nguon)
print("Co 'X-Khoa-Thiet-Bi':", "X-Khoa-Thiet-Bi" in ma_nguon)