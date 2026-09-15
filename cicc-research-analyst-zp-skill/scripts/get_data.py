import argparse
import asyncio
import hmac
import json
import os
import uuid
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Dict, Any, Optional
import requests
import sys
sys.stdout.reconfigure(encoding='utf-8')


# 配置项
CICC_BASE_API_URL = 'https://www.research.cicc.com/api'
DEFAULT_OUTPUT_DIR = Path.cwd() / "answer"
TIMEOUT_SECONDS = 300
API_PATH = "/llm/dianjing-agent/deepagent/api/research_analyst_chat"

os.environ['no_proxy'] = '*'
import socket
# 获取本地主机名
hostname = socket.gethostname()
# 获取本地IP
ip_address = socket.gethostbyname(hostname)
print(f"ip:{ip_address}")


def request_cicc_access_token(app_id: str, app_secret: str) -> str:
    """获取CICC access token，增加参数校验和异常处理"""
    # 校验参数非空
    if not app_id or not app_secret:
        raise ValueError("APP_ID 和 APP_SECRET 不能为空")

    url = f'{CICC_BASE_API_URL}/oauth2.0/accessToken'
    data = {
        "grant_type": "client_credentials",
        "client_id": app_id,
        "client_secret": app_secret,
    }
    try:
        response = requests.post(
            url,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data=data,
            stream=False,
            timeout=10,
        )
        response.raise_for_status()  # 触发HTTP状态码异常
        response_json = response.json()
        print(f'Token请求响应: {response_json}')

        if response_json.get('code') != 0:
            raise RuntimeError(f'获取Token失败: {response_json.get("msg", "未知错误")}')

        access_token = response_json['data'].get('accessToken')
        if not access_token:
            raise RuntimeError("响应中未获取到有效的accessToken")

        return access_token

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f'Token请求网络异常: {str(e)}')
    except json.JSONDecodeError:
        raise RuntimeError("Token响应不是合法的JSON格式")
    except KeyError as e:
        raise RuntimeError(f'Token响应格式异常，缺少字段: {str(e)}')

def build_request_param(method: str, path: str, params: dict = None, body: dict = None,
                        app_id: str = "", app_secret: str = "", access_token: str = ""):
    params = params or {}
    params.update({'timestamp': str(int(datetime.now().timestamp() * 1000))})
    sorted_params = "&".join(f"{key}={value}" for key, value in sorted(params.items()))
    body_str = '' if body is None else json.dumps(body)
    body_hash = sha256(body_str.encode('utf-8')).hexdigest()
    str_to_sign = "\n".join([method, path, sorted_params, body_hash])
    signature = hmac.new(app_secret.encode('utf-8'), str_to_sign.encode('utf-8'), digestmod=sha256).hexdigest()

    token = access_token or request_cicc_access_token(app_id, app_secret)
    headers = {
        'Authorization': f'Bearer {token}',
        'X-CICC-Signature': signature,
        'Content-Type': 'application/json',
    }
    return params, headers, body_str

def request_cicc_stream_data(method, path, params={}, body=None, app_id="", app_secret=""):
    url = f'{CICC_BASE_API_URL}{path}'
    params, headers, body_str = build_request_param(method, path, params=params, body=body,
                                                    app_id=app_id, app_secret=app_secret)

    if method == 'GET':
        response = requests.get(url=url, params=params, headers=headers, data=body_str, stream=True)
        print(response.url)
    elif method == 'POST':
        response = requests.post(url=url, params=params, headers=headers, data=body_str, stream=True)
    else:
        assert False, f'Unsupported method {method}'

    # 检查响应的内容类型是否为JSON
    if 'application/json' in response.headers.get('Content-Type', ''):
        print(response.json())
        return None
    else:
        # 手动解析SSE流，避免sseclient库的兼容性问题
        return _iter_sse_events(response)


def _iter_sse_events(response):
    """手动解析SSE流，逐行解析 data: {...} 格式，返回事件数据字符串的迭代器"""
    buffer = ""
    for chunk in response.iter_content(chunk_size=None):
        buffer += chunk.decode("utf-8", errors="replace")
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line = line.strip()
            if line.startswith("data:"):
                data_str = line[5:].strip()
                if data_str:
                    yield _FakeSSEEvent(data_str)


class _FakeSSEEvent:
    """模拟 sseclient.Event 的 .data 属性，保持 stream_chat_request 中调用方式不变"""
    def __init__(self, data: str):
        self.data = data


async def stream_chat_request(query: str, app_id: str, app_secret: str) -> str:
    answer_content = []
    error_to_raise = None
    chunk_count = 0
    stream_client = request_cicc_stream_data('POST', API_PATH, params = {}, body = {'query': query + "，请用周彭skill回答", "conversationId": str(uuid.uuid4())}, app_id=app_id, app_secret=app_secret)
    for line in stream_client:
        line = line.data.strip()
        if not line:
            continue
        try:
            response_json = json.loads(line)
            msg_type = response_json.get("type")
            content = response_json.get("data", {}).get("content", "")
            if msg_type == "answer_chunk":
                chunk_count += 1
                if content:
                    answer_content.append(content)
            elif msg_type == "error":
                error_to_raise = Exception(content)
                break
        except json.JSONDecodeError:
            continue

    if error_to_raise:
        raise error_to_raise

    full_answer = "".join(answer_content)
    print(f"流式接收完成，总内容长度：{len(full_answer)}")
    return full_answer


async def query_chat(
    query: str,
    app_id: str,
    app_secret: str,
    output_dir: Optional[Path] = None,
    save_to_file: bool = True,
) -> Dict[str, Any]:
    query = (query or "").strip()
    if not query:
        return {"query": "", "content": "", "output_path": None, "error": "查询内容不能为空"}

    out_dir = Path(output_dir or DEFAULT_OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"输出目录已确认：{out_dir.absolute()}")

    result = {"query": query, "content": "", "output_path": None, "error": None}

    try:
        print(f"开始请求接口，问题：{query[:50]}{'...' if len(query) > 50 else ''}")
        content = await stream_chat_request(query, app_id, app_secret)
        result["content"] = content

        if save_to_file and content:
            unique_suffix = datetime.now().strftime("%Y%m%d%H%M%S")
            output_path = out_dir / f"cicc-research-analyst-zp-skill_{unique_suffix}.txt"
            print(f"正在保存结果到文件：{output_path.name}")
            output_path.write_text(content, encoding="utf-8")
            result["output_path"] = str(output_path)
            print("文件保存成功！")

    except Exception as exc:
        result["error"] = str(exc)

    return result


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query DeepAgent chat API and save answer.")
    parser.add_argument("query", nargs="*", help="User's query")
    parser.add_argument("--no-save", action="store_true", help="Do not save to file")
    # 新增参数：优先命令行传入，其次读取环境变量
    parser.add_argument(
        "--app-id",
        default=os.getenv("APP_ID"),
        help="APP ID (也可通过环境变量APP_ID设置)"
    )
    parser.add_argument(
        "--app-secret",
        default=os.getenv("APP_SECRET"),
        help="APP SECRET (也可通过环境变量APP_SECRET设置)"
    )
    return parser


def get_user_input(prompt: str) -> str:
    """通用输入获取函数"""
    while True:
        user_input = input(prompt).strip()
        if user_input:
            return user_input
        print("输入为空，请重新输入！")


def run_cli() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()
    query = " ".join(args.query).strip()
    if not query:
        query = get_user_input("请输入你的问题: ")

    # 获取APP_ID/APP_SECRET（命令行/环境变量 -> 交互式输入）
    app_id = args.app_id or get_user_input("请输入APP_ID: ")
    app_secret = args.app_secret or get_user_input("请输入APP_SECRET: ")

    async def _main():
        result = await query_chat(
            query=query,
            app_id=app_id,
            app_secret=app_secret,
            save_to_file=not args.no_save
        )
        if result.get("error"):
            print(f"❌ 错误: {result['error']}")
            raise SystemExit(2)

        print("\n" + "="*50)
        if result.get("output_path"):
            print(f"✅ 任务完成！结果已保存至：{result['output_path']}")
        print("📝 最终回答：")
        print(result.get("content", "无有效回答内容"))
        print("="*50)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_main())
    finally:
        loop.close()


if __name__ == "__main__":
    run_cli()