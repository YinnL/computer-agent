# 电脑操作 Agent

一个基于 AI 视觉的电脑操作助手，能够分析屏幕内容并自主执行操作任务。

## 功能特点

- 🖼️ **屏幕截图** - 使用 mss 高速截图
- 🤖 **AI 视觉分析** - 使用 OpenAI GPT-4o 分析屏幕内容
- 🖱️ **自动操作** - 使用 pyautogui 执行鼠标键盘操作
- 🔄 **循环迭代** - 截图→思考→操作，直到完成任务
- 📐 **坐标映射** - AI 使用 1000x1000 归一化坐标，自动映射到实际分辨率
- 🌐 **Web 界面** - 现代化的 Web 操作界面

## 快速开始

### 1. 安装依赖

```bash
cd computer_agent
pip install -r requirements.txt
```

### 2. 配置 API

编辑 `config.yaml` 文件：

```yaml
api:
  base_url: "https://api.openai.com/v1"
  api_key: "your-api-key-here"  # 替换为你的 API 密钥
  model: "gpt-4o"
  max_tokens: 4096
  temperature: 0.7
```

### 3. 运行

#### 方式一：命令行运行

```bash
python main.py -t "打开浏览器"
```

#### 方式二：Web 界面

```bash
python web_interface.py
```

然后在浏览器访问 http://localhost:5000

## 项目结构

```
computer_agent/
├── main.py                 # 主程序（命令行）
├── web_interface.py        # Web 界面服务器
├── config.yaml             # 配置文件
├── requirements.txt        # Python 依赖
├── templates/
│   └── index.html         # Web 界面 HTML
└── agent.log              # 运行日志
```

## 注意事项

1. **紧急停止** - 将鼠标快速移到屏幕角落可以触发 pyautogui 的安全机制
2. **权限问题** - macOS 需要授予屏幕录制和辅助功能权限
3. **API 费用** - 使用 GPT-4o 等模型会产生 API 费用

## License

MIT License
