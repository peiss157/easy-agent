"""保存标准聊天消息，包括模型工具调用及其结果。"""

from copy import deepcopy
import json


class Memory:
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.clear()

    def add(self, role: str, content, **fields) -> None:
        if not isinstance(content, str) and content is not None:
            content = json.dumps(content, ensure_ascii=False)
        self.add_message({"role": role, "content": content, **fields})

    def add_message(self, message: dict) -> None:
        self.messages.append(deepcopy(message))

    def get_context(self) -> list[dict]:
        return deepcopy(self.messages)

    def clear(self) -> None:
        self.messages = [{"role": "system", "content": self.system_prompt}]
