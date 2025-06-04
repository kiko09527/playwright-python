from datetime import datetime, timedelta
import platform

class DateUtils:
    """日期工具类（修复版）"""

    @classmethod
    def _get_format_str(cls, fmt: str) -> str:
        """处理跨平台格式化符号差异"""
        return fmt.replace('%-', '%#') if platform.system() == 'Windows' else fmt

    @classmethod
    def get_month_end_day(cls) -> str:
        """获取当月最后一天的日部分（无前导零）"""
        # 核心计算逻辑
        today = datetime.now()
        next_month = today.replace(day=28) + timedelta(days=4)
        last_day = next_month - timedelta(days=next_month.day)
        return str(last_day.day)

    @classmethod
    def get_current_month_day(cls) -> str:
        """获取当天日期的月日部分（格式：年X月X日）"""
        now = datetime.now()
        fmt = cls._get_format_str("年%m月%d日")
        return now.strftime(fmt).replace("年0", "年").replace("月0", "月")  # 移除前导零

    @classmethod
    def get_current_day(cls) -> str:
        """获取当天日部分（无前导零），返回字符串类型"""
        return str(datetime.now().day)  # 直接转换自然去除前导零


    @classmethod
    def get_tomorrow_day(cls) -> str:
        """获取明天日期的日部分（无前导零）"""
        tomorrow = datetime.now() + timedelta(days=1)
        result = str(tomorrow.day)
        return result

    @classmethod
    def get_one_week_later_day(cls) -> str:
        """获取一周后的日部分（无前导零）"""
        target_date = datetime.now() + timedelta(days=7)
        result = str(target_date.day)
        return result

# 在测试用例中调用
def test_date_utils():
    print("当前日期：", DateUtils.get_current_day())
    print("月末日期：", DateUtils.get_month_end_day())
    print("完整格式：", DateUtils.get_current_month_day())
    print("明天日期：", DateUtils.get_tomorrow_day())
    print("一周后日期：", DateUtils.get_one_week_later_day())

# 执行测试
if __name__ == "__main__":
    test_date_utils()
