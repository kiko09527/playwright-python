import logging
import json
from config.db_config import db_config
import mysql.connector
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
responses = []

#
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
def log_response(response, delete_apis=None,filtered_apis=None, need_api=None, current_file_name=None, unique_code=None):
    try:
        if delete_apis is None:
            delete_apis = set()

        if filtered_apis is None:
            filtered_apis = set()
        # 没有指定要记录的 API 则使用默认值
        if need_api is None:
            need_api = "api-store-test.gaojihealth.cn"
        # 先检查 request.url 是否包含 need_api，若不包含则直接返回
        if need_api not in response.url:
            # logger.warning(f"log_response 首次次校验不通过|url:{response.url}跳过记录")
            return  # 直接返回，不记录任何内容
        # 如果 delete_apis 不为空，并且 response.url 包含其中任意一项，则直接返回
        if delete_apis and any(api in response.url for api in delete_apis):
            return  # 不记录任何内容

        if filtered_apis and any(api in response.url for api in filtered_apis):
            return  # 直接返回，不记录任何内容

        response_data = {
            "script_name": current_file_name,
            "unique_code": unique_code,
            "method": response.request.method,
            "request_url": response.request.url,
            # 对 headers 进行处理以去掉双引号并将所有单引号替换成双引号
            "header": str(response.request.headers).replace('"', '').replace("'", '"'),
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

def queryHttpSettingInfo4Server(query_data):
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
        return result
    except Exception as e:
        logger.error(f"queryHttpSettingInfo|整体服务异常: {e}")
    finally:
        # 关闭游标和连接
        if cursor:
            cursor.close()
        if connection:
            connection.close()

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
        # 从数据库获取 filtered_apis、delete_apis 和 need_api
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # 使用 SQL 查询获取相关数据
        cursor.execute("SELECT need_api, filtered_apis, delete_apis FROM script_info WHERE script_name = %s", (current_file_name,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()

        if result:
            # 获取过滤的 API 和需要的 API
            filtered_apis_str = result['filtered_apis']
            delete_apis_str = result['delete_apis']
            need_api = result['need_api']

            # 将 filtered_apis 字符串转换为集合
            filtered_apis = set(filtered_apis_str.split('|')) if filtered_apis_str else set()

            # 将 delete_apis 字符串转换为集合
            delete_apis = set(delete_apis_str.split('|')) if delete_apis_str else set()

            return {
                "filtered_apis": filtered_apis,
                "delete_apis": delete_apis,
                "need_api": need_api
            }

        return None

    except Exception as e:
        logger.error(f"get_api_fifter|服务异常 current_file_name:{current_file_name}, 异常: {e}")
        return None


# 创建新页面并绑定监听器
def setup_page(page, current_file_name, unique_code):
    try:
        logger.info(f"setup_page|请求参数 current_file_name:{current_file_name},unique_code:{unique_code}")
        current_file_name = current_file_name.replace(".py", "")
        result = get_api_fifter(current_file_name)
        # 绑定请求监听器，传递过滤接口和记录的 API URL
        # page.on("request", lambda request: log_request(request, filtered_apis, need_api, current_file_name, unique_code))
        page.on("response", lambda response: log_response(response,
                                                          result.get("delete_apis", set()),
                                                          result.get("filtered_apis", set()),
                                                          result.get("need_api", None),
                                                          current_file_name,
                                                          unique_code))  # 设置响应的监听器
    except Exception as e:
        logger.error(f"setup_page|服务异常 current_file_name:{current_file_name},unique_code:{unique_code},{e}")
