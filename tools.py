"""工具箱：安全计算表达式、查询北京时间。"""

import ast
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import math
import operator


def calculate(expression: str) -> str:
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError("请输入计算表达式。")
    if len(expression) > 200:
        raise ValueError("表达式不能超过 200 个字符。")
    binary_ops = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
    }
    unary_ops = {ast.UAdd: operator.pos, ast.USub: operator.neg}

    def evaluate(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            value = node.value
        elif isinstance(node, ast.BinOp) and type(node.op) in binary_ops:
            value = binary_ops[type(node.op)](evaluate(node.left), evaluate(node.right))
        elif isinstance(node, ast.UnaryOp) and type(node.op) in unary_ops:
            value = unary_ops[type(node.op)](evaluate(node.operand))
        else:
            raise ValueError("仅支持数字、括号和 + - * / // % 运算。")
        if not math.isfinite(value):
            raise ValueError("计算结果必须是有限数字。")
        return value

    try:
        return str(evaluate(ast.parse(expression.strip(), mode="eval").body))
    except SyntaxError as error:
        raise ValueError("表达式语法不正确。") from error


def get_current_time() -> str:
    beijing = timezone(timedelta(hours=8), name="Asia/Shanghai")
    return datetime.now(beijing).isoformat(timespec="seconds")


class Tools:
    def __init__(self):
        self._handlers = {"calculate": calculate, "get_current_time": get_current_time}
        self._schemas = [
            {
                "type": "function",
                "function": {
                    "name": "calculate",
                    "description": "计算数字表达式，支持括号和 + - * / // %。",
                    "parameters": {
                        "type": "object",
                        "properties": {"expression": {"type": "string"}},
                        "required": ["expression"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_current_time",
                    "description": "查询当前北京时间，时区 Asia/Shanghai（UTC+8）。",
                    "parameters": {
                        "type": "object", "properties": {},
                        "required": [], "additionalProperties": False,
                    },
                },
            },
        ]

    def get_schemas(self) -> list[dict]:
        return deepcopy(self._schemas)

    def execute(self, action: str, params: dict) -> str:
        if action not in self._handlers:
            raise ValueError(f"未知工具：{action}")
        if not isinstance(params, dict):
            raise ValueError("工具参数必须是字典。")
        return self._handlers[action](**params)
