# wechat-reply-helper

本项目是一个桌面微信助手，通过调用 OpenAI 的 API 对剪贴板中的消息生成回复。它并不自动读取或发送微信消息，而是需要用户手动复制消息并通过快捷键生成回复，然后手动粘贴发送，这样可以降低账号被封的风险。

## 环境要求

- Windows 10 或以上（理论上兼容其他桌面系统）
- Python 3.10 及以上
- 已安装并配置好 OpenAI API Key（环境变量 `OPENAI_API_KEY`）

## 安装步骤

1. 克隆仓库或下载代码。
2. 在项目目录创建并激活虚拟环境（可选）：
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   ```
3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

## 使用方法

1. 在端口设置环境变量（或在系统设置中永久设置）：
   ```bash
   set OPENAI_API_KEY=你的API密钥
   ```
2. 运行脚本：
   ```bash
   python reply_helper.py
   ```
   启动后会显示提示信息：
   - `Ctrl+Alt+G`：读取剪贴板文本，调用 OpenAI API 生成回复并自动复制到剪贴板。
   - `Ctrl+Alt+R`：清空会话上下文。
   - `Ctrl+C`：退出程序。

3. 在微信对话框中，复制对方的消息，按 `Ctrl+Alt+G` 生成回复，再粘贴发送。

## 常见问题

- 如果提示 `insufficient_quota`，说明 API 配额已用完，需要检查 OpenAI 账户的 Billing。
- 如果按快捷键无反应，确认程序以管理员权限运行，并且键盘布局为 Windows 默认。

## 注意事项

- 该脚本只生成回复，不会自动发送。
- 谨慎使用，避免大量满留导致 API 调用费用过高或微信账号风险。
