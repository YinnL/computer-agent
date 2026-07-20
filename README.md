# Computer Agent

An AI-powered computer-use assistant that interprets screen content and autonomously performs desktop tasks.

## Features

- 🖼️ **High-performance screen capture** — Captures the screen efficiently with mss.
- 🤖 **AI-powered visual analysis** — Uses Alibaba Cloud Qwen3.5 to interpret screen content.
- 🖱️ **Automated interaction** — Uses pyautogui to control the mouse and keyboard.
- 🔄 **Iterative execution loop** — Repeats the cycle of capture, reasoning, and action until the task is complete.
- 📐 **Coordinate mapping** — Converts the AI's normalized 1,000 × 1,000 coordinate system to the actual display resolution.
- 🌐 **Web interface** — Provides a modern browser-based control interface.

## Quick Start

### 1. Install the dependencies

~~~bash
cd computer_agent
pip install -r requirements.txt
~~~

### 2. Obtain an Alibaba Cloud API key

1. Visit the Alibaba Cloud DashScope console: https://dashscope.console.aliyun.com/
2. Enable the Qwen3.5 service.
3. Create an API key.

### 3. Configure the API

Edit the config.yaml file:

~~~yaml
api:
  base_url: "https://coding.dashscope.aliyuncs.com/v1"
  api_key: "your-api-key-here"
  model: "qwen3.5-plus"
~~~

### 4. Run the agent

#### Command-line interface

~~~bash
python main.py -t "Create a new note"
~~~

#### Web interface

~~~bash
python web_interface.py
~~~

Then open http://localhost:5000 in your browser.

## Project Structure

~~~
computer_agent/
├── main.py                 # Core agent implementation
├── web_interface.py        # Web interface server
├── config.yaml             # Runtime configuration
├── requirements.txt        # Python dependencies
├── templates/
│   └── index.html         # Web interface
└── agent.log              # Runtime log
~~~

## Important Notes

1. **Emergency stop** — Move the mouse rapidly to a screen corner to trigger the built-in safety mechanism.
2. **Permissions** — On macOS, grant Screen Recording and Accessibility permissions before running the agent.
3. **API costs** — Use of Alibaba Cloud DashScope may incur charges.

## License

MIT License
