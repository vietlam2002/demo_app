from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os


app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Cấu hình thư mục lưu trữ file upload
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Tạo thư mục nếu chưa tồn tại
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db_connection():
    conn = psycopg2.connect(
        dbname="mydatabase",
        user="postgres",
        password="password",
        host="localhost",
        port=3000
    )
    return conn

@app.route('/')
def index():
    if 'user_id' in session:
        conn = get_db_connection()
        cur = conn.cursor()

        # Lấy thông tin người dùng hiện tại
        cur.execute('SELECT username, coin FROM users WHERE id = %s', (session['user_id'],))
        user = cur.fetchone()

        # Lấy danh sách tất cả người dùng, ngoại trừ người dùng hiện tại
        cur.execute('SELECT id, username FROM users WHERE id != %s', (session['user_id'],))
        users = cur.fetchall()

        cur.close()
        conn.close()
        return render_template('dashboard.html', user=user, users=users)
    return redirect(url_for('login'))

@app.route('/joke/<int:user_id>', methods=['POST'])
def joke(user_id):
    if 'user_id' in session:
        conn = get_db_connection()
        cur = conn.cursor()

        # Lấy số dư coin của người dùng hiện tại
        cur.execute('SELECT coin FROM users WHERE id = %s', (session['user_id'],))
        sender_coin = cur.fetchone()[0]

        if sender_coin >= 50:
            # Trừ 50 coin từ người dùng hiện tại
            cur.execute('UPDATE users SET coin = coin - 50 WHERE id = %s', (session['user_id'],))
            conn.commit()

        cur.close()
        conn.close()

    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, password FROM users WHERE username = %s', (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            return redirect(url_for('index'))
        return 'Invalid credentials'
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, password))
            conn.commit()
        except Exception as e:
            conn.rollback()
            return str(e)
        cur.close()
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/transfer', methods=['POST'])
def transfer():
    if 'user_id' in session:
        recipient_username = request.form['username']
        amount = int(request.form['amount'])

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('SELECT coin FROM users WHERE id = %s', (session['user_id'],))
        sender_coin = cur.fetchone()[0]

        if sender_coin >= amount:
            cur.execute('UPDATE users SET coin = coin - %s WHERE id = %s', (amount, session['user_id']))
            cur.execute('UPDATE users SET coin = coin + %s WHERE username = %s', (amount, recipient_username))
            conn.commit()

        cur.close()
        conn.close()

    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Lưu thông tin file vào database
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('INSERT INTO files (user_id, filename, filepath) VALUES (%s, %s, %s)', 
                        (session['user_id'], filename, filepath))
            cur.execute('UPDATE users SET coin = coin + 30 WHERE id = %s', (session['user_id'],))
            conn.commit()
            cur.close()
            conn.close()

            flash('File uploaded successfully and 30 coins added to your balance.')
            return redirect(url_for('index'))
    return render_template('upload.html')

@app.route('/library')
def library():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, filename, user_id FROM files')
    files = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('library.html', files=files)

@app.route('/download/<int:file_id>')
def download_file(file_id):
    if 'user_id' in session:
        conn = get_db_connection()
        cur = conn.cursor()

        # Trừ 10 coin khi mở file
        cur.execute('SELECT coin FROM users WHERE id = %s', (session['user_id'],))
        user_coin = cur.fetchone()[0]
        
        if user_coin >= 10:
            cur.execute('UPDATE users SET coin = coin - 10 WHERE id = %s', (session['user_id'],))
            cur.execute('SELECT filepath FROM files WHERE id = %s', (file_id,))
            file = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()

            if file:
                return send_file(file[0], as_attachment=True)
            else:
                flash('File not found.')
                return redirect(url_for('library'))
        else:
            flash('Not enough coins.')
            return redirect(url_for('library'))

    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
