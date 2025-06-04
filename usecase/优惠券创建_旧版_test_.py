import re
import uuid
import os
from http_info import setup_page
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) ->None:
    try:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()
        current_file_name = os.path.basename(__file__)
        unique_code = str(uuid.uuid1())
        setup_page(page, current_file_name, unique_code)
        page.on('popup', lambda p: setup_page(p, current_file_name,
            unique_code))
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
     
        page1.get_by_text('营销管理').click()
        page1.get_by_text('卡券管理').click()
        page1.get_by_role('link', name='优惠券模板', exact=True).click()
        page1.get_by_role('button', name='创建通用劵').click()
        page1.get_by_role('textbox', name='* 模板名称:').click()
        page1.get_by_role('textbox', name='* 模板名称:').fill('旧版通用券录制')
                # 找到文件输入框并上传文件
        file_input = page1.locator('input[type="file"]')
        file_input.set_input_files('111.png')

        # 等待上传完成，检查是否有新的 <img> 元素
        uploaded_image = page1.locator('input[type="file"] + img')
        # page1.get_by_role('button', name='图标: plus 上传').click()
        # page1.get_by_role('button', name='图标: plus 上传').set_input_files(
        #     '006MqdVuly1hj61pxuhwfj30qo0uj0uw.jpg')
        page1.get_by_text('请选择').first.click()
        page1.get_by_role('option', name='门店核销 图标: check').click()
        page1.locator('[id="couponChannel\\[\\"singleChannels\\"\\]\\[0\\]"]'
            ).get_by_text('请选择').click()
        page1.get_by_role('option', name='主题活动类').click()
        page1.locator('[id="couponChannel\\[\\"singleChannels\\"\\]\\[1\\]"]'
            ).get_by_text('请选择').click()
        page1.get_by_role('option', name='会员日优惠券', exact=True).click()
        page1.locator('#type').get_by_text('请选择').click()
        page1.get_by_role('option', name='满减券').click()
        page1.get_by_role('textbox', name='* 面值:').click()
        page1.get_by_role('textbox', name='* 面值:').fill('9')
        page1.get_by_role('textbox', name='* 券数量:').click()
        page1.get_by_role('textbox', name='* 券数量:').fill('9')
        page1.get_by_role('button', name='下一步').click()

        page1.get_by_role("textbox", name="开始时间").click()
        page1.get_by_text("22", exact=True).click()
        page1.get_by_role("button", name="确 定").click()
        page1.get_by_role("radio", name="领用后 天生效 天失效").check()
        page1.get_by_role("textbox", name="结束时间").click()
        page1.get_by_text("30", exact=True).click()
        page1.get_by_role("button", name="确 定").click()
        page1.get_by_role("radio", name="固定时间 ~ 图标: calendar").check()
        page1.get_by_role("textbox", name="开始日期").click()
        page1.get_by_title("年4月22日").locator("div").click()
        page1.get_by_text("30", exact=True).first.click()
        page1.get_by_role("button", name="确 定").click()
        page1.locator("#getLimit").click()
        page1.locator("#getLimit").fill("10")
        page1.get_by_role("textbox", name="消费提示:").click()
        page1.get_by_role("textbox", name="消费提示:").fill("消费提示")
        page1.get_by_role("textbox", name="* 优惠说明:").click()
        page1.get_by_role("textbox", name="* 优惠说明:").fill("优惠说明")
        page1.get_by_role("textbox", name="客服电话:").click()
        page1.get_by_role("textbox", name="客服电话:").fill("15711257768")
        page1.get_by_role("radio", name="所有门店").check()
        page1.get_by_role("radio", name="无限制").check()
        page1.get_by_role("radio", name="不验证").check()
        page1.get_by_role("radio", name="参与叠加优惠券的使用 图标: question-circle").check()
        page1.get_by_role("button", name="下一步").click()
        page1.get_by_role("button", name="启用").click()
        page1.get_by_role("button", name="确定").click()
    finally:
        context.tracing.stop(path='旧版通用券创建_test_.zip')
        context.close()
        browser.close()


with sync_playwright() as playwright:
    run(playwright)
