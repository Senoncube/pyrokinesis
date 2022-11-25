from flask import Flask, render_template, request, session, redirect, url_for, flash
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = 'aboba bebra'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite'
app.permanent_session_lifetime = timedelta(days=15)

db = SQLAlchemy(app)
with app.app_context():
    db.create_all()

class users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    albums = db.relationship('album', backref='user')

    def __init__(self, username, password):
        self.username = username
        self.password = password


class album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    cover = db.Column(db.String(100), nullable=False)
    post_author = db.Column(db.Integer, db.ForeignKey('users.id'))
    path = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(500))
    songs = db.relationship('song', backref='album')



class song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    in_alb_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    length = db.Column(db.String(50), nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'))

    def __init__(self, alb_id, name, length, album_id):
        self.in_alb_id = alb_id
        self.name = name
        self.length = length
        self.album_id = album_id

albums_list = [
    {
        'name': 'Акустический',
        'cover': '30d251d2f344acc92cd15d5a1949d406.1000x1000x1.jpg',
        'track_count': '8',
        'year': '2019',
        'post_author': 'Senon',
        'path': 'akusticheskiy',
        'description': 'Акустичний альбом',
        'songs': [
            {
                'id': '1',
                'name': 'Восток моей юности',
                'length': '3:15'
            },
            {
                'id': '2',
                'name': 'Абоба бебра',
                'length': '2:10'
            }
        ]
    },
    {
        'name': 'FINAL FANTASY',
        'cover': 'final_fantasy.jpg',
        'track_count': '7',
        'year': '2016',
        'post_author': 'Senon',
        'path': 'akusticheskiy',
        'description': 'Акустичний альбом',
        'songs': [
            {
                'id': '1',
                'name': 'Okean',
                'length': '3:15'
            },
            {
                'id': '2',
                'name': 'Абоба бебра',
                'length': '2:10'
            }
        ]
    }
]

@app.route('/')
def home():  # put application's code here
    db.create_all()
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/albums')
def albums():
    db.create_all()
    albums_list = album.query.filter_by().all()
    authrors = {}
    for i in albums_list:
        authrors[i.id] = users.query.filter_by(id=i.post_author).first().username
    return render_template('albums.html', albums=albums_list, authors=authrors)

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        found_user = users.query.filter_by(username=username).first()
        if found_user:
            if found_user.password == request.form['password']:
                session.permanent = True
                session['user'] = username
                flash(f'Успіщний вхід в аккаунт {username}', 'norm')
                return redirect(url_for('home'))
            else:
                flash('Непрвильний пароль!', 'bad')
        else:
            flash('Непрвильний логін!', 'bad')
    elif 'user' in session:
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/register', methods=['POST', 'GET'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        password1 = request.form['password']
        password2 = request.form['password_confirm']
        print(username, password1)
        check_user = users.query.filter_by(username=username).first()
        if not check_user and password1 == password2: # доделать проверку на уникальность логина
            db.session.add(users(username, password1))
            db.session.commit()
            session.permanent = True
            session['user'] = username
            print(session['user'])
            flash(f'Аккаунт {username} успішно створено!', 'norm')
            return redirect(url_for('home'))
        else:
            if password1 == password2:
                flash('Акккаунт з таким логіном уже існує!', 'bad')
            else:
                flash('Паролі не однакові!', 'bad')
    elif 'user' in session:
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    if 'user' in session:
        session.pop('user', None)
        flash('Ви вийшли з аккаунту!', 'info')
    return redirect(url_for('home'))

@app.route('/albums/<path>')
def album_path(path):
    alb = album.query.filter_by(path=path).first()
    alb_author = users.query.filter_by(id=alb.post_author).first()
    return render_template('album_layout.html', album=alb, post_author=alb_author.username)

@app.route('/albums/<path>_edit', methods=['POST', 'GET'])
def album_edit(path):
    if 'user' not in session:
        flash('У вас не має прав доступу до цього меню', 'bad')
        return redirect(url_for('home'))
    alb = album.query.filter_by(path=path).first()
    if request.method == 'POST':
        prew = alb

        alb.name = request.form['name']
        alb.year = request.form['year']
        alb.description = request.form['description']
        alb.path = request.form['path']

        past_songs = song.query.filter_by(album_id=alb.id).all()

        if request.files['img_file']:
            image = request.files['img_file']
            image.save(os.path.join('static/covers/', image.filename))
            alb.cover = image.filename

        for sg in past_songs:
            db.session.delete(sg)

        songs_count = int(request.form['songs_count'])

        songs = []

        for i in range(songs_count):
            print(f'id_{i}: {request.form["id_0"]}')
            id = request.form[f'id_{i}']
            name = request.form[f'name_{i}']
            length = request.form[f'length_{i}']
            s = song(id, name, length, alb.id)
            songs.append(s)
            db.session.add(s)

        if not check_album(alb, songs, prew):
            return render_template('edit_album_layout.html', album=alb, redact=True)

        db.session.commit()
        flash(f'Альбом "{alb.name}" змінено!', 'norm')
        return redirect(f'/albums/{alb.path}')

    alb_author = users.query.filter_by(id=alb.post_author).first()
    return render_template('edit_album_layout.html', album=alb, post_author=alb_author.username, redact=True)

@app.route('/albums/<path>_delete')
def delete_album(path):
    if 'user' not in session:
        flash('У вас не має прав доступу до цього меню', 'bad')
        return redirect(url_for('home'))
    alb = album.query.filter_by(path=path).first()
    if alb:
        db.session.delete(alb)
        db.session.commit()
        flash(f'Альбом {alb.name} було видалено!', 'info')
    else:
        flash('Такого альбому не існує!', 'bad')
    return redirect(url_for('albums'))

@app.route('/albums/create', methods=['POST', 'GET'])
def create():
    if 'user' not in session:
        flash('У вас не має прав доступу до цього меню', 'bad')
        return redirect(url_for('home'))
    if request.method == 'POST':
        new_album = album()
        new_album.name = request.form['name']
        new_album.year = request.form['year']
        new_album.description = request.form['description']
        new_album.path = request.form['path']
        author_name = session['user']
        new_album.post_author = users.query.filter_by(username=author_name).first().id


        if request.files['img_file']:
            image = request.files['img_file']
            image.save(os.path.join('static/covers/', image.filename))
            new_album.cover = image.filename
        else:
            new_album.cover = 'standart.png'


        if album.query.filter_by().all():
            album_id = album.query.filter_by().all()[-1].id + 1
        else:
            new_album.id = 1
            album_id = 1

        songs_count = int(request.form['songs_count'])

        songs = []

        for i in range(songs_count):
            id = request.form[f'id_{i}']
            name = request.form[f'name_{i}']
            length = request.form[f'length_{i}']
            s = song(id, name, length, album_id)
            songs.append(s)
            db.session.add(s)

        if not check_album(new_album, songs):
            return render_template('edit_album_layout.html', album=new_album, redact=False)

        db.session.add(new_album)
        db.session.commit()
        flash(f'Альбом "{new_album.name}" додано до списку!', 'norm')
        return redirect(url_for('albums'))

    return render_template('edit_album_layout.html', redact=False)

@app.errorhandler(404)
def error_404(e):
    return render_template('404.html'), 404

def check_album(alb, songs, prew = None):
    if not prew or prew.name != alb.name:
        if album.query.filter_by(name=alb.name).first():
            flash('Альбом за такою назвою уже існує!', 'bad')
            return False
        if album.query.filter_by(path=alb.path).first():
            flash('Альбом з таким шляхом уже існує!', 'bad')
            return False
    if alb.path.endswith('_edit'):
        flash('Назва не може закінчуватися на "_edit"!', 'bad')
        return False
    if len(alb.name) < 4:
        flash('Назва повинна бути мінімум 4 символи!', 'bad')
        return False
    if len(alb.path) < 4:
        flash('Шлях повинен бути мінімум 4 символи!', 'bad')
        return False
    for sg in songs:
        for sgj in songs:
            if sg.in_alb_id == sgj.in_alb_id and sg != sgj:
                flash('У пісень повинні бути унікальні номера!', 'bad')
                return False
        if len(sg.name) < 4:
            flash('Назви пісень повинні бути не менше 4 символів!', 'bad')
            return False
    return True

if __name__ == '__main__':
    db.create_all()
    app.run()
