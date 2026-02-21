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
        """截取屏幕"""
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
        return jpeg_data, actual_resolution
    
    def get_screen_size(self) -> Tuple[int, int]:
        """获取屏幕分辨率"""
        return self.logic_size


class CoordinateMapper:
    """坐标映射器"""
    
    def __init__(self, virtual_resolution: int = 1000):
        self.virtual_resolution = virtual_resolution
        
    def map_coordinates(self, ai_x: float, ai_y: float, actual_width: int, actual_height: int) -> Tuple[int, int]:
        """将 AI 坐标映射到实际屏幕坐标"""
        ai_x = max(0, min(ai_x, self.virtual_resolution))
        ai_y = max(0, min(ai_y, self.virtual_resolution))
        scale_x = actual_width / self.virtual_resolution
        scale_y = actual_height / self.virtual_resolution
        actual_x = int(ai_x * scale_x)
        actual_y = int(ai_y * scale_y)
        return actual_x, actual_y


class ActionExecutor:
    """操作执行器"""
    
    def __init__(self, config: Config, logger=None):
        self.config = config
        self.mapper = CoordinateMapper(config.virtual_resolution)
        self.logger = logger or logging.getLogger(__name__)
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = config.click_interval
        
    def execute_action(self, action: Dict[str, Any], screen_size: Tuple[int, int]) -> str:
        """执行单个操作"""
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
            return f"已输入文本：{text[:50]}{'...' if len(text) > 50 else ''}"
        except Exception as e:
            pyautogui.write(text, interval=self.config.type_interval)
            return f"已输入文本（模拟键盘）: {text[:50]}{'...' if len(text) > 50 else ''}"
    
    def _press_key(self, action: Dict) -> str:
        params = self._get_params(action)
        key = params.get('key', '')
        pyautogui.press(key)
        return f"已按下按键：{key}"
    
    def _hotkey(self, action: Dict) -> str:
        params = self._get_params(action)
        keys = params.get('keys', [])
        if not keys:
            return "错误：未指定组合键"
        key_map = {
            'ctrl': 'command', 'control': 'command', 'cmd': 'command',
            'alt': 'option', 'option': 'option', 'win': 'command'
        }
        mapped_keys = [key_map.get(k.lower(), k.lower()) for k in keys]
        pyautogui.hotkey(*mapped_keys)
        return f"已按下组合键：{'+'.join(keys)}"
    
    def _scroll(self, action: Dict, screen_size: Tuple[int, int]) -> str:
        clicks = action.get('clicks', 1)
        pyautogui.scroll(clicks)
        return f"已滚动 {clicks} 个单位"
    
    def _wait(self, action: Dict) -> str:
        seconds = action.get('seconds', 1.0)
        time.sleep(seconds)
        return f"已等待 {seconds} 秒"


class ComputerAgent:
    """电脑操作 Agent 主类"""
    
    SYSTEM_PROMPT = """你是一个电脑操作助手，通过视觉分析屏幕并执行操作任务。

## 坐标系统
- 使用 0-1000 的归一化坐标系
- (0, 0) = 屏幕左上角，(1000, 1000) = 屏幕右下角

## 可用操作类型
1. move_mouse - 移动鼠标
2. click - 点击
3. double_click - 双击
4. type - 输入文本
5. press_key - 按下单键
6. hotkey - 组合键
7. scroll - 滚动
8. wait - 等待

## 返回格式（必须是纯 JSON）
{
    "thought": "分析屏幕内容",
    "actions": [{"action_type": "类型", "参数": "值"}],
    "is_complete": false
}"""

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
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
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