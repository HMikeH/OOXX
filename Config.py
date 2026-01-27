"""
Config.py - 應用配置設定

從 config.json 加載配置
參數：
- SECRET_KEY: 用於 Flask session 的密鑰
- HOST: 應用運行的主機地址
- FLASK_RUN_PORT: Flask 運行的端口號
- DEBUG: 是否啟用調試模式
"""
import json

with open('config.json', 'r') as f:
    _config = json.load(f)

class Config:
    SECRET_KEY = _config.get('SECRET_KEY', 'SINBON')
    HOST = _config.get('HOST', '0.0.0.0')
    FLASK_RUN_PORT = int(_config.get('FLASK_RUN_PORT', 5000))
    DEBUG = bool(_config.get('DEBUG', True))
