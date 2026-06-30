# 🐱 NekoCat — 猫娘对话系统 SDK

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-61%20passed-brightgreen.svg)]()

可插拔多 AI 后端的 CLI 猫娘聊天机器人。在终端中与可爱的猫娘角色实时流式对话。

<p align="center">
  <img src="https://img.shields.io/badge/AI-DeepSeek%20%7C%20Claude%20%7C%20OpenAI%20%7C%20Ollama-orange" alt="AI Backends">
</p>

## ✨ 特性

- 🎭 **猫娘角色系统** — 内置 3 种性格预设（元气/傲娇/冷酷），支持自定义 YAML
- 🔌 **可插拔 AI 后端** — DeepSeek / Claude / OpenAI / Ollama / Mock，一键切换
- 💬 **流式打字机效果** — Rich 终端渲染，逐字输出，沉浸式对话体验
- 🎨 **多款颜色主题** — pink / purple / mint / sunset
- ⚙️ **灵活配置** — `.env` 文件 / YAML / 环境变量 / CLI 参数
- 🧪 **零成本测试** — 内置 MockBackend，无需 API Key 即可体验

## 📦 安装

```bash
git clone https://github.com/bloodsuckerking/nekocat.git
cd nekocat
pip install -e ".[openai]"   # DeepSeek / OpenAI 后端（推荐）
```

> 可选：`pip install -e ".[anthropic]"` (Claude) / `pip install -e ".[ollama]"` (本地 Ollama)

### 配置 API Key

```bash
cp .env.example .env
```

编辑 `.env` 填入你的 API key：

```bash
# DeepSeek（推荐）— 在 https://platform.deepseek.com 获取
OPENAI_API_KEY=sk-your-deepseek-key

# 或用 Claude
ANTHROPIC_API_KEY=sk-ant-your-key
```

> CLI 启动时会自动从 `.env` 加载环境变量，无需手动 `export`。

## 🚀 快速开始

```bash
# DeepSeek V4 Pro（推荐，性价比最高）
python -m nekocat chat --backend deepseek --model deepseek-v4-pro

# DeepSeek V4 Flash（更快更便宜）
python -m nekocat chat --backend deepseek --model deepseek-v4-flash

# Claude
python -m nekocat chat --backend claude --model claude-sonnet-4-6

# OpenAI
python -m nekocat chat --backend openai --model gpt-4o-mini

# 测试模式（无需 API Key）
python -m nekocat chat --backend mock

# 傲娇猫娘
python -m nekocat chat --backend deepseek --persona tsundere_neko
```

## 🎭 角色预设

| 预设 | 角色 | 风格 | 描述 |
|------|------|------|------|
| `classic_neko` | 小咪 (Mimi) | 元气可爱 | 活泼开朗的三花猫娘，最喜欢被摸头 |
| `tsundere_neko` | 咲希 (Saki) | 傲娇 | 嘴上说着不要，身体却很诚实 |
| `kuudere_neko` | 零 (Rei) | 冷酷 | 冷静从容的银白虎斑猫娘 |

```bash
python -m nekocat persona-list              # 查看所有角色
python -m nekocat persona-show kuudere_neko # 查看角色详情
python -m nekocat persona-validate my.yaml  # 验证自定义角色
```

## 🔌 后端

```bash
python -m nekocat backends   # 列出可用后端
```

| 后端 | 命令 | API Key |
|------|------|---------|
| DeepSeek | `--backend deepseek` | `OPENAI_API_KEY` |
| Claude | `--backend claude` | `ANTHROPIC_API_KEY` |
| OpenAI | `--backend openai` | `OPENAI_API_KEY` |
| Ollama | `--backend ollama` | 本地服务 |
| Mock | `--backend mock` | 无需 |

## ⌨️ 对话命令

| 命令 | 功能 |
|------|------|
| `/help` | 显示帮助 |
| `/reset` | 清除对话历史 |
| `/persona <name>` | 切换角色 |
| `/system` | 查看系统提示词 |
| `/history` | 查看对话统计 |
| `/save` | 保存对话记录 |
| `/exit` | 退出 |

## 🧩 作为 SDK 使用

```python
import asyncio
from nekocat.persona.presets._registry import load_preset
from nekocat.core.chat import NekoChat
from nekocat.core.session import ChatSession
from nekocat.backends.registry import BackendRegistry

async def main():
    persona = load_preset("classic_neko")
    backend = BackendRegistry.get("deepseek", model="deepseek-v4-pro")
    chat = NekoChat(persona=persona, backend=backend)
    session = ChatSession()

    async for token in chat.stream("你好呀！", session):
        print(token, end="")

asyncio.run(main())
```

## 🎨 自定义角色

创建 `my-neko.yaml`：

```yaml
name: MyNeko
display_name: "我的猫娘"
description: "一只独一无二的猫娘"
backstory: "她的故事由你来写..."
speech_style: moe

traits:
  - name: 温柔
    description: "说话轻声细语"
    intensity: 0.9

rules:
  - rule: "每次回复都要以「喵~」结尾"
    priority: 1

interjections:
  - "喵~"
  - "呜咪~"

endings:
  - "的说~"
  - "nya~"
```

```bash
python -m nekocat chat --persona-file ./my-neko.yaml
```

## 📁 项目结构

```
nekocat/
├── pyproject.toml              # Python 项目配置
├── .env.example                # 环境变量模板
│
├── src/nekocat/
│   ├── core/                   # NekoChat 编排器、会话、对话历史
│   ├── persona/                # 角色模型 + 提示词生成 + YAML 预设
│   │   └── presets/            # classic / tsundere / kuudere
│   ├── backends/               # AI 后端 (mock/claude/openai/ollama/deepseek)
│   ├── cli/                    # Typer CLI + Rich 渲染 + REPL
│   ├── config/                 # pydantic-settings 配置
│   └── utils/
│
└── tests/                      # 61 个测试
```

## 📄 许可

MIT
