from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'


def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    return redirect(url_for('news'))


@app.route('/news')
def news():
    conn = get_db_connection()
    news_list = conn.execute('SELECT * FROM news').fetchall()
    conn.close()
    return render_template('news.html', news=news_list)


@app.route('/open_events')
def open_events():
    conn = get_db_connection()
    events = conn.execute('SELECT * FROM events WHERE status = "open"').fetchall()

    user_registrations = set()
    if 'user_id' in session:
        user_id = session['user_id']
        registrations = conn.execute(
            'SELECT event_id FROM event_registrations WHERE user_id = ?',
            (user_id,)
        ).fetchall()
        user_registrations = {row['event_id'] for row in registrations}

    conn.close()
    return render_template('open_events.html', events=events, user_registrations=user_registrations)



@app.route('/closed_events')
def closed_events():
    conn = get_db_connection()
    events = conn.execute('SELECT * FROM events WHERE status = "closed"').fetchall()
    conn.close()
    return render_template('closed_events.html', events=events)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        birth_year = request.form['birth_year']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        email = request.form['email']
        phone = request.form['phone']

        if password != confirm_password:
            flash('Пароли не совпадают!', 'danger')
            return redirect(url_for('register'))

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO users (full_name, birth_year, username, password, email, phone)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (full_name, birth_year, username, password, email, phone))
        conn.commit()
        conn.close()

        flash('Вы успешно зарегистрировались!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?',
                            (username, password)).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Вы вошли в систему!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверные учетные данные!', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему!', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()

    # Получаем данные пользователя
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    # Получаем список секций, в которых состоит пользователь
    sections = conn.execute('SELECT section_name FROM user_sections WHERE user_id = ?', (user_id,)).fetchall()

    # Получаем мероприятия, на которые записан пользователь
    upcoming_events = conn.execute('''
        SELECT events.name, events.description FROM events
        JOIN event_registrations ON events.id = event_registrations.event_id
        WHERE event_registrations.user_id = ? AND events.status = "open"
    ''', (user_id,)).fetchall()

    # Получаем результаты прошедших мероприятий
    past_events = conn.execute('''
        SELECT events.name, events.description, events.results FROM events
        JOIN event_registrations ON events.id = event_registrations.event_id
        WHERE event_registrations.user_id = ? AND events.status = "closed"
    ''', (user_id,)).fetchall()

    conn.close()

    return render_template('profile.html', user=user, sections=sections, upcoming_events=upcoming_events,
                           past_events=past_events)


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему!', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()

    if request.method == 'POST':
        full_name = request.form['full_name']
        birth_year = request.form['birth_year']
        phone = request.form['phone']
        email = request.form['email']

        conn.execute('''
            UPDATE users SET full_name = ?, birth_year = ?, phone = ?, email = ?
            WHERE id = ?
        ''', (full_name, birth_year, phone, email, user_id))

        conn.commit()
        conn.close()
        flash('Информация обновлена!', 'success')
        return redirect(url_for('profile'))

    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()

    return render_template('edit_profile.html', user=user)


@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему!', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        user_id = session['user_id']
        new_password = request.form['password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash('Пароли не совпадают!', 'danger')
            return redirect(url_for('change_password'))

        conn = get_db_connection()
        conn.execute('UPDATE users SET password = ? WHERE id = ?', (new_password, user_id))
        conn.commit()
        conn.close()

        flash('Пароль успешно изменен!', 'success')
        return redirect(url_for('profile'))

    return render_template('change_password.html')


@app.route('/register_for_event/<int:event_id>', methods=['POST'])
def register_for_event(event_id):
    if 'user_id' not in session:
        flash('Сначала войдите в систему!', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']

    conn = get_db_connection()
    conn.execute('INSERT INTO event_registrations (user_id, event_id) VALUES (?, ?)', (user_id, event_id))
    conn.commit()
    conn.close()

    flash('Вы успешно записались на мероприятие!', 'success')
    return redirect(url_for('open_events'))


@app.route('/toggle_event/<int:event_id>', methods=['POST'])
def toggle_event(event_id):
    if 'user_id' not in session:
        flash('Сначала войдите в систему!', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()

    # Проверяем, записан ли пользователь
    registration = conn.execute(
        'SELECT * FROM event_registrations WHERE user_id = ? AND event_id = ?',
        (user_id, event_id)
    ).fetchone()

    if registration:
        # Если записан — удаляем запись
        conn.execute('DELETE FROM event_registrations WHERE user_id = ? AND event_id = ?', (user_id, event_id))
        flash('Вы отказались от участия.', 'info')
    else:
        # Если не записан — добавляем
        conn.execute('INSERT INTO event_registrations (user_id, event_id) VALUES (?, ?)', (user_id, event_id))
        flash('Вы успешно записались!', 'success')

    conn.commit()
    conn.close()
    return redirect(url_for('open_events'))


@app.route('/news/<int:news_id>')
def news_detail(news_id):
    conn = get_db_connection()
    news_item = conn.execute('SELECT * FROM news WHERE id = ?', (news_id,)).fetchone()
    conn.close()

    if news_item is None:
        flash('Новость не найдена!', 'danger')
        return redirect(url_for('news'))

    return render_template('news_detail.html', news=news_item)


@app.route('/event/<int:event_id>')
def event_detail(event_id):
    conn = get_db_connection()
    event = conn.execute('SELECT * FROM events WHERE id = ?', (event_id,)).fetchone()
    conn.close()

    if event is None:
        flash('Мероприятие не найдено!', 'danger')
        return redirect(url_for('open_events'))

    return render_template('event_detail.html', event=event)


if __name__ == '__main__':
    app.run(debug=True)