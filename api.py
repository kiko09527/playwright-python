import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page()

        # 记录请求和响应信息
        requests = []
        responses = []

        # 监听请求
        async def log_request(request):
            if "api-test.gaojihealth.cn" in request.url:
                requests.append({
                    "url": request.url,
                    "method": request.method,
                    "post_data": request.post_body
                })
                print(f"Request URL: {request.url}")

        # 监听响应
        async def log_response(response):
            if "api-test.gaojihealth.cn" in response.url:
                body = await response.body()
                responses.append({
                    "url": response.url,
                    "status": response.status,
                    "body": body.decode('utf-8')
                })
                print(f"Response URL: {response.url}")

        page.on("request", log_request)
        page.on("response", log_response)

        # 访问页面
        await page.goto("https://mobile-test.gaojihealth.cn/haidian/integralExchangeB?businessId=99999&storeId=87446199999&userId=230980788099999&platformUserId=264452024993329&userIntegral=4862.51&digitalUserId=229599678210000&up=17601259793&dictMap=eyJuYW1lIjoiZGlhbiIsImVycENvZGUiOiIxMjMwOTgwNzg4MDk5OTk5In0=&uuidKey=HD")

        # 等待页面加载一段时间
        await page.wait_for_timeout(5000)  # 等待5秒以捕获请求和响应

        # 你可以在这里处理请求和响应数据
        print("\n--- Summary of Requests ---")
        for request in requests:
            print(request)

        print("\n--- Summary of Responses ---")
        for response in responses:
            print(response)

        await browser.close()

# 运行异步函数
asyncio.run(run())