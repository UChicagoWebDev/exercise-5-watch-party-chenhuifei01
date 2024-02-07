# app.py
import logging
import string
import traceback
import random
import sqlite3
from datetime import datetime
from flask import *  # Flask, g, redirect, render_template, request, url_for
from functools import wraps

app = Flask(__name__)

# These should make it so your Flask app always returns the latest version of
# your HTML, CSS, and JS files. We would remove them from a production deploy,
# but don't change them here.
app.debug = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache"
    return response


def get_db():
    db = getattr(g, '_database', None)

    if db is None:
        db = g._database = sqlite3.connect('db/watchparty.sqlite3')
        db.row_factory = sqlite3.Row
        setattr(g, '_database', db)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    db = get_db()
    cursor = db.execute(query, args)
    print("query_db")
    print(cursor)
    rows = cursor.fetchall()
    print(rows)
    db.commit()
    cursor.close()
    if rows:
        if one:
            return rows[0]
        return rows
    return None


def new_user():
    name = "Unnamed User #" + ''.join(random.choices(string.digits, k=6))
    password = ''.join(random.choices(
        string.ascii_lowercase + string.digits, k=10))
    api_key = ''.join(random.choices(
        string.ascii_lowercase + string.digits, k=40))
    u = query_db('insert into users (name, password, api_key) ' +
                 'values (?, ?, ?) returning id, name, password, api_key',
                 (name, password, api_key),
                 one=True)
    return u


def get_user_from_cookie(request):
    user_id = request.cookies.get('user_id')
    password = request.cookies.get('user_password')
    if user_id and password:
        return query_db('select * from users where id = ? and password = ?', [user_id, password], one=True)
    return None


def render_with_error_handling(template, **kwargs):
    try:
        return render_template(template, **kwargs)
    except:
        t = traceback.format_exc()
        return render_template('error.html', args={"trace": t}), 500

# ------------------------------ NORMAL PAGE ROUTES ----------------------------------


@app.route('/')
def index():
    print("index")  # For debugging
    user = get_user_from_cookie(request)

    if user:
        rooms = query_db('select * from rooms')
        return render_with_error_handling('index.html', user=user, rooms=rooms)

    return render_with_error_handling('index.html', user=None, rooms=None)


@app.route('/rooms/new', methods=['GET', 'POST'])
def create_room():
    print("create room")  # For debugging
    user = get_user_from_cookie(request)
    if user is None:
        return {}, 403

    if (request.method == 'POST'):
        name = "Unnamed Room " + ''.join(random.choices(string.digits, k=6))
        room = query_db(
            'insert into rooms (name) values (?) returning id', [name], one=True)
        return redirect(f'{room["id"]}')
    else:
        return app.send_static_file('create_room.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    print("signup")
    user = get_user_from_cookie(request)

    if user:
        return redirect('/profile')
        # return render_with_error_handling('profile.html', user=user) # redirect('/')

    if request.method == 'POST':
        u = new_user()
        print("u")
        print(u)
        for key in u.keys():
            print(f'{key}: {u[key]}')

        resp = redirect('/profile')
        resp.set_cookie('user_id', str(u['id']))
        resp.set_cookie('user_password', u['password'])
        return resp

    return redirect('/login')


@app.route('/profile')
def profile():
    print("profile")
    user = get_user_from_cookie(request)
    if user:
        return render_with_error_handling('profile.html', user=user)

    redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    print("login")
    user = get_user_from_cookie(request)

    if user:
        return redirect('/')

    if request.method == 'POST':
        name = request.form['username']
        password = request.form['password']
        u = query_db('select * from users where name = ? and password = ?',
                     [name, password], one=True)
        if u:  # 正確檢查從數據庫查詢到的用戶變量u，而不是user
            resp = make_response(redirect("/"))
            resp.set_cookie('user_id', str(u['id']))  # 確保使用正確的方式從行對象中獲取數據
            # 注意：實際應用中不應將密碼存儲於cookie
            resp.set_cookie('user_password', u['password'])
            return resp

    return render_with_error_handling('login.html', failed=True)


@app.route('/logout')
def logout():
    resp = make_response(redirect('/'))
    resp.set_cookie('user_id', '')
    resp.set_cookie('user_password', '')
    return resp


@app.route('/rooms/<int:room_id>')
def room(room_id):
    user = get_user_from_cookie(request)
    if user is None:
        return redirect('/')

    room = query_db('select * from rooms where id = ?', [room_id], one=True)
    return render_with_error_handling('room.html',
                                      room=room, user=user)

# -------------------------------- API ROUTES ----------------------------------


def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('Authorization')
        if api_key is None:
            return jsonify({"error": "API key is missing"}), 403

        api_key = api_key.replace("Bearer ", "", 1)

        user = query_db('SELECT * FROM users WHERE api_key = ?',
                        [api_key], one=True)
        if user is None:
            return jsonify({"error": "Invalid API key"}), 403

        return f(*args, **kwargs)
    return decorated_function


# POST to change the user's name


@app.route('/api/user/update/username', methods=['POST'])
@require_api_key
def update_user_username():
    user = get_user_from_cookie(request)
    print("user: ", user)
    if not user:
        return jsonify({'error': 'Authentication required'}), 403

    new_username = request.json.get('new_username')
    if not new_username:
        return jsonify({'error': 'New username is required'}), 400

    try:
        query_db('UPDATE users SET name = ? WHERE id = ?',
                 [new_username, user['id']])
        return jsonify({'success': 'Username updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# POST to change the user's password


@app.route('/api/user/update/password', methods=['POST'])
@require_api_key
def update_user_password():
    user = get_user_from_cookie(request)
    if not user:
        return jsonify({'error': 'Authentication required'}), 403

    new_password = request.json.get('new_password')
    if not new_password:
        return jsonify({'error': 'New password is required'}), 400

    try:
        query_db('UPDATE users SET password = ? WHERE id = ?',
                 [new_password, user['id']])
        return jsonify({'success': 'Password updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# POST to change the name of a room
@app.route('/api/rooms/<int:room_id>/update', methods=['POST'])
@require_api_key
def update_room_name(room_id):
    user = get_user_from_cookie(request)
    if user is None:
        return jsonify({'error': 'Authentication required'}), 403

    new_name = request.json.get('name')
    if not new_name:
        return jsonify({'error': 'New name is required'}), 400

    try:
        query_db('UPDATE rooms SET name = ? WHERE id = ?', [new_name, room_id])
        return jsonify({'success': 'Room name updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# GET to get all the messages in a room
# query data from database, and send json format to js function
@app.route('/api/rooms/<int:room_id>/messages', methods=['GET'])
def get_room_messages(room_id):
    query = """
    SELECT m.id, m.body, u.name as author, m.room_id
    FROM messages m
    JOIN users u ON m.user_id = u.id
    WHERE m.room_id = ?
    ORDER BY m.id ASC;
    """
    db = get_db()
    cur = db.execute(query, [room_id])
    messages = cur.fetchall()

    messages_list = [dict(id=row['id'], body=row['body'],
                          author=row['author'], room_id=row['room_id']) for row in messages]
    return jsonify(messages_list)


# POST to post a new message to a room
@app.route('/api/rooms/<int:room_id>/messages/post', methods=['POST'])
@require_api_key
def post_room_message(room_id):
    # Authentication check (simplified version, replace with actual auth check)
    user = get_user_from_cookie(request)
    print("user: ", user)
    if user is None:
        return jsonify({'error': 'Authentication required'}), 403

    # Extracting message body from the POST request
    message_body = request.json.get('body')
    print("message_body: ", message_body)
    if not message_body:
        return jsonify({'error': 'Message body is required'}), 400

    # Insert message into the database
    try:
        query = """
        INSERT INTO messages (user_id, room_id, body)
        VALUES (?, ?, ?)
        """
        query_db(query, [user['id'], room_id, message_body])
        return jsonify({'success': 'Message posted successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


app.run(host='0.0.0.0', port=3000, debug=True)
