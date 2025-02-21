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

        logger.info(f"save_script_log|执行成功, log_id: {log_id}")
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


def update_script_execute_log(script_id, new_status, new_msg):
    logger.error(f"update_script_execute_log|修改状态new_status: {new_status}")
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # 更新状态和消息的 SQL 查询
        update_query = """
            UPDATE script_execute_log 
            SET status = %s, msg = %s, update_time = NOW() 
            WHERE id = %s
        """
        # 执行更新操作
        cursor.execute(update_query, (new_status, json.dumps(new_msg), script_id))

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
