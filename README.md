# WeChat Reply Helper（桌面微信回复助手）

这是一个基于 **OpenAI** 的桌面微信回复助手脚本，可以帮助你快速生成回复内容，并且为不同联系人维护独立的会话历史。脚本支持通过快捷键生成回复、切换联系人以及会话清空等功能，适合在 Windows 平台配合桌面版微信使用。

## 主要特性

- **调用 OpenAI 模型**：使用 OpenAI 的 Responses API 生成聊天回复，需要在运行前设置 `OPENAI_API_KEY`。
- **独立会话管理**：每个联系人拥有独立的对话上下文，历史记录保存在 `sessions.json` 中，重启程序后仍能记忆之前的对话。
- **快捷键操作**：
  - `Ctrl+Alt+G`：从剪贴板读取文本，向 OpenAI 发送请求并将生成的回复复制回剪贴板。
  - `Ctrl+Alt+1` ~ `Ctrl+Alt+9`、`Ctrl+Alt+0`：快速切换到前 10 个联系人会话。
  - `Ctrl+Alt+P`：按字母顺序在已有联系人会话中循环切换。
  - `Ctrl+Alt+L`：列出当前所有联系人会话。
  - `Ctrl+Alt+R`：清空当前联系人会话历史。
- **剪贴板路由前缀**：支持在剪贴板文本前添加 `[Alice] …` 或 `@Alice …` 等形式自动归档到指定联系人会话。
- **可配置系统提示**：通过环境变量 `SYSTEM_PROMPT` 调整机器人的语气和风格，`MAX_TURNS` 控制每个会话保留的历史轮数。

## 环境要求

- Windows 10/11 系统（建议以管理员权限运行，方便监听热键）。
- Python 3.10 及以上。
- 依赖库：`openai`、`pyperclip`、`keyboard`。已在 `requirements.txt` 中列出。
- 一个有效的 OpenAI API Key，并保证账户有足够的额度。

## 安装与运行

1. **克隆项目并进入目录：**
   ```bash
   git clone https://github.com/ETO-ze/wechat-reply-helper.git
   cd wechat-reply-helper
   ```

2. **创建虚拟环境并安装依赖：**
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate        # Windows PowerShell 环境
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **设置环境变量：**
   将你的 OpenAI API Key 写入环境变量。例如在 PowerShell 中：
   ```powershell
   $env:OPENAI_API_KEY = "sk-xxx..."
   # 可选：自定义系统提示和上下文长度
   $env:SYSTEM_PROMPT = "你是一个简洁友好的微信助手。"
   $env:MAX_TURNS = "6"
   ```

4. **运行脚本：**
   ```bash
   python reply_helper.py
   ```

   启动后终端会输出各快捷键说明，例如如何生成回复、切换会话等。

5. **使用流程：**
   - 在微信对话中复制对方的消息（Ctrl+C）。
   - 按下 `Ctrl+Alt+G` 生成回复，程序会调用 GPT 模型输出文本，并自动复制到剪贴板。
   - 回到微信聊天框中粘贴（Ctrl+V）并发送即可。
   - 若要区分不同联系人，可在消息前添加 `[联系人名]` 或 `@联系人名` 前缀后再复制；或预先用 `Ctrl+Alt+1..9/0` 切换当前会话。

## 文件说明

- **reply_helper.py**：主程序文件，实现读取剪贴板、调用 OpenAI API、会话管理和快捷键绑定。
- **requirements.txt**：依赖列表，包含 `openai`、`pyperclip`、`keyboard` 等库。
- **sessions.json**（运行时自动生成）：存储每个联系人会话的历史记录，无需手动修改。
- **README.md**（本文件）：详细的安装与使用说明。

## 温馨提示

1. **使用 OpenAI API 需要计费**：请确保你的 API Key 已开通付费并有足够的额度，否则会报错 `insufficient_quota`。
2. **脚本需管理员权限运行**：在 Windows 系统下，监听全局快捷键通常需要以管理员身份打开终端或 VS Code，否则 `keyboard` 库可能报错。
3. **避免滥用自动回复**：虽然脚本不直接自动发送消息，但建议合理使用，避免高频率调用导致微信风控。
4. **会话数据安全**：`sessions.json` 中只保存对话摘要，不包含敏感账号信息。如需清空历史，可手动删除该文件或使用快捷键清空。
