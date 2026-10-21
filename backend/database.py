from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from backend.cau_hinh import bat_buoc, lay

DATABASE_URL = (
    f"postgresql://{lay('DB_NGUOI_DUNG', 'postgres')}"
    f":{quote_plus(bat_buoc('DB_MAT_KHAU'))}"
    f"@{lay('DB_MAY_CHU', 'localhost')}:{lay('DB_CONG', '5432')}"
    f"/{lay('DB_TEN', 'ThuCungIoT_DB')}"
)

engine = create_engine(
    DATABASE_URL,
    connect_args={"connect_timeout": 5}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()