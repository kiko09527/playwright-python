import logging
import json
import mysql.connector
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
responses = []

# 数据库连接配置
db_config = {
    'host': '127.0.0.1',  # 数据库主机
    'user': 'root',  # 数据库用户名
    'password': 'password',  # 数据库密码
    'database': 'autotest'  # 数据库名称
}


# 记录请求
# def log_request(request, filtered_apis=None, need_api=None, current_file_name=None, unique_code=None):
#     logger.info(f"log_request|请求参数 url:{request.url}")
#     try:
#         if filtered_apis is None:
#             filtered_apis = set()
#         # 没有指定要记录的 API 则使用默认值
#         if need_api is None:
#             need_api = "api-store-test.gaojihealth.cn"
#
#         # 先检查 request.url 是否包含 need_api，若不包含则直接返回
#         if need_api not in request.url:
#             logger.warning(f"log_request首次次校验不通过|url:{request.url}跳过记录")
#             return  # 直接返回，不记录任何内容
#
#         if filtered_apis and any(api in request.url for api in filtered_apis):
#             return  # 直接返回，不记录任何内容
#         # 如果 request.url 包含 filtered_apis 中的任何一项，则记录请求
#         requests.append({
#             "url": request.url,  # 请求的 URL
#             "method": request.method,  # 请求方法（GET, POST等）
#             "post_data": request.post_data,  # POST 数据（如果有的话）
#             "headers": request.headers,  # 请求头
#         })
#         logger.info(f"log_request记录请求|url:{request.url}已记录请求")
#     except Exception as e:
#         logger.error(f"log_request|请求服务异常{e}")
#         pass


# 记录响应
def log_response(response, filtered_apis=None, need_api=None, current_file_name=None, unique_code=None):
    try:
        if filtered_apis is None:
            filtered_apis = set()
        # 没有指定要记录的 API 则使用默认值
        if need_api is None:
            need_api = "api-store-test.gaojihealth.cn"

        # 先检查 request.url 是否包含 need_api，若不包含则直接返回
        if need_api not in response.url:
            # logger.warning(f"log_response 首次次校验不通过|url:{response.url}跳过记录")
            return  # 直接返回，不记录任何内容

        if filtered_apis and any(api in response.url for api in filtered_apis):
            return  # 直接返回，不记录任何内容
        # 如果 request.url 包含 filtered_apis 中的任何一项，则记录请求
        # 记录请求
        # 记录请求数据
        response_data = {
            "script_name": current_file_name,
            "unique_code": unique_code,
            "method": response.request.method,
            "request_url": response.request.url,
            "header": str(response.request.headers),
            "request_post_data": response.request.post_data,
            "url": response.url,
            "status": response.status,
            "body": response.body().decode('utf-8'),
            "response_header": response.headers
        }
        logger.info(f"log_response 记录响应结果|url:{response.url}已记录响应")
        # 将响应数据保存到数据库
        save_to_database(response_data, current_file_name, unique_code)
    except Exception as e:
        logger.error(f"log_response|处理服务异常{e}")
        pass


def save_to_database(data, current_file_name, unique_code):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        # 删除基于 script_name 的所有记录,只保存最新的
        delete_query = "DELETE FROM log_http WHERE script_name = %s and unique_code!=%s"
        cursor.execute(delete_query, (current_file_name, unique_code,))

        # 提交删除操作
        connection.commit()

        insert_query = """
            INSERT INTO log_http (script_name, unique_code, url, headers, post_data, method, status, body,response_header)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s)
        """
        # 批量插入
        # 插入单个数据对象
        cursor.execute(insert_query, (
            data['script_name'],
            data['unique_code'],
            data['url'],
            data['header'],
            data['request_post_data'],
            data['method'],
            data['status'],
            data['body'],
            json.dumps(data['response_header'])
        ))
        connection.commit()
    except Exception as e:
        logger.error(f"save_to_database|数据库操作异常: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def get_api_fifter(current_file_name):
    try:
        # 从数据库获取 filtered_apis 和 need_api
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        # 这里的 SQL 查询可以根据需要进行调整
        cursor.execute("SELECT need_api, filtered_apis FROM script_info WHERE script_name = %s", (current_file_name,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        if result:
            filtered_apis_json = result['filtered_apis']
            if filtered_apis_json:
                try:
                    # 解析 JSON 并转换为集合
                    filtered_apis = set(json.loads(filtered_apis_json))
                except json.JSONDecodeError:
                    # 如果解析失败，返回空集合
                    filtered_apis = set()
            else:
                # 如果 filtered_apis 为空字符串，返回空集合
                filtered_apis = set()

            return filtered_apis, result['need_api']
        return None, None
    except Exception as e:
        logger.error(f"get_api_fifter|服务异常 current_file_name:{current_file_name},异常{e}")
        pass


# 创建新页面并绑定监听器
def setup_page(page, current_file_name, unique_code):
    try:
        logger.info(f"setup_page|请求参数 current_file_name:{current_file_name},unique_code:{unique_code}")
        current_file_name = current_file_name.replace(".py", "")
        filtered_apis, need_api = get_api_fifter(current_file_name)
        # 绑定请求监听器，传递过滤接口和记录的 API URL
        # page.on("request", lambda request: log_request(request, filtered_apis, need_api, current_file_name, unique_code))
        page.on("response", lambda response: log_response(response, filtered_apis, need_api, current_file_name,
                                                          unique_code))  # 设置响应的监听器
    except Exception as e:
        logger.error(f"setup_page|服务异常 current_file_name:{current_file_name},unique_code:{unique_code},{e}")
