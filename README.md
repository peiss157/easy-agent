# DeepSeek Agent

这是一个使用 DeepSeek Chat Completions API 的简单 Agent 示例。它按照下面的流程工作：

1. 读取用户任务并保存到记忆。
2. 调用 DeepSeek 判断是否需要工具。
3. 执行工具，并把结果返回给模型。
4. 模型生成最终回答。
5. 最多循环 10 次，避免任务无限执行。

## 当前功能

- DeepSeek 多轮对话
- 工具调用
- 安全计算：数字、括号和 `+ - * / // %`
- 查询北京时间
- 对话历史和清空历史
- 本地演示模式，无需 API Key
- 单次任务模式和交互模式

## 配置

打开 `llm.py`，填写：

```python
DEEPSEEK_API_KEY = "你的 DeepSeek API Key"
```

也可以使用环境变量：

```powershell
$env:DEEPSEEK_API_KEY = "你的 DeepSeek API Key"
```

默认模型为 `deepseek-flash`，可以在 `llm.py` 中修改，或运行时使用 `--model` 覆盖。

## 运行

在本目录运行交互模式：

```powershell
python main.py
```

运行本地演示，不访问 DeepSeek：

```powershell
python main.py --demo
```

直接执行一次任务：

```powershell
python main.py "计算 (12 + 8) * 3"
python main.py "现在几点"
```

交互模式命令：

- `/help`：显示帮助
- `/history`：查看当前历史
- `/clear`：清空历史
- `/exit`：退出程序

## 文件说明

- `main.py`：Agent 主循环和命令行入口
- `llm.py`：DeepSeek 请求、响应解析和本地演示模型
- `tools.py`：工具定义和工具执行
- `memory.py`：对话记忆
- `prompt.py`：系统提示词
