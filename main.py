#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电脑操作 Agent
使用 mss 截图、pyautogui 操作、OpenAI SDK 进行 AI 决策
"""

import os
import sys
import time
import base64
import logging
from io import BytesIO
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

import yaml
import mss
import mss.tools
import pyautogui
from PIL import Image
from openai import OpenAI


class Config:
    """配置管理器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
    def _load_config(self) -> dict:
        """加载配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在：{self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    @property
    def api_base_url(self) -> str:
        return self.config['api']['base_url']
    
    @property
    def api_key(self) -> str:
        return self.config['api']['api_key']
    
    @property
    def model(self) -> str:
        return self.config['api']['model']
    
    @property
    def max_tokens(self) -> int:
        return self.config['api']['max_tokens']
    
    @property
    def temperature(self) -> float:
        return self.config['api']['temperature']
    
    @property
    def screenshot_quality(self) -> int:
        return self.config['screen']['screenshot_quality']
    
    @property
    def virtual_resolution(self) -> int:
        return self.config['screen']['virtual_resolution']
    
    @property
    def mouse_duration(self) -> float:
        return self.config['action']['mouse_duration']
    
    @property
    def click_interval(self) -> float:
        return self.config['action']['click_interval']
    
    @property
    def type_interval(self) -> float:
        return self.config['action']['type_interval']


class ScreenCapture:
    """屏幕截图模块"""
    
    def __init__(self, quality: int = 90, logger=None):
        self.quality = quality
        self.sct = mss.mss()
        self.logic_size = pyautogui.size()
        self.logger = logger or logging.getLogger(__name__)
        
    def capture(self, monitor: int = 1) -> Tuple[bytes, Tuple[int, int]]:
        monitor_info = self.sct.monitors[min(monitor, len(self.sct.monitors) - 1)]
        screenshot = self.sct.grab(monitor_info)
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        screenshot_size = screenshot.size
        
        if screenshot_size != self.logic_size:
            img = img.resize(self.logic_size, Image.Resampling.LANCZOS)
            self.logger.info(f"截图缩放：{screenshot_size} -> {self.logic_size}")
        
        actual_resolution = self.logic_size
        img_bytes = BytesIO()
        img.save(img_bytes, format="JPEG", quality=self.quality)
        jpeg_data = img_bytes.getvalue()
        
        self.logger.info(f"截图完成：分辨率={actual_resolution}")
        self.logger.info(f"pyautogui 当前鼠标位置：{pyautogui.position()}")
        
        return jpeg_data, actual_resolution
    
    def get_screen_size(self) -> Tuple[int, int]:
        return self.logic_size


class CoordinateMapper:
    """坐标映射器"""
    
    def __init__(self, virtual_resolution: int = 1000):
        self.virtual_resolution = virtual_resolution
        
    def map_coordinates(self, ai_x: float, ai_y: float, actual_width: int, actual_height: int) -> Tuple[int, int]:
        ai_x = max(0, min(ai_x, self.virtual_resolution))
        ai_y = max(0, min(ai_y, self.virtual_resolution))
        scale_x = actual_width / self.virtual_resolution
        scale_y = actual_height / self.virtual_resolution
        actual_x = int(ai_x * scale_x)
        actual_y = int(ai_y * scale_y)
        return actual_x, actual_y
    
    def map_coordinates_reverse(self, actual_x: int, actual_y: int, actual_width: int, actual_height: int) -> Tuple[float, float]:
        scale_x = actual_width / self.virtual_resolution
        scale_y = actual_height / self.virtual_resolution
        ai_x = actual_x / scale_x
        ai_y = actual_y / scale_y
        return ai_x, ai_y


class ActionExecutor:
    """操作执行器"""
    
    def __init__(self, config: Config, logger=None):
        self.config = config
        self.mapper = CoordinateMapper(config.virtual_resolution)
        self.logger = logger or logging.getLogger(__name__)
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = config.click_interval
        
    def execute_action(self, action: Dict[str, Any], screen_size: Tuple[int, int]) -> str:
        action_type = action.get('action_type', '').lower()
        try:
            if action_type == 'move_mouse':
                return self._move_mouse(action, screen_size)
            elif action_type == 'click':
                return self._click(action, screen_size)
            elif action_type == 'double_click':
                return self._double_click(action, screen_size)
            elif action_type == 'right_click':
                return self._right_click(action, screen_size)
            elif action_type == 'type':
                return self._type(action)
            elif action_type == 'press_key':
                return self._press_key(action)
            elif action_type == 'hotkey':
                return self._hotkey(action)
            elif action_type == 'scroll':
                return self._scroll(action, screen_size)
            elif action_type == 'wait':
                return self._wait(action)
            else:
                return f"未知操作类型：{action_type}"
        except Exception as e:
            return f"执行操作失败：{str(e)}"
    
    def _get_params(self, action: Dict) -> Dict:
        if 'parameters' in action:
            return action['parameters']
        elif '参数' in action:
            return action['参数']
        elif 'params' in action:
            return action['params']
        else:
            return action
    
    def _get_coordinates(self, action: Dict, screen_size: Tuple[int, int]) -> Tuple[int, int]:
        params = self._get_params(action)
        ai_x = params.get('x', 500)
        ai_y = params.get('y', 500)
        return self.mapper.map_coordinates(ai_x, ai_y, screen_size[0], screen_size[1])
    
    def _move_mouse(self, action: Dict, screen_size: Tuple[int, int]) -> str:
        params = self._get_params(action)
        ai_x = params.get('x', 500)
        ai_y = params.get('y', 500)
        x, y = self._get_coordinates(action, screen_size)
        self.logger.info(f"AI 坐标 ({ai_x}, {ai_y}) -> 实际坐标 ({x}, {y})")
        pyautogui.moveTo(x, y, duration=self.config.mouse_duration)
        return f"鼠标已移动到 ({x}, {y})"
    
    def _click(self, action: Dict, screen_size: Tuple[int, int]) -> str:
        params = self._get_params(action)
        ai_x = params.get('x', 500)
        ai_y = params.get('y', 500)
        button = params.get('button', 'left')
        x, y = self._get_coordinates(action, screen_size)
        self.logger.info(f"AI 坐标 ({ai_x}, {ai_y}) -> 实际坐标 ({x}, {y})")
        pyautogui.click(x, y, button=button)
        return f"已{button}键点击 ({x}, {y})"
    
    def _double_click(self, action: Dict, screen_size: Tuple[int, int]) -> str:
        x, y = self._get_coordinates(action, screen_size)
        pyautogui.doubleClick(x, y)
        return f"已双击 ({x}, {y})"
    
    def _right_click(self, action: Dict, screen_size: Tuple[int, int]) -> str:
        x, y = self._get_coordinates(action, screen_size)
        pyautogui.rightClick(x, y)
        return f"已右键点击 ({x}, {y})"
    
    def _type(self, action: Dict) -> str:
        params = self._get_params(action)
        text = params.get('text', '')
        if not text:
            self.logger.warning(f"type 操作未指定文本，params: {params}")
            return "错误：未指定要输入的文本"
        clear_first = params.get('clear_first', False)
        if clear_first:
            pyautogui.hotkey('command', 'a')
            time.sleep(0.1)
            pyautogui.press('backspace')
            time.sleep(0.1)
        import subprocess
        try:
            subprocess.run(['pbcopy'], input=text.encode('utf-8'), check=True)
            time.sleep(0.1)
            pyautogui.hotkey('command', 'v')
            time.sleep(0.2)
            self.logger.info("文本输入成功（使用剪贴板粘贴）")
            return f"已输入文本：{text[:50]}{'...' if len(text) > 50 else ''}"
        except Exception as e:
            self.logger.warning(f"剪贴板方式失败：{e}，回退到模拟键盘")
            pyautogui.write(text, interval=self.config.type_interval)
            return f"已输入文本（模拟键盘）: {text[:50]}{'...' if len(text) > 50 else ''}"
    
    def _press_key(self, action: Dict) -> str:
        params = self._get_params(action)
        key = params.get('key', '')
        presses = params.get('presses', 1)
        interval = params.get('interval', 0.1)
        pyautogui.press(key, presses=presses, interval=interval)
        return f"已按下按键：{key}"
    
    def _hotkey(self, action: Dict) -> str:
        params = self._get_params(action)
        keys = params.get('keys', [])
        if not keys:
            self.logger.warning(f"hotkey 操作未指定按键，params: {params}")
            return "错误：未指定组合键"
        key_map = {
            'ctrl': 'command' if sys.platform == 'darwin' else 'ctrl',
            'control': 'command' if sys.platform == 'darwin' else 'ctrl',
            'cmd': 'command', 'command': 'command',
            'alt': 'option', 'option': 'option', 'win': 'command',
            'enter': 'enter', 'return': 'enter', 'tab': 'tab',
            'space': 'space', 'backspace': 'backspace', 'delete': 'delete',
            'escape': 'esc', 'esc': 'esc',
            'up': 'up', 'down': 'down', 'left': 'left', 'right': 'right',
            'a': 'a', 'b': 'b', 'c': 'c', 'd': 'd', 'e': 'e',
            'f': 'f', 'g': 'g', 'h': 'h', 'i': 'i', 'j': 'j',
            'k': 'k', 'l': 'l', 'm': 'm', 'n': 'n', 'o': 'o',
            'p': 'p', 'q': 'q', 'r': 'r', 's': 's', 't': 't',
            'u': 'u', 'v': 'v', 'w': 'w', 'x': 'x', 'y': 'y', 'z': 'z',
            '0': '0', '1': '1', '2': '2', '3': '3', '4': '4',
            '5': '5', '6': '6', '7': '7', '8': '8', '9': '9'
        }
        mapped_keys = [key_map.get(k.lower(), k.lower()) for k in keys]
        pyautogui.hotkey(*mapped_keys)
        return f"已按下组合键：{'+'.join(keys)}"
    
    def _scroll(self, action: Dict, screen_size: Tuple[int, int]) -> str:
        clicks = action.get('clicks', 1)
        x, y = self._get_coordinates(action, screen_size) if 'x' in action else (None, None)
        pyautogui.scroll(clicks, x=x, y=y)
        return f"已滚动 {clicks} 个单位"
    
    def _wait(self, action: Dict) -> str:
        seconds = action.get('seconds', 1.0)
        time.sleep(seconds)
        return f"已等待 {seconds} 秒"


class ComputerAgent:
    """电脑操作 Agent 主类"""
    
    SYSTEM_PROMPT = """你是一个电脑操作助手，通过视觉分析屏幕并执行操作任务。

# 坐标系统（重要！）
- 使用 0-1000 的归一化坐标系
- (0, 0) = 屏幕左上角
- (1000, 1000) = 屏幕右下角  
- (500, 500) = 屏幕正中心
- x 轴：从左到右 0→1000
- y 轴：从上到下 0→1000

# 视觉定位方法（重要！）

## 1. 使用相对位置估算
- 屏幕左侧边缘：x ≈ 50-100
- 屏幕水平 1/4 位置：x ≈ 250
- 屏幕中心：x ≈ 500
- 屏幕水平 3/4 位置：x ≈ 750
- 屏幕右侧边缘：x ≈ 900-950

- 屏幕顶部边缘：y ≈ 50-100
- 屏幕垂直 1/4 位置：y ≈ 250
- 屏幕中心：y ≈ 500
- 屏幕垂直 3/4 位置：y ≈ 750
- 屏幕底部边缘：y ≈ 900-950

## 2. 常见 UI 元素的坐标特征
- macOS 顶部菜单栏：y ≈ 30-40
- macOS Dock 栏（底部）：y ≈ 920-980
- 窗口标题栏：y 坐标通常在窗口的顶部
- 窗口内容区域：在标题栏下方
- 按钮：通常在窗口底部或右下角

## 3. 使用 Spotlight 搜索（必须完整执行）

⚠️ 重要：Spotlight 搜索必须一次性完成所有步骤！

完整流程（必须在一次响应中包含所有步骤）：
1. 按 Cmd+Space 打开 Spotlight
2. 立即使用 type 输入应用名称
3. 按 Enter 打开应用

示例：
{"thought": "需要打开微信应用", "actions": [{"action_type": "hotkey", "parameters": {"keys": ["cmd", "space"]}}, {"action_type": "type", "parameters": {"text": "微信"}}, {"action_type": "press_key", "parameters": {"key": "enter"}}], "is_complete": false}

# 可用操作类型

## 鼠标操作
1. move_mouse - 移动鼠标 参数：{"x": 数字，"y": 数字}
2. click - 点击 参数：{"x": 数字，"y": 数字，"button": "left"|"right"}
3. double_click - 双击 参数：{"x": 数字，"y": 数字}

## 键盘操作
4. type - 输入文本 参数：{"text": "字符串", "clear_first": true/false}
5. press_key - 按下单键 参数：{"key": "enter"|"tab"|"backspace"|"esc"}
6. hotkey - 组合键 参数：{"keys": ["cmd", "c"]}

## 其他
7. scroll - 滚动 参数：{"clicks": 数字}
8. wait - 等待 参数：{"seconds": 数字}

# 返回格式（必须是纯 JSON，不要有任何其他文字）
{"thought": "分析屏幕内容", "actions": [{"action_type": "类型", "parameters": {}}], "is_complete": false}

# 重要提示
- 只返回纯 JSON，不要有任何 markdown 代码块
- 使用 Spotlight 时必须一次完成：Cmd+Space → 输入名称 → Enter
- 输入文本使用 type 操作，系统会自动粘贴"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config = Config(config_path)
        self._setup_logging()
        self.screen_capture = ScreenCapture(self.config.screenshot_quality, self.logger)
        self.executor = ActionExecutor(self.config, self.logger)
        self.client = OpenAI(
            base_url=self.config.api_base_url,
            api_key=self.config.api_key
        )
        
    def _setup_logging(self):
        log_level = getattr(logging, self.config.config['logging']['level'])
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        handlers = []
        if self.config.config['logging'].get('file'):
            file_handler = logging.FileHandler(self.config.config['logging']['file'])
            file_handler.setLevel(log_level)
            handlers.append(file_handler)
        if self.config.config['logging'].get('console', True):
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            handlers.append(console_handler)
        logging.basicConfig(level=log_level, format=log_format, handlers=handlers)
        self.logger = logging.getLogger(__name__)
        
    def _encode_image(self, image_data: bytes) -> str:
        return base64.b64encode(image_data).decode('utf-8')
    
    def _parse_ai_response(self, content: str) -> Dict[str, Any]:
        import re, json
        code_block_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', content)
        if code_block_match:
            return json.loads(code_block_match.group(1))
        content_stripped = content.strip()
        if content_stripped.startswith('{') and content_stripped.endswith('}'):
            return json.loads(content_stripped)
        return {"thought": content, "actions": [], "is_complete": False}
    
    def _send_to_ai(self, task: str, screenshot_base64: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        messages.extend(conversation_history)
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": f"任务：{task}"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{screenshot_base64}"}}
            ]
        })
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature
        )
        return self._parse_ai_response(response.choices[0].message.content)
    
    def run(self, task: str, max_iterations: int = 20) -> str:
        conversation_history = []
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            self.logger.info(f"=== 第 {iteration} 次迭代 ===")
            screenshot_data, screen_size = self.screen_capture.capture()
            screenshot_base64 = self._encode_image(screenshot_data)
            response = self._send_to_ai(task, screenshot_base64, conversation_history)
            thought = response.get('thought', '')
            actions = response.get('actions', [])
            is_complete = response.get('is_complete', False)
            self.logger.info(f"AI 思考：{thought}")
            conversation_history.append({"role": "assistant", "content": f"思考：{thought}\n操作：{actions}"})
            if actions:
                for action in actions:
                    result = self.executor.execute_action(action, screen_size)
                    self.logger.info(f"操作结果：{result}")
            if is_complete:
                return "任务执行完成"
            time.sleep(self.config.config['screen']['screenshot_interval'])
        return f"达到最大迭代次数 ({max_iterations})"


def main():
    import argparse
    parser = argparse.ArgumentParser(description='电脑操作 Agent')
    parser.add_argument('-t', '--task', required=True, help='要执行的任务描述')
    parser.add_argument('-m', '--max-iterations', type=int, default=20)
    args = parser.parse_args()
    agent = ComputerAgent()
    result = agent.run(args.task, args.max_iterations)
    print(f"任务执行结果：{result}")


if __name__ == '__main__':
    main()