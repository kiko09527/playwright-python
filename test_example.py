import re
import os
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    try:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()
        page.goto("https://sso-uat.gaojihealth.cn/login/#/")
        page.get_by_role("textbox", name="请输入工号/移动电话").click()
        page.get_by_role("textbox", name="请输入工号/移动电话").fill("13581791523")
        page.get_by_role("textbox", name="请输入密码").dblclick()
    finally:
        context.tracing.stop(path = "111.zip")
        context.close()
        browser.close()


with sync_playwright() as playwright:
    run(playwright)