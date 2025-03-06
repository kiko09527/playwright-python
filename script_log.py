import logging
import json
import mysql.connector
from config.db_config import db_config
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
responses = []

# 数据库连接配置


def query_script_info(script_name):
    logger.info(f"query_script_info|请求参数 script_name: {script_name}")
    script_name = script_name.replace(".py", "")
    # 初始化数据库连接和游标
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)  # 使用字典方式获取结果
        # 查询脚本信息的 SQL 查询
        query = "SELECT * FROM script_info WHERE script_name = %s"
        # 执行查询操作
        cursor.execute(query, (script_name,))
        result = cursor.fetchone()  # 获取第一条记录
        if result:
            logger.info(f"query_script_info|找到记录: {result}")
            return result  # 返回找到的记录
        else:
            logger.warning(f"query_script_info|未找到脚本名称 '{script_name}' 的记录。")
            return None  # 没有找到对应记录
    except Exception as e:
        logger.error(f"query_script_info|数据库操作异常: {e}")
        return None  # 如果出现异常，返回 None
    finally:
        # 关闭游标和连接
        if cursor:
            cursor.close()
        if connection:
            connection.close()


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


def update_script_execute_log(script_id, new_status, new_msg, script_name):
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

    except Exception as e:
        logger.error(f"update_script_execute_log|数据库操作异常: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def update_script_execute_log_api(script_id, new_status, new_msg, script_name, totalCount, currentCount):
    logger.info(f"update_script_execute_log_api|请求参数 new_status: {new_status}")
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
        if totalCount > 1:
            new_status = f"【{new_status}】"
        # 根据 currentCount 的值更新 script_info 表的 last_exec_status
        if currentCount == 1:
            update_info_query = """
                UPDATE script_info 
                SET last_exec_status = %s
                WHERE script_name = %s
            """
            cursor.execute(update_info_query, (new_status, script_name))
        else:
            update_info_query = """
                UPDATE script_info 
                SET last_exec_status =  CONCAT(last_exec_status, %s)
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
