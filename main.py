import asyncio
from fastapi import FastAPI
from hypercorn.config import Config
from hypercorn.asyncio import serve


from app.geo_query import router as geo_query_router


# Tạo app
app = FastAPI()

@app.get("/")
def main_page():
    return "Hello world from FastAPI"


# Nối các router
app.include_router(geo_query_router)



# if __name__ == "__main__":
#     config = Config()
#     config.bind = [
#         "0.0.0.0:60000",
#     ]
#
#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(serve(app, config))