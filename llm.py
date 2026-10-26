"""DeepSeek 模型接入；仅使用 Python 标准库。"""

import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

# 在下面的引号内填写你自己的 DeepSeek API Key。
DEEPSEEK_API_KEY = "请输入秘钥"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-flash"  # 也可按你的账号修改模型名称。


class LLMError(RuntimeError):
    """模型配置、网络或响应错误。"""


def format_response(message: dict) -> dict:
    calls = message.get("tool_calls") or []
    if not isinstance(calls, list):
        raise LLMError("模型返回的工具调用格式不正确。")
    for call in calls:
        if not isinstance(call, dict):
            raise LLMError("模型返回的工具调用格式不正确。")
        function = call.get("function")
        if not (call.get("id") and isinstance(function, dict)
                and isinstance(function.get("name"), str)
                and isinstance(function.get("arguments"), str)):
            raise LLMError("模型返回的工具调用缺少 ID、名称或参数。")
    answer = message.get("content") or ""
    if not calls and (not isinstance(answer, str) or not answer.strip()):
        raise LLMError("模型返回空答案，请重新尝试。")
    return {"answer": answer, "tool_calls": calls, "message": message}


class LLM:
    def __init__(self, tool_schemas=None, api_key=None, model=None, timeout=60):
        self.api_key = (api_key or os.getenv("DEEPSEEK_API_KEY") or DEEPSEEK_API_KEY).strip()
        if not self.api_key or self.api_key in (
            "在这里填写你的 DeepSeek API Key",
            "请输入秘钥",
        ):
            raise LLMError("请在 llm.py 顶部填写 DEEPSEEK_API_KEY；本地测试可运行 python main.py --demo。")
        self.model = model or os.getenv("DEEPSEEK_MODEL") or DEEPSEEK_MODEL
        self.base_url = os.getenv("DEEPSEEK_BASE_URL", DEEPSEEK_BASE_URL).rstrip("/")
        self.tool_schemas = tool_schemas or []
        self.timeout = timeout

    def chat(self, messages, fmt=None) -> dict:
        # fmt 保留你原先的接口；实际响应通过原生 tool_calls 解析。
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "thinking": {"type": "disabled"},
        }
        if self.tool_schemas:
            payload["tools"] = self.tool_schemas
        request = Request(
            self.base_url + "/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Authorization": "Bearer " + self.api_key,
                     "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            hints = {401: "密钥无效，请检查 llm.py 中的配置。",
                     402: "账号余额不足。", 429: "请求过于频繁，请稍后重试。"}
            hint = hints.get(error.code, "请检查模型名称、网络及服务状态。")
            raise LLMError(f"DeepSeek 请求失败（HTTP {error.code}）：{hint}") from None
        except (URLError, TimeoutError, OSError) as error:
            raise LLMError("无法连接 DeepSeek 或请求超时，请检查网络后重试。") from None
        except (ValueError, UnicodeDecodeError):
            raise LLMError("DeepSeek 返回的内容不是有效的 JSON。") from None
        try:
            choice = body["choices"][0]
            raw = choice["message"]
            message = {"role": "assistant", "content": raw.get("content")}
            for field in ("tool_calls", "reasoning_content"):
                if raw.get(field) is not None:
                    message[field] = raw[field]
        except (KeyError, IndexError, TypeError, AttributeError):
            raise LLMError("DeepSeek 返回的响应结构不完整。") from None
        if choice.get("finish_reason") not in ("stop", "tool_calls"):
            raise LLMError("模型回复未正常完成，请缩短任务或稍后重试。")
        return format_response(message)


class DemoLLM:
    """明确标注的本地演示，不调用模型、不产生 API 请求。"""

    model = "local-demo"

    def chat(self, messages, fmt=None) -> dict:
        last = messages[-1]
        if last["role"] == "tool":
            result = json.loads(last["content"])
            text = ("工具结果：" + str(result["result"])) if result["ok"] else ("工具执行失败：" + result["error"])
            return format_response({"role": "assistant", "content": text})
        task = str(last["content"]).strip()
        expression = task
        for prefix in ("计算", "calc "):
            if task.lower().startswith(prefix):
                expression = task[len(prefix):].lstrip(":： ")
                break
        if any(word in task.lower() for word in ("时间", "几点", "日期", "time")):
            name, arguments = "get_current_time", {}
        elif expression != task or re.fullmatch(r"[0-9.()+*/% -]+", expression):
            name, arguments = "calculate", {"expression": expression}
        else:
            return format_response({"role": "assistant", "content": "当前是本地演示模式，可输入计算表达式或查询时间；填写密钥后去掉 --demo 即可使用 DeepSeek 对话。"})
        call = {"id": "call_" + uuid4().hex, "type": "function",
                "function": {"name": name, "arguments": json.dumps(arguments, ensure_ascii=False)}}
        return format_response({"role": "assistant", "content": None, "tool_calls": [call]})
