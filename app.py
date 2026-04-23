from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
CORS(app) 

DB_FILE = 'daigong_users.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # 升级表结构：增加 age, gender, score, essay 字段
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            score INTEGER,
            essay TEXT
        )
    ''')
    
    # 初始化测试账号 admin
    test_user = "admin"
    test_password = "123456"
    cursor.execute('SELECT * FROM users WHERE username = ?', (test_user,))
    if not cursor.fetchone():
        hashed_pw = generate_password_hash(test_password)
        # admin 账号的附加信息可以留空
        cursor.execute('INSERT INTO users (username, password_hash, age, gender, score, essay) VALUES (?, ?, ?, ?, ?, ?)', 
                       (test_user, hashed_pw, 20, "系统管理员", 750, "我是初始账号"))
    conn.commit()
    conn.close()

# 强制初始化
init_db()

# 注册/申请接口
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    age = data.get('age')
    gender = data.get('gender')
    score = data.get('score')
    essay = data.get('essay')

    if not username or not password:
        return jsonify({"success": False, "message": "姓名和密码不能为空"}), 400

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        hashed_pw = generate_password_hash(password)
        cursor.execute('INSERT INTO users (username, password_hash, age, gender, score, essay) VALUES (?, ?, ?, ?, ?, ?)', 
                       (username, hashed_pw, age, gender, score, essay))
        conn.commit()
        return jsonify({"success": True, "message": "恭喜！你已被戴公大学正式录取！"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "该姓名/ID 已被占用，请尝试其他名称。"}), 400
    finally:
        conn.close()

# 登录接口
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # 登录时顺便把所有用户信息都查出来
    cursor.execute('SELECT password_hash, age, gender, score, essay FROM users WHERE username = ?', (username,))
    user_record = cursor.fetchone()
    conn.close()

    if user_record and check_password_hash(user_record[0], password):
        # 登录成功，返回用户档案
        return jsonify({
            "success": True, 
            "message": "登录成功！",
            "user_info": {
                "username": username,
                "age": user_record[1],
                "gender": user_record[2],
                "score": user_record[3],
                "essay": user_record[4]
            }
        }), 200
    else:
        return jsonify({"success": False, "message": "账号或密码错误"}), 401

# 新增：获取所有在校学生/校友名单的接口
@app.route('/api/students', methods=['GET'])
def get_all_students():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 从数据库中查询所有人（出于安全考虑，绝对不要把 password_hash 查出来发给前端）
    # 我们只拿：名字, 年龄, 性别, 分数, 文书
    cursor.execute('SELECT username, age, gender, score, essay FROM users')
    all_users = cursor.fetchall()
    conn.close()

    # 把查询到的数据整理成漂亮的 JSON 列表
    student_list = []
    for user in all_users:
        student_list.append({
            "username": user[0],
            "age": user[1],
            "gender": user[2],
            "score": user[3],
            "essay": user[4]
        })

    return jsonify({
        "success": True,
        "data": student_list
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
