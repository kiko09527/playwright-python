from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.jzyx_api import app as jzyx_api_app
from routes.multi_routes import app as multi_routes_app
from routes.file_api import app as file_api_app

app = FastAPI()
# 添加 CORS 中间件
origins = [
    "http://localhost:63342",  # 允许的前端应用源
    "http://127.0.0.1:8000",    # 其他服务的源（如果有）
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 可以根据需要设置允许的源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有HTTP头
)

# 将不同的 API 挂载到不同的路径下
app.mount("/jzyx", jzyx_api_app)      # 访问 /api/v1/trace
app.mount("/test", multi_routes_app)    # 访问 /api/v2/trace
app.mount("/api/", file_api_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)