from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.responses import JSONResponse
import subprocess
import json
from script_log import save_script_log, update_script_execute_log
from pydantic import BaseModel
import os
import logging
import genera_python_code
import mysql.connector
from typing import Optional

app = FastAPI()

# 设置文件上传目录为项目根目录
UPLOAD_FOLDER = os.getcwd()  # 根目录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 数据库连接配置
db_config = {
    'host': '127.0.0.1',  # 数据库主机
    'user': 'root',  # 数据库用户名
    'password': 'password',  # 数据库密码
    'database': 'autotest'  # 数据库名称
}


def create_response(success: bool, message: str, output=None):
    """生成一致的响应格式"""
    response_data = {
        "success": success,
        "message": message,
    }

    if output is not None:
        response_data["output"] = output

    return JSONResponse(content=response_data)


@app.get("/trace", summary="生成trace")
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
            return create_response(False, "Script execution failed", None)  # 返回404错误

        # 返回生成的代码
        return create_response(True, "generated_code successfully.", process.stdout.strip())  # 返回成功响应

    except Exception as e:
        logger.error(f"codegen|服务异常{e}")
        return create_response(False, f"Script execution failed: {e.stderr.strip()}", None)


@app.get("/execute", summary="执行一次脚本")
def execute_script(name: str):
    if not name:
        return create_response(False, "No script name provided.", None)  # 返回400
    log_id = save_script_log(name, "无",  "脚本","正在执行..","脚本正在执行,请耐心等候")  # 保存日志
    # 获取当前工作目录
    current_directory = os.getcwd()
    # 确保脚本名是以 '.py' 结尾
    if not name.endswith('.py'):
        name += '.py'  # 自动添加 '.py' 后缀

    script_path = os.path.join(current_directory, name)
    # 检查文件是否存在
    if not os.path.isfile(script_path):
        logger.error(f"execute_script|文件不存在log_id:{log_id}")
        update_script_execute_log(log_id, "执行失败", "Script does not exist in the current directory",name)
        return create_response(False, "Script does not exist in the current directory.", None)  # 返回404错误

    try:
        # 使用subprocess运行外部python脚本
        result = subprocess.run(['python', script_path], capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        update_script_execute_log(log_id, "执行成功", "Script executed successfully.",name)
        logger.error(f"execute_script|执行成功{output}")
        return create_response(True, "Script executed successfully.", output)  # 返回成功响应
    except Exception as e:
        # 将错误信息转换为 JSON 字符串
        error_message = {
            "stderr": e.stderr.strip() if e.stderr else None,
            "error": str(e)
        }
        error_message_json = json.dumps(error_message)  # 转换为 JSON 字符串
        update_script_execute_log(log_id, "执行失败", error_message_json,name)
        logger.error(f"execute_script|服务异常{e}")
        return create_response(False, f"Script execution failed: {e.stderr.strip()}", None)


@app.get("/showTrace", summary="显示 Playwright 跟踪报告")
def show_trace(trace: str):
    if not trace:
        return create_response(False, "No trace file provided.", None)  # 返回400

    # 获取当前工作目录
    current_directory = os.getcwd()

    # 确保 trace 文件名是以 '.zip' 结尾
    if not trace.endswith('.zip'):
        trace += '.zip'  # 自动添加 '.zip' 后缀

    trace_path = os.path.join(current_directory, trace)

    # 检查文件是否存在
    if not os.path.isfile(trace_path):
        return create_response(False, "Trace file does not exist in the current directory.", None)  # 返回404错误

    try:
        # 使用 subprocess 运行 Playwright show-trace 命令
        result = subprocess.run(['playwright', 'show-trace', trace_path], capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        return create_response(True, "Trace displayed successfully.", output)  # 返回成功响应
    except Exception as e:
        logger.error(f"show_trace|服务异常{e}")
        return create_response(False, f"Trace display failed: {e.stderr.strip()}", None)


@app.get("/debug", summary="执行 文件 debug模式")
def run_pytest(trace: str):
    if not trace:
        return create_response(False, "No trace file provided.", None)  # 返回400

    # 获取当前工作目录
    current_directory = os.getcwd()

    # 确保 trace 文件名是以 '.py' 结尾
    if not trace.endswith('.py'):
        trace += '.py'  # 自动添加 '.py' 后缀

    trace_path = os.path.join(current_directory, trace)

    # 检查文件是否存在
    if not os.path.isfile(trace_path):
        return create_response(False, "Trace file does not exist in the current directory.", None)  # 返回404错误

    try:
        # 设置 PWDEBUG 环境变量，并运行 pytest
        env = os.environ.copy()  # 复制当前环境变量
        env["PWDEBUG"] = "1"  # 设置 PWDEBUG 环境变量
        result = subprocess.run(['pytest', '-s', trace_path], capture_output=True, text=True, env=env, check=True)
        output = result.stdout.strip()
        return create_response(True, "Pytest executed successfully.", output)  # 返回成功响应
    except Exception as e:
        logger.error(f"run_pytest|服务异常{e}")
        return create_response(False, f"Pytest execution failed: {e.stderr.strip()}", None)


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


# 脚本信息模型
class ScriptInfo(BaseModel):
    id: int
    script_name: str
    execute_time: str
    need_api: str
    filtered_apis: str
    create_time: str
    update_time: str


@app.get("/queryScriptList", response_model=dict, summary="查询脚本文件列表")
async def queryScriptList(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1),
        script_name: str = Query(None, title="脚本名称", description="可选脚本名称进行模糊匹配")
):
    try:
        offset = (page - 1) * page_size
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # 构建查询
        query = "SELECT * FROM script_info WHERE TRUE"
        params = []

        # 如果提供了脚本名称，添加到查询条件
        if script_name:
            query += " AND script_name = %s"
            params.append(script_name)

        query += " LIMIT %s OFFSET %s"
        params.append(page_size)
        params.append(offset)

        # 查询数据
        cursor.execute(query, params)
        rows = cursor.fetchall()

        # 获取总记录数
        count_query = "SELECT COUNT(*) as total FROM script_info WHERE TRUE"
        if script_name:
            count_query += " AND script_name = %s"
        cursor.execute(count_query, [script_name] if script_name else [])
        total_count = cursor.fetchone()['total']

        return {
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'data': rows
        }

    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.get("/queryScriptLogList", response_model=dict, summary="查询脚本执行列表")
async def query_script_log_list(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1),
        script_name: Optional[str] = Query(None, title="脚本名称", description="可选脚本名称进行模糊匹配")
):
    connection = None
    cursor = None
    try:
        offset = (page - 1) * page_size
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # 构建查询
        query = "SELECT * FROM script_execute_log WHERE TRUE"
        params = []

        # 如果提供了脚本名称，添加到查询条件
        if script_name:
            query += " AND script_name LIKE %s"
            params.append(f"%{script_name}%")

        query += " LIMIT %s OFFSET %s"
        params.append(page_size)
        params.append(offset)

        # 查询数据
        cursor.execute(query, params)
        rows = cursor.fetchall()

        # 获取总记录数
        count_query = "SELECT COUNT(*) as total FROM script_execute_log WHERE TRUE"
        if script_name:
            count_query += " AND script_name LIKE %s"

        cursor.execute(count_query, [f"%{script_name}%"] if script_name else [])
        total_count = cursor.fetchone()['total']

        return {
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'data': rows
        }

    except Exception as e:
        logger.error(f"query_script_log_list|服务异常{e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# 更新请求模型
class ScriptUpdate(BaseModel):
    script_name: Optional[str] = None
    execute_time: Optional[str] = None
    need_api: Optional[str] = None
    filtered_apis: Optional[str] = None


@app.post("/updateScript/{script_id}", response_model=dict, summary="更新脚本信息")
async def update_script(
        script_id: int = Path(..., title="脚本 ID", description="需要更新的脚本的 ID"),
        update_data: ScriptUpdate = None  # 确保这个参数顺序正确
):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # 生成动态 SQL 语句
        updates = []
        params = []

        if update_data.script_name is not None:
            updates.append("script_name = %s")
            params.append(update_data.script_name)

        if update_data.execute_time is not None:
            updates.append("execute_time = %s")
            params.append(update_data.execute_time)

        if update_data.need_api is not None:
            updates.append("need_api = %s")
            params.append(update_data.need_api)

        if update_data.filtered_apis is not None:
            updates.append("filtered_apis = %s")
            params.append(update_data.filtered_apis)

        if update_data.filtered_apis is not None:
            updates.append("delete_apis = %s")
            params.append(update_data.filtered_apis)

        # 如果没有字段需要更新，则抛出异常
        if not updates:
            raise HTTPException(status_code=400, detail="没有提供需要更新的字段")

        # 添加 ID 到参数表中
        params.append(script_id)

        query = f"UPDATE script_info SET {', '.join(updates)} WHERE id = %s"
        cursor.execute(query, params)
        connection.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="脚本未找到")

        return {"message": "脚本信息更新成功"}

    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@app.get("/", summary="根文件")
def read_root():
    return JSONResponse(
        content={"message": "Welcome to the Playwright code generator API. Use /codegen?url=<your_url>"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
