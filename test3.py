import ast
import astor


class CodeModifier(ast.NodeTransformer):
    def __init__(self):
        super().__init__()

    def visit_FunctionDef(self, node):
        # 只处理名为 'run' 的函数
        if node.name == 'run':
            # 创建 try 和 finally 节点
            try_node = ast.Try(
                body=[],  # 将原来的函数体清空，将其重新加入
                handlers=[],  # 没有处理块
                orelse=[],  # 没有其他分支
                finalbody=[]
            )

            # 在函数体中查找 page = context.new_page() 的调用
            for i, stmt in enumerate(node.body):
                if (
                        isinstance(stmt, ast.Assign) and
                        len(stmt.targets) == 1 and
                        isinstance(stmt.targets[0], ast.Name) and
                        stmt.targets[0].id == 'page' and
                        isinstance(stmt.value, ast.Call) and
                        hasattr(stmt.value.func, 'attr') and
                        stmt.value.func.attr == 'new_page'
                ):
                    get_current_file_name_call = ast.Expr(
                        value=ast.Assign(
                            targets=[ast.Name(id='current_file_name', ctx=ast.Store())],
                            value=ast.Call(
                                func=ast.Attribute(
                                    value=ast.Name(id='os', ctx=ast.Load()),
                                    attr='path.basename',
                                    ctx=ast.Load()
                                ),
                                args=[ast.Name(id='__file__', ctx=ast.Load())],  # 修改此行,
                                keywords=[]
                            ),
                        )
                    )
                    # 生成唯一代码
                    unique_code_call = ast.Expr(
                        value=ast.Assign(
                            targets=[ast.Name(id='unique_code', ctx=ast.Store())],
                            value=ast.Call(
                                func=ast.Name(id='str', ctx=ast.Load()),  # str() 函数
                                args=[
                                    ast.Call(
                                        func=ast.Attribute(value=ast.Name(id='uuid', ctx=ast.Load()), attr='uuid1', ctx=ast.Load()),
                                        args=[],
                                        keywords=[]
                                    )
                                ],
                                keywords=[]
                            )
                        )
                    )
                    # 在 page = context.new_page() 后插入 setup_page(page) 和 page.on(...)
                    setup_page_call = ast.Expr(
                        value=ast.Call(
                            func=ast.Name(id='setup_page', ctx=ast.Load()),
                            args=[
                                stmt.targets[0],  # 使用 page 变量
                                ast.Name(id='current_file_name', ctx=ast.Load()),  # 使用文件名变量
                                ast.Name(id='unique_code', ctx=ast.Load())  # 新增唯一代码
                            ],
                            keywords=[]
                        )
                    )
                    # 3. 创建处理 popup 事件的 lambda
                    # 创建处理 popup 事件的 lambda
                    setup_popup_call = ast.Expr(
                        value=ast.Call(
                            func=ast.Attribute(
                                value=stmt.targets[0],  # page 变量
                                attr='on',
                                ctx=ast.Load()
                            ),
                            args=[
                                ast.Constant(value='popup'),
                                ast.Lambda(
                                    args=ast.arguments(
                                        args=[ast.arg(arg='p', annotation=None)],
                                        vararg=None,
                                        kwonlyargs=[],
                                        kw_defaults=[],
                                        kwarg=None,
                                        defaults=[]
                                    ),
                                    body=ast.Call(
                                        func=ast.Name(id='setup_page', ctx=ast.Load()),
                                        args=[
                                            ast.Name(id='p', ctx=ast.Load()),
                                            ast.Name(id='current_file_name', ctx=ast.Load()),  # 使用文件名变量
                                            ast.Name(id='unique_code', ctx=ast.Load())  # 新增唯一代码
                                        ],
                                        keywords=[]
                                    )
                                )
                            ],
                            keywords=[]
                        )
                    )

                    # 插入语句到节点中
                    node.body.insert(i + 1, get_current_file_name_call)
                    node.body.insert(i + 2, unique_code_call)  # 插入生成唯一代码的调用
                    node.body.insert(i + 3, setup_page_call)
                    node.body.insert(i + 4, setup_popup_call)

            # 在原代码的函数体中插入到 try 块
            for stmt in node.body:
                if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                    # 检查是否为 context.close() 或 browser.close()
                    if hasattr(stmt.value.func, 'attr') and (stmt.value.func.attr == 'close'):
                        continue  # 跳过这两个调用
                try_node.body.append(stmt)

            try_node.finalbody.append(
                ast.Expr(value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Attribute(
                            value=ast.Name(id='context', ctx=ast.Load()),
                            attr='tracing',
                            ctx=ast.Load()
                        ),
                        attr='stop',
                        ctx=ast.Load()
                    ),
                    args=[],  # args 不需要参数，因为我们使用关键字参数
                    keywords=[ast.keyword(arg='path', value=ast.Constant(value="12121.zip"))]  # 使用双引号
                ))
            )

            # 添加上下文和浏览器关闭的代码到 finally
            try_node.finalbody.append(
                ast.Expr(value=ast.Call(
                    func=ast.Attribute(value=ast.Name(id='context', ctx=ast.Load()), attr='close', ctx=ast.Load()),
                    args=[],
                    keywords=[]
                ))
            )
            try_node.finalbody.append(
                ast.Expr(value=ast.Call(
                    func=ast.Attribute(value=ast.Name(id='browser', ctx=ast.Load()), attr='close', ctx=ast.Load()),
                    args=[],
                    keywords=[]
                ))
            )

            # 始终在 context 赋值后，插入 context.tracing.start
            for i, stmt in enumerate(try_node.body):
                if isinstance(stmt, ast.Assign) and isinstance(stmt.targets[0], ast.Name) and stmt.targets[
                    0].id == 'context':
                    tracing_start_stmt = ast.Expr(
                        value=ast.Call(
                            func=ast.Attribute(value=stmt.targets[0], attr='tracing.start', ctx=ast.Load()),
                            args=[],
                            keywords=[
                                ast.keyword(arg='screenshots', value=ast.Constant(value=True)),
                                ast.keyword(arg='snapshots', value=ast.Constant(value=True)),
                                ast.keyword(arg='sources', value=ast.Constant(value=True)),
                            ]
                        )
                    )
                    try_node.body.insert(i + 1, tracing_start_stmt)

            node.body = [try_node]  # 替换函数体为 try/finally 结构

        return node

    def visit_ImportFrom(self, node):
        # 检查这个导入是否是 playwright.sync_api
        if node.module == "playwright.sync_api":
            # 创建 http_info 的导入节点
            new_import = ast.ImportFrom(
                module='http_info',
                names=[ast.alias(name='setup_page', asname=None)],
                level=0
            )
            # 创建 os 的导入节点
            os_import = ast.Import(names=[ast.alias(name='os', asname=None)])
            uuid_import = ast.Import(names=[ast.alias(name='uuid', asname=None)])

            # 在 playwright 导入上方插入 http_info 和 os 导入
            return [uuid_import,os_import, new_import, node]  # 确保 os_import 在前
        return node


def modify_code(source_code):
    # 解析源代码为 AST
    tree = ast.parse(source_code)
    # 在 AST 中插入 try-finally 结构和 tracing 代码
    modified_tree = CodeModifier().visit(tree)
    # 转换为源代码
    return astor.to_source(modified_tree)


# 原始 Python 代码
original_code = """
from playwright.sync_api import Playwright, sync_playwright

def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://sso-uat.gaojihealth.cn/login/#/")
    page.get_by_role("textbox", name="请输入工号/移动电话").click()
    page.get_by_role("textbox", name="请输入工号/移动电话").fill("12121")
    page.get_by_role("textbox", name="请输入密码").click()
    page.get_by_role("textbox", name="请输入密码").fill("1212121")
    page.get_by_role("textbox", name="请输入工号/移动电话").click()

    context.close()  # 这一行将被移除
    browser.close()  # 这一行将被移除

with sync_playwright() as playwright:
    run(playwright)
"""

# 修改代码，默认添加 tracing 逻辑
modified_code = modify_code(original_code)

# 输出修改后的代码
print(modified_code)
