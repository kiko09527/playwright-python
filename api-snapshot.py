from flask import Flask, request, jsonify
import subprocess
import os
import logging
import genera_python_code

app = Flask(__name__)
# 设置文件上传目录为项目根目录
UPLOAD_FOLDER = os.getcwd()  # 根目录
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@app.route('/trace', methods=['GET'])
def trace():
    # 从查询参数中获取 trace 文件名和测试文件名
    test_file_name = request.args.get('test_file_name', 'test_example.py')  # 默认值
    logger.info(f"trace|请求参数:test_file_name={test_file_name}")
    # 确保 test 文件名以 .py 结尾
    if not test_file_name.endswith('.py'):
        test_file_name += '.py'

    # 构建 pytest 命令
    command = ['pytest', '--trace', test_file_name]

    # 执行 pytest 命令
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return jsonify({
            'status': 'success',
            'output': result.stdout
        }), 200
    except Exception as e:
        logger.error(f"trace|当前测试文件回溯异常{e}")
        return jsonify({
            'status': 'error',
            'output': e.stderr
        }), 500


@app.route("/codegen", methods=["GET"])
def codegen():
    url = request.args.get("url")
    if not url:
        return jsonify({"detail": "URL parameter is required"}), 400

    try:
        # 调用 playwright codegen 命令
        command = ["playwright", "codegen", url]
        process = subprocess.run(command, capture_output=True, text=True)

        # 检查命令是否成功执行
        if process.returncode != 0:
            return jsonify({"error": process.stderr.strip()}), 500

        # 返回生成的代码
        return jsonify({"generated_code": process.stdout.strip()})

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/execute', methods=['GET'])
def execute_script():
    try:
        # 从查询参数获取文件名
        script_name = request.args.get('name')

        if not script_name:
            return jsonify({"error": "No script name provided."}), 400

        # 获取当前工作目录
        current_directory = os.getcwd()

        # 确保脚本是 `.py` 文件，并构建完整路径
        if not script_name.endswith('.py'):
            return jsonify({"error": "Invalid script name. It must end with .py."}), 400

        script_path = os.path.join(current_directory, script_name)

        # 检查文件是否存在
        if not os.path.isfile(script_path):
            return jsonify({"error": "Script does not exist in the current directory."}), 400

        try:
            # 使用subprocess运行外部python脚本
            result = subprocess.run(['python', script_path], capture_output=True, text=True, check=True)
            output = result.stdout.strip()
            return jsonify({"output": output}), 200
        except subprocess.CalledProcessError as e:
            return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/upload', methods=['POST'])
def upload_code():
    try:
        # 获取文件名和代码内容
        filename = request.form.get('filename')
        code = request.form.get('code')

        # 文件名不能为空，且必须以 .py 结尾
        if not filename.endswith('.py'):
            filename += '.py'  # 自动添加 .py 扩展名

        if not code:
            return jsonify({"error": "No code provided."}), 400

        modified_code = genera_python_code.modify_code(code,filename)

        # 生成完整文件路径
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        try:
            # 将代码写入指定的 .py 文件
            with open(file_path, 'w') as file:
                file.write(modified_code)

            return jsonify({"message": "Python script created successfully!", "filename": filename}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/")
def read_root():
    return jsonify({"message": "Welcome to the Playwright code generator API. Use /codegen?url=<your_url>"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001)
