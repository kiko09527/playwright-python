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


def save_script_log(script_name, post_data, mode, status, msg):
    cursor = None
    connection = None
    try:
        # 建立数据库连接
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # 生成 INSERT SQL 语句
        query = """
        INSERT INTO script_execute_log (script_name, post_data, mode, status, msg)
        VALUES (%s, %s, %s, %s, %s)
        """

        # 准备插入参数
        params = (script_name, post_data, mode, status, msg)

        # 执行插入操作
        cursor.execute(query, params)
        connection.commit()

        # 获取新插入记录的 ID
        log_id = cursor.lastrowid  # 获取最后插入记录的自增 ID

        logger.info(f"save_script_log|保存成功, log_id: {log_id} status:{status}")
        return log_id

    except mysql.connector.Error as e:
        logger.error(f"save_script_log|执行异常: {e}")
        return {"error": "数据库操作失败，请重试。"}

    except Exception as e:
        logger.error(f"save_script_log|其他异常: {e}")
        return {"error": "内部服务器错误，请稍后再试。"}

    finally:
        # 确保游标和连接都被关闭
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def insert_script_info(script_name, last_exec_status):
    logger.info(f"insert_script_info|请求参数 script_name: {script_name}, last_exec_status: {last_exec_status}")
    script_name = script_name.replace(".py", "")
    # 初始化数据库连接和游标
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # 插入记录的 SQL 查询，只包含 script_name 和 last_exec_status
        insert_query = """
            INSERT INTO script_info (script_name, last_exec_status)
            VALUES (%s, %s)
        """

        # 执行插入操作
        cursor.execute(insert_query, (script_name, last_exec_status))

        # 提交插入操作
        connection.commit()

        logger.info(f"insert_script_info|成功插入新的脚本信息，script_name: {script_name}")

    except Exception as e:
        logger.error(f"insert_script_info|数据库操作异常: {e}")
    finally:
        # 关闭游标和连接
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def update_script_execute_log(script_id, new_status, new_msg,script_name):
    logger.info(f"update_script_execute_log|请求参数 new_status: {new_status}")
    # 去掉 .py 后缀如果存在
    script_name = script_name.replace(".py", "")
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # 更新状态和消息的 SQL 查询
        update_query = """
            UPDATE script_execute_log 
            SET status = %s, msg = %s
            WHERE id = %s
        """
        # 执行更新操作
        cursor.execute(update_query, (new_status, json.dumps(new_msg), script_id))

        # 更新 script_info 表的 last_exec_status
        update_info_query = """
            UPDATE script_info 
            SET last_exec_status = %s
            WHERE script_name = %s
        """
        cursor.execute(update_info_query, (new_status, script_name))

        # 提交更新操作
        connection.commit()

        if cursor.rowcount == 0:
            logger.warning(f"update_script_execute_log|未找到 ID 为 {script_id} 的记录。")

    except Exception as e:
        logger.error(f"update_script_execute_log|数据库操作异常: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()