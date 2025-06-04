import schedule
import time
from datetime import datetime
import threading
import mysql.connector
import logging
from routes.file_api import execute_script
from config.db_config import db_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
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
            logger.info("任务执行线程已启动")

    def stop(self):
        """停止定时器"""
        self.running = False
        if self.thread:
            self.thread.join()
            logger.info("任务执行线程已停止")

    def _run_scheduler(self):
        """运行调度器"""
        logger.info("调度器开始运行")
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def check_and_execute_tasks(self):
        logger.info("========== 开始检查任务 ==========")
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
            
            if not result:
                logger.info("没有找到需要执行的任务")
                return
                
            logger.info(f"共找到 {len(result)} 个待检查任务")
            executed_tasks = []
            non_executed_tasks = []
            
            for row in result:
                script_name = row['script_name']
                execute_mode = row['execute_mode']
                execute_time = row['execute_time']
                execute_cycle_time = row['execute_cycle_time']

                logger.info(f"检查脚本: {script_name}, 执行模式: {execute_mode}")
                
                if execute_mode == 'specified':
                    # 检查是否到达指定执行时间
                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    logger.info(f"  - 当前时间: {current_time}, 计划执行时间: {execute_time}")
                    
                    if current_time >= execute_time:
                        logger.info(f"  - 脚本 [{script_name}] 已达到指定执行时间，开始执行")
                        # 执行脚本
                        try:
                            execute_script(script_name)
                            executed_tasks.append(script_name)
                            logger.info(f"  - 脚本 [{script_name}] 执行完成")
                            
                            # 更新执行时间，避免重复执行
                            update_query = """
                                UPDATE script_info 
                                SET execute_time = NULL 
                                WHERE script_name = %s
                            """
                            cursor.execute(update_query, (script_name,))
                            connection.commit()
                            logger.info(f"  - 已清除脚本 [{script_name}] 的执行时间，防止重复执行")
                        except Exception as e:
                            logger.error(f"  - 执行脚本 [{script_name}] 时出错: {str(e)}")
                    else:
                        non_executed_tasks.append({
                            "name": script_name, 
                            "reason": f"尚未到达执行时间，计划时间: {execute_time}"
                        })
                        logger.info(f"  - 脚本 [{script_name}] 尚未到达执行时间，跳过")

                elif execute_mode == 'cycle':
                    # 设置周期执行任务
                    logger.info(f"  - 为脚本 [{script_name}] 设置 {execute_cycle_time} 分钟周期执行任务")
                    
                    def execute_with_logging(script_name=script_name):
                        logger.info(f"  - 周期执行脚本 [{script_name}]")
                        try:
                            execute_script(script_name)
                            logger.info(f"  - 脚本 [{script_name}] 周期执行完成")
                            return True
                        except Exception as e:
                            logger.error(f"  - 执行脚本 [{script_name}] 时出错: {str(e)}")
                            return False
                    
                    schedule.every(execute_cycle_time).minutes.do(execute_with_logging)
                    non_executed_tasks.append({
                        "name": script_name, 
                        "reason": f"已设置为每 {execute_cycle_time} 分钟周期执行"
                    })

            # 打印执行总结
            logger.info("========== 任务检查执行总结 ==========")
            if executed_tasks:
                logger.info(f"本次执行的脚本 ({len(executed_tasks)}): {', '.join(executed_tasks)}")
            else:
                logger.info("本次没有执行任何脚本")
                
            if non_executed_tasks:
                logger.info(f"未执行的脚本 ({len(non_executed_tasks)}):")
                for task in non_executed_tasks:
                    logger.info(f"  - {task['name']}: {task['reason']}")

        except Exception as e:
            logger.error(f"任务检查过程中发生错误: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()
            logger.info("========== 任务检查结束 ==========")

# 创建定时器实例
task_executor = TaskExecutor()

def start_task_executor():
    """启动任务执行器"""
    task_executor.start()
    # 每分钟检查一次任务
    schedule.every(1).minutes.do(task_executor.check_and_execute_tasks)
    logger.info("定时任务执行器已启动，每分钟检查一次任务")

if __name__ == "__main__":
    start_task_executor()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        task_executor.stop()
