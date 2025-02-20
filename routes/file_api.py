from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import subprocess
import os
import logging
import genera_python_code

app = FastAPI()

# 设置文件上传目录为项目根目录
UPLOAD_FOLDER = os.getcwd()  # 根目录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.get("/trace", summary="显示trace链路图")
def trace(test_file_name: str = 'test_example.py'):
    # 获取 trace 文件名和测试文件名
    logger.info(f"trace|请求参数:test_file_name={test_file_name}")

    # 确保 test 文件名以 .py 结尾
    if not test_file_name.endswith('.py'):
        test_file_name += '.py'

    # 构建 pytest 命令
    command = ['pytest', '--trace', test_file_name]

    # 执行 pytest 命令
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return JSONResponse(content={
            'status': 'success',
            'output': result.stdout
        })
    except subprocess.CalledProcessError as e:
        logger.error(f"trace|当前测试文件回溯异常{e}")
        return JSONResponse(content={
            'status': 'error',
            'output': e.stderr
        }, status_code=500)

@app.get("/codegen", summary="生成脚本语句")
def codegen(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="URL parameter is required")

    try:
        # 调用 playwright codegen 命令
        command = ["playwright", "codegen", url]
        process = subprocess.run(command, capture_output=True, text=True)

        # 检查命令是否成功执行
        if process.returncode != 0:
            return JSONResponse(content={"error": process.stderr.strip()}, status_code=500)

        # 返回生成的代码
        return JSONResponse(content={"generated_code": process.stdout.strip()})

    except Exception as e:
        return JSONResponse(content={"error": f"An error occurred: {str(e)}"}, status_code=500)

@app.get("/execute", summary="执行一次脚本")
def execute_script(name: str):
    if not name:
        raise HTTPException(status_code=400, detail="No script name provided.")

    # 获取当前工作目录
    current_directory = os.getcwd()

    # 确保脚本是 `.py` 文件，并构建完整路径
    if not name.endswith('.py'):
        raise HTTPException(status_code=400, detail="Invalid script name. It must end with .py.")

    script_path = os.path.join(current_directory, name)

    # 检查文件是否存在
    if not os.path.isfile(script_path):
        raise HTTPException(status_code=400, detail="Script does not exist in the current directory.")

    try:
        # 使用subprocess运行外部python脚本
        result = subprocess.run(['python', script_path], capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        return JSONResponse(content={"output": output})
    except subprocess.CalledProcessError as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/upload", summary="生成脚本文件")
def upload_code(filename: str, code: str):
    if not filename.endswith('.py'):
        filename += '.py'  # 自动添加 .py 扩展名

    if not code:
        raise HTTPException(status_code=400, detail="No code provided.")

    modified_code = genera_python_code.modify_code(code, filename)

    # 生成完整文件路径
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    try:
        # 将代码写入指定的 .py 文件
        with open(file_path, 'w') as file:
            file.write(modified_code)

        return JSONResponse(content={"message": "Python script created successfully!", "filename": filename})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/", summary="根文件")
def read_root():
    return JSONResponse(content={"message": "Welcome to the Playwright code generator API. Use /codegen?url=<your_url>"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)