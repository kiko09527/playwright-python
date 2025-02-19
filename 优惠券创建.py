import re
import os
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
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
        page1.locator("div").filter(has_text=re.compile(r"^营销管理$")).click()
        page1.get_by_text("卡券管理").click()
        page1.get_by_role("link", name="优惠券模板", exact=True).click()
        page1.get_by_role("button", name="创建通用劵").click()
        page1.get_by_role("textbox", name="* 模板名称:").click()
        page1.get_by_role("textbox", name="* 模板名称:").fill("测试001")

        # 找到文件输入框并上传文件
        file_input = page1.locator('input[type="file"]')
        file_input.set_input_files('111.png')

        # 等待上传完成，检查是否有新的 <img> 元素
        uploaded_image = page1.locator('input[type="file"] + img')

        page1.get_by_text("请选择").first.click()
        page1.get_by_role("option", name="门店核销 图标: check").click()
        page1.locator("[id=\"couponChannel\\[\\\"singleChannels\\\"\\]\\[0\\]\"]").get_by_text("请选择").click()
        page1.get_by_role("option", name="精准营销类").click()
        page1.locator("[id=\"couponChannel\\[\\\"singleChannels\\\"\\]\\[1\\]\"]").get_by_text("请选择").click()
        page1.get_by_role("option", name="定向营销").click()
        page1.locator("#type div").nth(1).click()
        page1.get_by_role("option", name="满减券").click()
        page1.get_by_role("textbox", name="* 面值:").click()
        page1.get_by_role("textbox", name="* 面值:").fill("10")
        page1.get_by_role("textbox", name="* 券数量:").click()
        page1.get_by_role("textbox", name="* 券数量:").fill("100")
        page1.get_by_role("radio", name="满 元 可用").check()
        page1.locator("#full").click()
        page1.locator("#full").fill("100")
        page1.get_by_role("button", name="下一步").click()
        page1.get_by_role("textbox", name="开始时间").click()
        page1.get_by_text("14", exact=True).click()
        page1.get_by_role("button", name="确 定").click()
        page1.get_by_title("年2月28日").locator("div").click()
        page1.get_by_role("button", name="确 定").click()
        page1.get_by_role("radio", name="领用后 天生效 天失效").check()
        page1.locator("#delayEffect").click()
        page1.locator("#delayEffect").fill("1")
        page1.locator("#delayDisable").click()
        page1.locator("#delayDisable").fill("10")
        page1.locator("#getLimit").click()
        page1.locator("#getLimit").fill("2")
        page1.get_by_role("textbox", name="消费提示:").click()
        page1.get_by_role("textbox", name="消费提示:").fill("消费提示")
        page1.get_by_role("textbox", name="* 优惠说明:").click()
        page1.get_by_role("textbox", name="* 优惠说明:").fill("优惠说明")
        page1.locator("label").filter(has_text="所有门店").locator("span").nth(1).click()
        page1.get_by_role("radio", name="所有门店").check()
        page1.get_by_role("button", name="下一步").click()
        page1.get_by_role("button", name="启用").click()
        page1.get_by_role("button", name="确定").click()
        # ---------------------
        context.close()
        browser.close()



with sync_playwright() as playwright:
    run(playwright)