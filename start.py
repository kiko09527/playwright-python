from fastapi import FastAPI
from routes.jzyx_api import app as jzyx_api_app
from routes.multi_routes import app as multi_routes_app
from routes.file_api import app as file_api_app

app = FastAPI()

# 将不同的 API 挂载到不同的路径下
app.mount("/jzyx", jzyx_api_app)      # 访问 /api/v1/trace
app.mount("/test", multi_routes_app)    # 访问 /api/v2/trace
app.mount("/api/", file_api_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)