from fastapi import HTTPException, APIRouter, Depends
from pydantic import BaseModel, field_validator
from shapely import wkb
from typing import Optional
from sqlalchemy import Column, Integer, Float, String, select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2 import Geometry, Geography

from app.database import Base, get_db





# -----------------------------------------
# Tạo Model
class Leisure(Base):
    __tablename__ = "leisure_data"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    ten_xa = Column(String)
    ma_xa = Column(String)
    loai = Column(String)
    dtich_km2 = Column(Float)
    dan_so = Column(Integer)
    matdo_km2 = Column(Integer)
    nhom_tag = Column(String)
    gia_tri_tag = Column(String)
    nhom_don_gian = Column(String)
    geom = Column(Geometry("POINT", srid=4326))




# --------------------------------------------------
# Tạo Schemas
class Geom(BaseModel):
    lon : float
    lat : float



# Đầu vào của người dùng có các trường sau:
# - Tọa độ của người dùng (EPSG:4326)
# - Loại địa điểm
# - Bán kính (Đơn vị : m)
# - Số lượng địa điểm tối đa (tối thiểu: 5)
class UserInput(BaseModel):
    user_geom: Geom
    type_of_leisure: Optional[str] = None
    radius: int
    min_leisure: Optional[int] = None


    @field_validator("min_leisure")
    @classmethod
    def check_min_leisure(cls, v):
        if v is None:
            v = 5
        return v


    @field_validator("radius")
    @classmethod
    def check_radius(cls, v):
        if v <= 0:
            raise ValueError("Radius must be positive")
        return v



# Đầu ra của người dùng
# - ID của địa điểm
# - Tên của địa điểm
class UserOutput(BaseModel):
    leisure_id : int
    leisure_name : str
    leisure_tag_eng : str
    leisure_tag_vie : str
    leisure_geom : Geom
    distance : float

    model_config = {"from_attributes" : True}





# --------------------------------------------------
# Tạo hàm truy vấn
async def main_query_crud(user_input: UserInput, db: AsyncSession):
    # Tạo điểm user dưới dạng WKTElement (Geometry) → dùng ST_DWithin / ST_Distance
    user_point_wkt = f"POINT({user_input.user_geom.lon} {user_input.user_geom.lat})"

    stmt = select(
        Leisure.id,
        Leisure.name,
        Leisure.gia_tri_tag,
        Leisure.nhom_don_gian,
        Leisure.geom,
        func.ST_Distance(
            Leisure.geom.cast(Geography),
            func.ST_SetSRID(func.ST_GeomFromText(user_point_wkt), 4326).cast(Geography)
        ).label("distance")
    ).where(
        func.ST_DWithin(
            Leisure.geom.cast(Geography),
            func.ST_SetSRID(func.ST_GeomFromText(user_point_wkt), 4326).cast(Geography),
            user_input.radius
        )
    )

    if user_input.type_of_leisure:
        stmt = stmt.where(
            or_(
                Leisure.nhom_tag == user_input.type_of_leisure,
                Leisure.gia_tri_tag == user_input.type_of_leisure
            )
        )

    stmt = stmt.order_by("distance").limit(user_input.min_leisure)


    result = await db.execute(stmt)
    records = result.fetchall()

    output = []
    for r in records:
        point = wkb.loads(bytes(r.geom.data))  # Geometry → shapely Point
        output.append(
            UserOutput(
                leisure_id=r.id,
                leisure_name=r.name,
                leisure_tag_eng=r.gia_tri_tag,
                leisure_tag_vie=r.nhom_don_gian,
                leisure_geom=Geom(lon=point.x, lat=point.y),
                distance=r.distance
            )
        )
    return output





# -------------------------------------------------
# Router
router = APIRouter(prefix = "/geometry")

@router.post("/")
async def main_query_router(user_input : UserInput, db : AsyncSession = Depends(get_db)):
    return await main_query_crud(user_input, db)