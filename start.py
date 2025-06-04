from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.jzyx_api import app as jzyx_api_app
from routes.multi_routes import app as multi_routes_app
from routes.file_api import app as file_api_app
from routes.taskTimeExecutor import start_task_executor

app = FastAPI()
# 添加 CORS 中间件
origins = [
    "http://localhost:63342",
    "http://10.8.50.48:63342",# 允许的前端应用源
    "http://10.8.50.48:8000",    # 其他服务的源（如果有）
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 可以根据需要设置允许的源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有HTTP头
)

# 将不同的 API 挂载到不同的路径下
app.mount("/jzyx", jzyx_api_app)
app.mount("/test", multi_routes_app)
app.mount("/api/", file_api_app)

# 启动定时任务执行器
start_task_executor()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="10.8.50.48", port=8000, reload=True)