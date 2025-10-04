from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# -----------------------------
# Thông tin kết nối Neon PostgreSQL
# -----------------------------
DATABASE_URL = (
    "postgresql+asyncpg://backend_dev:BackendDev!2025@"
    "ep-plain-smoke-a1ipw7es-pooler.ap-southeast-1.aws.neon.tech/neondb"
)

# -----------------------------
# Tạo engine async
# -----------------------------
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
)



# -----------------------------
# Tạo async session
# -----------------------------
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)



# -----------------------------
# Base để kế thừa trong models
# -----------------------------
Base = declarative_base()



# -----------------------------
# Hàm dùng với Depends
# -----------------------------
async def get_db():
    async with SessionLocal() as session:
        yield session


