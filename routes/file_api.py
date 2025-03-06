from datetime import datetime

from fastapi import FastAPI, HTTPException, Query, Path, Request, Form
from fastapi.responses import JSONResponse
import subprocess
import json
from script_log import save_script_log, update_script_execute_log, insert_script_info, query_script_info, \
    update_script_execute_log_api
from pydantic import BaseModel
import os
import logging
import genera_python_code
import mysql.connector
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
import httpx  # 用于发送 HTTP 请求
from config.db_config import db_config
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 可以根据需要设置允许的源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 设置文件上传目录为项目根目录
UPLOAD_FOLDER = os.getcwd()  # 根目录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



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
    log_id = save_script_log(name, "无", "脚本", "正在执行..", "脚本正在执行,请耐心等候")  # 保存日志
    # 获取当前工作目录
    current_directory = os.getcwd()
    # 确保脚本名是以 '.py' 结尾
    if not name.endswith('.py'):
        name += '.py'  # 自动添加 '.py' 后缀

    script_path = os.path.join(current_directory, name)
    # 检查文件是否存在
    if not os.path.isfile(script_path):
        logger.error(f"execute_script|文件不存在log_id:{log_id}")
        update_script_execute_log(log_id, "执行失败", "Script does not exist in the current directory", name)
        return create_response(False, "Script does not exist in the current directory.", None)  # 返回404错误

    try:
        # 使用subprocess运行外部python脚本
        result = subprocess.run(['python', script_path], capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        update_script_execute_log(log_id, "执行成功", "Script executed successfully.", name)
        logger.error(f"execute_script|执行成功{output}")
        return create_response(True, "Script executed successfully.", output)  # 返回成功响应
    except Exception as e:
        update_script_execute_log(log_id, "执行失败", str(e), name)
        logger.error(f"execute_script|服务异常{e}")
        return create_response(False, f"Script execution failed: {str(e)}", None)


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
        return create_response(False, f"Trace display failed: {str(e)}", None)


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
        return create_response(False, f"Pytest execution failed: {str(e)}", None)


@app.post("/upload", summary="生成脚本文件")
def upload_code(filename: str = Form(...), code: str = Form(...), fileType: str = Form(None)):
    logger.info(f"upload_code|请求参数 filename:{filename},code:{code},fileType:{fileType}")
    # 根据 fileType 修改文件名逻辑
    if not filename.endswith('.py'):
        filename += '.py'  # 自动添加 .py 扩展名

    if not code:
        raise HTTPException(status_code=400, detail="No code provided.")
    # 查询数据库确认 script_name 是否存在

    existing_script = query_script_info(filename)
    if existing_script:
        logger.warning(f"upload_code|脚本名称 '{filename}' 已存在，无法重复上传。")
        raise HTTPException(status_code=400, detail="Script already exists.")

    # 判断 fileType 是否存在并且等于 1
    if not (fileType is not None and fileType == "1"):
        logger.warning(f"upload_code|原始文件")
        modified_code = genera_python_code.modify_code(code, filename)
    else:
        logger.warning(f"upload_code|代码补充")
        modified_code = code  # 如果fileType是1,则直接使用code

    # 生成完整文件路径
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    try:
        # 将代码写入指定的 .py 文件
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(modified_code)
        insert_script_info(filename, "暂未执行")
        return JSONResponse(content={"message": "Python script created successfully!", "filename": filename})
    except Exception as e:
        logger.error(f"upload_code|服务异常{e}")
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

        # 添加排序条件并设置 LIMIT 和 OFFSET
        query += " ORDER BY create_time DESC LIMIT %s OFFSET %s"
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

        query += " ORDER BY create_time DESC"  # 假设表中创建时间的字段名为 created_at
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
    execute_mode: Optional[str] = None
    send_email: Optional[str] = None
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

        if update_data.execute_mode is not None:
            updates.append("execute_mode = %s")
            params.append(update_data.execute_mode)

        if update_data.send_email is not None:
            updates.append("send_email = %s")
            params.append(update_data.send_email)

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


@app.get("/queryLogHttpList", response_model=dict, summary="查询 HTTP 接口列表")
async def query_log_http_list(
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
        query = "SELECT * FROM log_http WHERE TRUE"
        params = []

        # 如果提供了脚本名称，添加到查询条件
        if script_name:
            query += " AND script_name LIKE %s"
            params.append(f"%{script_name}%")

        # 按创建时间倒序排列
        query += " ORDER BY create_time DESC"

        query += " LIMIT %s OFFSET %s"
        params.append(page_size)
        params.append(offset)

        # 查询数据
        cursor.execute(query, params)
        rows = cursor.fetchall()

        # 获取总记录数
        count_query = "SELECT COUNT(*) as total FROM log_http WHERE TRUE"
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
        logger.error(f"query_log_http_list|服务异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# 定义请求和响应的数据模型
class Item(BaseModel):
    name: str
    value: int


@app.post("/batchExecute", summary="执行多次脚本")
async def batchExecute(request: Request):
    try:
        # 从请求体中直接获取数据
        request_data = await request.json()
        name = request_data.get("name")
        data = request_data.get("data")
        logger.info(f"batchExecute|请求参数: url:{name},data:{data}")
        if not name:
            return create_response(False, "No script name provided.", None)  # 返回400
        # 获取当前工作目录
        current_directory = os.getcwd()
        # 确保脚本名是以 '.py' 结尾
        if not name.endswith('.py'):
            name += '.py'  # 自动添加 '.py' 后缀
        # 解析JSON字符串为列表
        data_list = json.loads(data)
        if not isinstance(data_list, list):
            return create_response(False, "batchExecute|数据格式错误，需要提供JSON数组", None)
        logger.info(f"batchExecute|本次一共{len(data_list)}个请求")
        script_path = os.path.join(current_directory, name)
        # 检查文件是否存在
        if not os.path.isfile(script_path):
            logger.error(f"batchExecute|文件不存在")
            return create_response(False, "Script does not exist in the current directory.", None)  # 返回404错误

        results = []
        # 循环处理每个请求
        for index, data_item in enumerate(data_list):
            try:
                # 获取当前计数
                currentCount = index + 1
                totalCount = len(data_list)
                # 将 保存日志
                log_id = save_script_log(name, json.dumps(data_item), "API", "正在执行..", "脚本正在执行,请耐心等候")  # 保存日志
                # 将 data_item 转换为字符串
                command = [
                    "python", script_path,
                    json.dumps(data_item)  # 转换为字符串以传递
                ]
                logger.info(f"batchExecute|执行命令: {command}")  # 记录执行的命令
                # 使用subprocess运行外部python脚本
                result = subprocess.run(command, capture_output=True, text=True, check=True)
                logger.info(f"batchExecute|命令输出: {result.stdout.strip()}")  # 记录命令输出
                output = result.stdout.strip()
                logger.info(f"batchExecute|执行成功{output}")
                # 处理响应
                results.append({
                    "status": "success",
                    "message": "执行成功",
                    "data": data_item,
                    "response": output
                })
                update_script_execute_log_api(log_id, "执行成功", "Script executed successfully.", name, totalCount,currentCount)
            except subprocess.CalledProcessError as e:
                logger.error(f"batchExecute|CalledProcessError服务异常: {e.stderr.strip()}")  # 记录标准错误输出
                update_script_execute_log_api(log_id, "执行失败", e.stderr.strip(), name, totalCount, currentCount)
                results.append({
                    "status": "error",
                    "message": str(e),
                    "data": data_item
                })
            except Exception as e:
                logger.error(f"batchExecute|服务异常{e}")
                update_script_execute_log_api(log_id, "执行失败", str(e), name, totalCount, currentCount)
                results.append({
                    "status": "error",
                    "message": str(e),
                    "data": data_item
                })
        # 返回所有执行结果
        success_count = sum(1 for r in results if r["status"] == "success")
        total_count = len(results)
        return {
            "success": True,
            "message": f"执行完成: 成功 {success_count}/{total_count}",
            "results": results
        }
    except Exception as e:
        logger.error(f"batchExecute|整体服务异常: {e}")
        return create_response(False, f"batchExecute|服务异常: {str(e)}", None)


@app.post("/executeApi")
async def executeApi(request: Request):
    try:
        # 从请求体中直接获取数据
        request_data = await request.json()
        url = request_data.get("url")
        data = request_data.get("data")
        logger.info(f"executeApi|请求参数: url:{url},data:{data}")
        if not url or not data:
            return create_response(False, "URL和请求数据不能为空", None)

        # 解析JSON字符串为列表
        data_list = json.loads(data)
        if not isinstance(data_list, list):
            return create_response(False, "数据格式错误，需要提供JSON数组", None)
        logger.info(f"executeApi|本次一共{len(data_list)}个请求")

        results = []
        # 循环处理每个请求
        for data_item in data_list:
            try:
                if not isinstance(data_item, dict):
                    logger.warning(f"executeApi|数据项格式错误: {data_item}")
                    results.append({
                        "status": "fail",
                        "message": "数据格式错误",
                        "data": data_item
                    })
                    continue

                # 发送请求
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, json=data_item)
                response.raise_for_status()

                # 处理响应
                results.append({
                    "status": "success",
                    "message": "执行成功",
                    "data": data_item,
                    "response": response.text
                })

            except Exception as item_error:
                logger.error(f"executeApi|单个请求执行异常: {item_error}")
                results.append({
                    "status": "error",
                    "message": str(item_error),
                    "data": data_item
                })

        # 返回所有执行结果
        success_count = sum(1 for r in results if r["status"] == "success")
        total_count = len(results)

        return {
            "success": True,
            "message": f"执行完成: 成功 {success_count}/{total_count}",
            "results": results
        }

    except Exception as e:
        logger.error(f"executeApi|整体服务异常: {e}")
        return create_response(False, f"服务异常: {str(e)}", None)


# 定义输入数据模型
class HttpSettingUpdate(BaseModel):
    script_name: Optional[str]
    url: Optional[str]
    assert_type: Optional[str]
    rule_type: Optional[str]
    assert_body_type: Optional[str]
    check_info: Optional[str]


@app.post("/updateHttpSettingInfo")
def updateHttpSettingInfo(update_data: HttpSettingUpdate):
    # 初始化数据库连接
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        # 构建更新 SQL 语句
        update_columns = []
        query_params = []
        logger.warning(f"updateHttpSettingInfo|请求参数update_data:{update_data}")
        # 检查必需的字段是否提供
        if not update_data.script_name or not update_data.url:
            raise HTTPException(status_code=400, detail="Both 'script_name' and 'url' are required.")

        # 只更新提供的字段
        if update_data.assert_type is not None:
            update_columns.append("assert_type = %s")
            query_params.append(update_data.assert_type)
        if update_data.rule_type is not None:
            update_columns.append("rule_type = %s")
            query_params.append(update_data.rule_type)
        if update_data.assert_body_type is not None:
            update_columns.append("assert_body_type = %s")
            query_params.append(update_data.assert_body_type)
        if update_data.check_info is not None:
            update_columns.append("check_info = %s")
            query_params.append(update_data.check_info)

        # 如果没有要更新的字段
        if not update_columns:
            logger.warning(f"updateHttpSettingInfo|No fields to update")
            raise HTTPException(status_code=400, detail="No fields to update.")

        # 添加 WHERE 条件
        query_params.append(update_data.script_name)
        query_params.append(update_data.url)
        update_query = f"""
            UPDATE http_seting_info 
            SET {', '.join(update_columns)} 
            WHERE script_name = %s AND url = %s
        """
        # 执行更新
        cursor.execute(update_query, query_params)
        connection.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Setting not found.")
        logger.warning(f"updateHttpSettingInfo|更新完成")
        return JSONResponse(content={"message": "Update successful."})
    except Exception as e:
        logger.error(f"updateHttpSettingInfo|整体服务异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 关闭游标和连接
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# 定义输入数据模型
class HttpSettingQuery(BaseModel):
    script_name: str
    url: str


@app.post("/queryHttpSettingInfo")
def queryHttpSettingInfo(query_data: HttpSettingQuery):
    # 初始化数据库连接
    connection = None
    cursor = None
    try:
        logger.info(f"queryHttpSettingInfo|查询参数query_data: {query_data}")
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)  # 返回字典格式数据

        # 构建查询 SQL 语句
        select_query = """
            SELECT * 
            FROM http_seting_info 
            WHERE script_name = %s AND url = %s
        """
        cursor.execute(select_query, (query_data.script_name, query_data.url))  # 执行查询
        result = cursor.fetchone()  # 获取第一条记录

        if result is None:
            logger.warning(f"queryHttpSettingInfo|Setting not found")
            raise HTTPException(status_code=404, detail="Setting not found.")
        for key, value in result.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()  # 转换为 ISO 格式字符串
        return JSONResponse(content={"setting": result})  # 返回找到的记录
    except Exception as e:
        logger.error(f"queryHttpSettingInfo|整体服务异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 关闭游标和连接
        if cursor:
            cursor.close()
        if connection:
            connection.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
