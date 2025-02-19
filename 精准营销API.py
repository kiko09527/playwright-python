import re
from fastapi import FastAPI
from playwright.sync_api import sync_playwright

app = FastAPI()

@app.get("/run-playwright")
def run_playwright():
    def run(playwright: Playwright) -> None:
        # 定义运行 Playwright 的函数
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        # 存储请求和响应
        requests = []
        responses = []

        # 监听请求事件
        def log_request(request):
            if "api-store-test.gaojihealth.cn" in request.url:
                requests.append({
                    "url": request.url,            # 请求的 URL
                    "method": request.method,      # 请求方法（GET, POST等）
                    "post_data": request.post_data,    # POST 数据（如果有的话）
                    "headers": request.headers,    # 请求头
                })
                print(f"Request URL: {request.url}")

        def log_response(response):
            if "api-store-test.gaojihealth.cn" in response.url:
                responses.append({
                    "url": response.url,
                    "status": response.status,
                    "body": response.body()
                })
                print(f"Response URL: {response.url}")
        # 创建新页面并绑定监听器
        def setup_page(page):
            page.on("request", log_request)
            page.on("response", log_response)
        page = context.new_page()
        setup_page(page)
        page.on("popup", lambda p: setup_page(p))

        page.goto("https://sso-uat.gaojihealth.cn/login/#/")

        page.get_by_role("textbox", name="请输入工号/移动电话").click()
        page.get_by_role("textbox", name="请输入工号/移动电话").fill("13581791523")
        page.get_by_role("textbox", name="请输入密码").dblclick()
        page.get_by_role("textbox", name="请输入密码").fill("Xifan@1007")
        page.get_by_role("button", name="登录").click()
        page.locator("div:nth-child(6) > img").click()
        with page.expect_popup() as page1_info:
            page.get_by_role("listitem").filter(has_text="13581791523").click()
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
        page1.get_by_role("textbox", name="* 任务名称:").fill("自动化测试001")
        page1.get_by_text("请选择分组").click()
        page1.get_by_role("option", name="默认分组").click()
        page1.get_by_role("button", name="图标: plus 选择人群").click()
        page1.get_by_role("row", name="高济测试人群包2025-02-15 13:20:20 - -").get_by_label("").check()
        page1.get_by_role("button", name="确定").click()
        page1.get_by_text("请选择任务类型").click()
        page1.get_by_role("option", name="慢病随访").click()
        page1.get_by_role("spinbutton", name="* 统计天数 图标: question-circle :").click()
        page1.get_by_role("spinbutton", name="* 统计天数 图标: question-circle :").fill("10")
        page1.get_by_role("radio", name="手动定时运营").check()
        page1.get_by_role("radio", name="审核后立即发送").check()
        page1.get_by_role("button", name="图标: edit 查看维系渠道及内容").click()

        # page1.get_by_text("发短信").click()
        # page1.get_by_role("button", name="图标: plus 选择短信模板").click()
        # page1.get_by_role("row", name="大促活动 审核通过 2025-02-08 15:57:19").get_by_label("").check()
        # page1.get_by_label("选择短信模板").get_by_role("button", name="确定").click()
        # page1.get_by_role("button", name="确定").click()

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
        # 打印请求和响应信息
        print("\n--- Summary of Requests ---")
        # for req in requests:
        #     print(req)
        #
        # print("\n--- Summary of Responses ---")
        # for resp in responses:
        #     # 注意：如果body是bytes，需进行解码
        #     if isinstance(resp["body"], bytes):
        #         print(f"Response URL: {resp['url']}, Status: {resp['status']}, Body: {resp['body'].decode('utf-8')}")
        #     else:
        #         print(f"Response URL: {resp['url']}, Status: {resp['status']}, Body: {resp['body']}")
        # ---------------------
        context.close()
        browser.close()

        with sync_playwright() as playwright:
            run(playwright)

    return {"message": "Playwright run completed."}

# 启动服务