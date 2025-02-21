from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from http_info import setup_page
from playwright.sync_api import Playwright, sync_playwright
import os
import uuid

app = FastAPI()

# 定义请求参数模型
class PromotionRequest(BaseModel):
    script_name: str          # 脚本名称
    username: str          # 工号/移动电话
    password: str          # 登录密码
    task_name: str         # 任务名称
    member_group: str      # 成员组
    task_type: str         # 任务类型
    stats_days: int        # 统计天数
    contact_mode: str      # 联系方式（发短信/发图文）

class PromotionResponse(BaseModel):
    success: bool          # 操作成功与否

def run(playwright: Playwright, request: PromotionRequest) -> bool:
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

        # 登录操作
        page.goto("https://sso-uat.gaojihealth.cn/login/#/")
        page.get_by_role("textbox", name="请输入工号/移动电话").fill(request.username)
        page.get_by_role("textbox", name="请输入密码").fill(request.password)
        page.get_by_role("button", name="登录").click()
        page.locator("div:nth-child(6) > img").click()

        with page.expect_popup() as page1_info:
            page.get_by_role("listitem").filter(has_text=request.username).click()
        page1 = page1_info.value

        # 进入会员管理
        page1.get_by_role("button", name="积分商城连锁").click()
        page1.get_by_text("会员管理").click()
        page1.get_by_text("会员营销").click()
        page1.get_by_role("link", name="精准营销新版").click()
        page1.get_by_role("tab", name="人群运营计划看板").click()
        page1.get_by_role("button", name="新建计划").click()

        # 设置任务信息
        page1.get_by_role("heading", name="小程序外消息类触达").click()
        page1.get_by_role("button", name="创 建").click()
        page1.get_by_role("textbox", name="* 任务名称:").fill(request.task_name)
        page1.get_by_text("请选择分组").click()
        page1.get_by_role("option", name=request.member_group).click()

        # 选择人群
        page1.get_by_role("button", name="图标: plus 选择人群").click()
        page1.get_by_role("row", name="会员等级测试项目1人群包").get_by_label("").check()
        page1.get_by_role("button", name="确定").click()

        # 设置任务类型
        page1.get_by_text("请选择任务类型").click()
        page1.get_by_role("option", name=request.task_type).click()
        page1.get_by_role("spinbutton", name="* 统计天数 图标: question-circle :").fill(str(request.stats_days))

        # 选择联系模式
        if request.contact_mode == "发短信":
            page1.get_by_text("发短信").click()
            # 添加更多的发短信相关操作

        elif request.contact_mode == "发图文":
            page1.get_by_text("发图文").click()
            # 添加更多的发图文相关操作

        # 提交审核
        page1.get_by_role("button", name="下一步").click()
        page1.get_by_role("button", name="提交审核").click()

        # 若所有操作顺利完成，返回 True
        return True

    except Exception as e:
        print(f"发生错误: {e}")
        # 出现异常时返回 False
        return False
    finally:
        context.tracing.stop(path='33.zip')
        context.close()
        browser.close()

@app.post("/execute", response_model=PromotionResponse)
def execute(request: PromotionRequest):
    with sync_playwright() as playwright:
        success = run(playwright, request)
    return PromotionResponse(success=success)
