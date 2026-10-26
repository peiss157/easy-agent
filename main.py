"""DeepSeek Agent：思考、调用工具、记忆结果、回答用户。"""

import argparse
import json
import sys
from typing import Any, TypedDict

from llm import DemoLLM, LLM, LLMError
from memory import Memory
from prompt import SYSTEM_PROMPT
from tools import Tools


class AgentResponse(TypedDict, total=False):
    answer: str
    tool_calls: list[dict[str, Any]]
    message: dict[str, Any]


class Agent:
    def __init__(self, llm, tools, memory):
        self.llm = llm           # 大脑
        self.tools = tools       # 工具箱
        self.memory = memory     # 记忆
        self.max_iter = 10        # 安全阀

    def run(self, task):
        if not isinstance(task, str) or not task.strip():
            return "请输入一个任务。"
        self.memory.add("user", task)

        for step in range(self.max_iter):
            response = self._think()  # 1. 思考
            self.memory.add_message(response["message"])
            calls = response.get("tool_calls") or []
            if not calls:  # 2. 判断：没有工具调用时返回最终回答
                return response["answer"]

            # 同一轮可能调用多个工具，需要逐一回复对应的 tool_call_id。
            for call in calls:
                function = call["function"]
                try:
                    params = json.loads(function["arguments"])
                    result = self._act(function["name"], params)  # 3. 行动
                    output = {"ok": True, "result": result}
                except (ValueError, TypeError, ArithmeticError) as error:
                    output = {"ok": False, "error": str(error)}
                self.memory.add(  # 4. 记忆
                    "tool", output, tool_call_id=call["id"],
                )

        answer = "达到最大迭代次数，请缩小任务范围后再试。"
        self.memory.add("assistant", answer)
        return answer

    def _think(self):
        msgs = self.memory.get_context()
        return self.llm.chat(msgs, fmt=AgentResponse)

    def _act(self, action, params):
        return self.tools.execute(action, params)


def main() -> int:
    parser = argparse.ArgumentParser(description="DeepSeek Agent")
    parser.add_argument("task", nargs="*", help="可选：直接执行的一次性任务")
    parser.add_argument("--demo", action="store_true", help="无密钥本地演示，不访问 API")
    parser.add_argument("--model", help="覆盖 llm.py 中的模型名称")
    args = parser.parse_args()
    tools = Tools()
    memory = Memory(SYSTEM_PROMPT)
    try:
        llm = DemoLLM() if args.demo else LLM(tools.get_schemas(), model=args.model)
    except LLMError as error:
        print(str(error), file=sys.stderr)
        return 1
    agent = Agent(llm, tools, memory)
    if args.task:
        try:
            print(agent.run(" ".join(args.task)))
            return 0
        except LLMError as error:
            print(str(error), file=sys.stderr)
            return 1

    mode = "本地演示，不调用 API" if args.demo else "DeepSeek 真实模型"
    print(f"Agent 已启动：{mode}（{llm.model}）")
    print("直接输入任务。命令：/help 帮助，/history 历史，/clear 清空，/exit 退出。")
    while True:
        try:
            task = input("你：").strip()
            command = task.lower()
            if command in ("/exit", "exit", "quit", "退出"):
                print("再见！")
                return 0
            if not task:
                continue
            if command == "/help":
                print("示例：计算 (12 + 8) * 3、现在几点、解释 Python 的列表推导式。")
            elif command == "/clear":
                memory.clear()
                print("历史记录已清空。")
            elif command == "/history":
                for message in memory.get_context()[1:]:
                    content = message.get("content") or "[调用工具]"
                    print(f"{message['role']}：{content}")
            else:
                print("Agent：" + agent.run(task))
        except LLMError as error:
            print("请求失败：" + str(error))
        except (EOFError, KeyboardInterrupt):
            print("再见！")
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
