from backend.database import SessionLocal
from backend import models
from backend.bao_mat import bam_mat_khau

db = SessionLocal()
dem = 0

for nguoi_dung in db.query(models.NguoiDung).all():
    if not nguoi_dung.mat_khau.startswith("$2"):
        nguoi_dung.mat_khau = bam_mat_khau(nguoi_dung.mat_khau)
        dem += 1

db.commit()
db.close()

print(f"Da bam {dem} mat khau.")