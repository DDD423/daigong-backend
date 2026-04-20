from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
CORS(app) # 允许跨域请求，让你的前端可以访问这个后端

DB_FILE = 'daigong_users.db'

# 初始化数据库并创建一个测试账号
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # 创建用户表：包含 id, 学号(username), 加密后的密码(password_hash)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    
    # 手动插入一个测试账号（满足你的需求）
    # 假设学号是 admin，密码是 123456
    test_user = "admin"
    test_password = "123456"
    
    # 先检查这个测试账号是不是已经存在了
    cursor.execute('SELECT * FROM users WHERE username = ?', (test_user,))
    if not cursor.fetchone():
        # 【重点】这里我们将密码 123456 变成了哈希乱码再存入！
        hashed_pw = generate_password_hash(test_password)
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (test_user, hashed_pw))
        print(f"🎉 测试账号创建成功！账号: {test_user}, 密码: {test_password}")
        print(f"👀 在数据库中，它的密码看起来是这样的: {hashed_pw}")
        
    conn.commit()
    conn.close()

# ★★★ 关键修复：直接在这里调用函数，确保 Gunicorn 启动时一定会执行它！
init_db()

# 接收前端登录请求的接口
@app.route('/api/login', methods=['POST'])
def login():
    # 1. 获取前端发来的 JSON 数据
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"success": False, "message": "学号和密码不能为空"}), 400

    # 2. 去数据库里找这个用户
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
    user_record = cursor.fetchone()
    conn.close()

    # 3. 验证逻辑
    if user_record is None:
        return jsonify({"success": False, "message": "该学号不存在，请查证。"}), 401
    
    stored_hash = user_record[0]
    
    # 4. 比对密码（用前端传来的明文和数据库的乱码进行比对）
    if check_password_hash(stored_hash, password):
        return jsonify({"success": True, "message": "登录成功！欢迎来到戴公大学教务系统。"}), 200
    else:
        return jsonify({"success": False, "message": "密码错误，请重试。"}), 401

if __name__ == '__main__':
    # 因为上面已经全局调用了 init_db()，这里就不需要再调用了
    
    # 获取云平台分配的端口，如果在本地运行则默认使用 5000
    port = int(os.environ.get("PORT", 5000))
    # host='0.0.0.0' 允许外部网络访问你的程序
    app.run(debug=False, host='0.0.0.0', port=port)
