import os
import re
import uuid
from http_info import setup_page
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    try:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()
        current_file_name = os.path.basename(__file__)
        uuid_code =str(uuid.uuid1())
        print(f"确定:current_file_name: {current_file_name}")
        setup_page(page,current_file_name,uuid_code)
        page.on("popup", lambda p: setup_page(p,current_file_name,uuid_code))

        page.goto("https://sso-uat.gaojihealth.cn/login/#/")

        page.get_by_role("textbox", name="请输入工号/移动电话").click()
        page.get_by_role("textbox", name="请输入工号/移动电话").fill("")
        page.get_by_role("textbox", name="请输入密码").dblclick()
        page.get_by_role("textbox", name="请输入密码").fill("")
        page.get_by_role("button", name="登录").click()
        page.locator("div:nth-child(6) > img").click()
        with page.expect_popup() as page1_info:
            page.get_by_role("listitem").filter(has_text="").click()
        page1 = page1_info.value
        page1.get_by_role("button", name="积分商城连锁").click()
        page1.get_by_text("会员管理").click()
        page1.get_by_text("会员营销").click()
        page1.get_by_role("link", name="精准营销新版").click()
        page1.get_by_role("tab", name="人群运营计划看板").click()
        page1.get_by_role("button", name="新建计划").click()
        page1.get_by_role("heading", name="小程序外消息类触达").click()
        page1.get_by_role("button", name="创 建").click()
        page1.get_by_role("textbox", name="* 任务名称:").click()
        page1.get_by_role("textbox", name="* 任务名称:").fill("RPA创建精准营销")
        page1.get_by_text("请选择分组").click()
        page1.get_by_role("option", name="默认分组").click()
        page1.get_by_role('button', name='图标: plus 选择人群').click()
        page1.get_by_role('cell', name='高济精准营销任务1人群包').click()
        page1.get_by_role('textbox', name='输入人群名称').click()
        page1.get_by_role('textbox', name='输入人群名称').fill('高济精准营销任务1')
        page1.get_by_role('button', name='搜索').click()
        page1.get_by_role('cell', name='高济精准营销任务1人群包').click()
        page1.get_by_role('button', name='确定').click()
        page1.get_by_label('', exact=True).check()
        page1.get_by_role('button', name='确定').click()
        page1.get_by_text("请选择任务类型").click()
        page1.get_by_role("option", name="慢病随访").click()
        page1.get_by_role("spinbutton", name="* 统计天数 图标: question-circle :").click()
        page1.get_by_role("spinbutton", name="* 统计天数 图标: question-circle :").fill("10")
        page1.get_by_role("radio", name="手动定时运营").check()
        page1.get_by_role("radio", name="审核后立即发送").check()
        page1.get_by_role("button", name="图标: edit 查看维系渠道及内容").click()

        page1.get_by_text("发图文").click()
        page1.get_by_role("row", name="五一调休，本周日上班 2023-11-29 16:25:").get_by_label("").check()
        # 等待并尝试点击按钮
        try:
            page1.get_by_role("button", name="确定").click(timeout=3000)  # 尝试使用选择器点击
        except Exception as e:
            print(f"确定:貌似报错了1:Error clicking button: {e}")
            # 如果点击失败，使用 JavaScript 点击
            page1.evaluate("document.querySelector('button[type=\"button\"][class*=\"ant-btn-primary\"]').click();")
        try:
            page1.get_by_role("button", name="下一步").click(timeout=3000)  # 尝试使用选择器点击
        except Exception as e:
            print(f"下一步:貌似报错了:Error clicking button: {e}")
            # 如果点击失败，使用 JavaScript 点击
            page1.evaluate("document.querySelector('button[type=\"button\"][class*=\"ant-btn-primary\"]').click();")
        try:
            page1.get_by_role("button", name="提交审核").click(timeout=3000)  # 尝试使用选择器点击
        except Exception as e:
            print(f"提交审核:貌似报错了:Error clicking button: {e}")
            # 如果点击失败，使用 JavaScript 点击
            page1.evaluate("document.querySelector('button[type=\"button\"][class*=\"ant-btn-primary\"]').click();")

        # 等待一段时间以确保请求完成
        page1.wait_for_timeout(5000)
    finally:
        context.tracing.stop(path='精准营销慢病任务通知_test_.zip')
        context.close()
        browser.close()


with sync_playwright() as playwright:
    run(playwright)
