# 电脑操作 Agent - Qwen3.5 优化版

一个基于 AI 视觉的电脑操作助手，使用阿里云 Qwen3.5 多模态模型进行屏幕分析和操作决策。

## 功能特点

- 🖼️ **屏幕截图** - 使用 mss 高速截图
- 🤖️ **AI 视觉分析** - 使用阿里云 Qwen3.5 分析屏幕内容
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

### 2. 获取阿里云 API 密钥

1. 访问 [阿里云 DashScope](https://dashscope.console.aliyun.com/)
2. 开通 Qwen3.5 服务
3. 创建 API Key

### 3. 配置 API

编辑 `config.yaml` 文件：

```yaml
api:
  base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  api_key: "your-dashscope-api-key-here"  # 替换为你的阿里云密钥
  model: "qwen3.5-plus"
```

### 4. 运行

#### 命令行方式

```bash
python main.py -t "打开微信"
```

#### Web 界面

```bash
python web_interface.py
```

然后在浏览器访问 http://localhost:5000

## 项目结构

```
computer_agent/
├── main.py                 # 主程序
├── web_interface.py        # Web 界面服务器
├── config.yaml             # 配置文件
├── requirements.txt        # Python 依赖
├── templates/
│   └── index.html         # Web 界面
└── agent.log              # 运行日志
```

## Qwen3.5 优化说明

### 提示词优化
- 使用简洁的 markdown 格式
- 强调纯 JSON 输出
- 优化坐标系统说明

### API 配置
- 使用阿里云 DashScope 兼容模式
- 支持 Qwen3.5 多模态模型
- 优化温度和 max_tokens 参数

## 注意事项

1. **紧急停止** - 将鼠标快速移到屏幕角落可触发安全机制
2. **权限问题** - macOS 需要授予屏幕录制和辅助功能权限
3. **API 费用** - 使用阿里云 DashScope 会产生相应费用

## License

MIT License