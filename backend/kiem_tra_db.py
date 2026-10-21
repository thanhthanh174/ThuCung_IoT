import os

import psycopg

from backend.cau_hinh import lay

mat_khau = lay("DB_MAT_KHAU")

print("Do dai mat khau:", len(mat_khau))
print("Co dau %:", "%" in mat_khau)
print("Co dau cach:", " " in mat_khau)
print("Co dau ngoac:", '"' in mat_khau or "'" in mat_khau)
print("Bien he thong DB_MAT_KHAU ton tai:", "DB_MAT_KHAU" in os.environ)

try:
    psycopg.connect(
        host=lay("DB_MAY_CHU", "localhost"),
        port=lay("DB_CONG", "5432"),
        user=lay("DB_NGUOI_DUNG", "postgres"),
        password=mat_khau,
        dbname=lay("DB_TEN", "ThuCungIoT_DB"),
        connect_timeout=5
    ).close()
    print("KET NOI OK")

except Exception as loi:
    print("LOI:", str(loi).splitlines()[0])