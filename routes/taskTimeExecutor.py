import schedule
import time
from datetime import datetime
import threading
import mysql.connector
import os
import sys
import subprocess
from routes.file_api import execute_script
from config.db_config import db_config

class TaskExecutor:
    def __init__(self):
        self.running = False
        self.thread = None

    def start(self):
        """启动定时器"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_scheduler)
            self.thread.daemon = True
            self.thread.start()

    def stop(self):
        """停止定时器"""
        self.running = False
        if self.thread:
            self.thread.join()

    def _run_scheduler(self):
        """运行调度器"""
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def check_and_execute_tasks(self):
        """检查并执行任务"""
        try:
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor(dictionary=True)
            
            # 查询所有需要执行的任务
            query = """
                SELECT script_name, execute_mode, execute_time, execute_cycle_time 
                FROM script_info 
                WHERE execute_mode IS NOT NULL 
                AND ((execute_mode = 'specified' AND execute_time IS NOT NULL) 
                OR (execute_mode = 'cycle' AND execute_cycle_time IS NOT NULL))
            """
            cursor.execute(query)
            result = cursor.fetchall()
            
            for row in result:
                script_name = row['script_name']
                execute_mode = row['execute_mode']
                execute_time = row['execute_time']
                execute_cycle_time = row['execute_cycle_time']

                if execute_mode == 'specified':
                    # 检查是否到达指定执行时间
                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    if current_time >= execute_time:
                        # 执行脚本
                        execute_script(script_name)
                        # 更新执行时间，避免重复执行
                        update_query = """
                            UPDATE script_info 
                            SET execute_time = NULL 
                            WHERE script_name = %s
                        """
                        cursor.execute(update_query, (script_name,))
                        connection.commit()

                elif execute_mode == 'cycle':
                    # 设置周期执行任务
                    schedule.every(execute_cycle_time).minutes.do(
                        lambda: execute_script(script_name)
                    )

        except Exception as e:
            print(f"Error in check_and_execute_tasks: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()

# 创建定时器实例
task_executor = TaskExecutor()

def start_task_executor():
    """启动任务执行器"""
    task_executor.start()
    # 每分钟检查一次任务
    schedule.every(1).minutes.do(task_executor.check_and_execute_tasks)
    print("定时任务执行器已启动")

if __name__ == "__main__":
    start_task_executor()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        task_executor.stop()
