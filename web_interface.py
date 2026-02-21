#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web 界面服务器 - 提供现代化的操作界面
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import threading
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'computer-agent-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 存储当前任务状态
task_status = {
    'running': False,
    'current_task': None,
    'logs': [],
    'result': None
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    return jsonify(task_status)

@app.route('/api/start', methods=['POST'])
def start_task():
    data = request.json
    task = data.get('task', '')
    if not task:
        return jsonify({'error': '任务描述不能为空'}), 400
    
    if task_status['running']:
        return jsonify({'error': '已有任务正在运行'}), 400
    
    task_status['running'] = True
    task_status['current_task'] = task
    task_status['logs'] = []
    task_status['result'] = None
    
    # 在后台线程中运行任务
    thread = threading.Thread(target=run_task, args=(task,))
    thread.start()
    
    return jsonify({'message': '任务已启动'})

@app.route('/api/stop', methods=['POST'])
def stop_task():
    task_status['running'] = False
    return jsonify({'message': '任务已停止'})

def run_task(task):
    """在后台运行任务"""
    try:
        from main import ComputerAgent
        agent = ComputerAgent()
        
        class LogHandler(logging.Handler):
            def emit(self, record):
                log_entry = self.format(record)
                task_status['logs'].append(log_entry)
                socketio.emit('log', {'message': log_entry})
        
        log_handler = LogHandler()
        log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger('main').addHandler(log_handler)
        
        result = agent.run(task)
        task_status['result'] = result
        socketio.emit('complete', {'result': result})
    except Exception as e:
        task_status['logs'].append(f"错误：{str(e)}")
        socketio.emit('error', {'error': str(e)})
    finally:
        task_status['running'] = False

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)