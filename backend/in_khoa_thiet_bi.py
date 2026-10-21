import sys

from backend.bao_mat import tao_khoa_thiet_bi

ma_thiet_bi = int(sys.argv[1]) if len(sys.argv) > 1 else 1

print(tao_khoa_thiet_bi(ma_thiet_bi))