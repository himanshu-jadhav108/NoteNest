from flask import Flask, render_template, request, redirect, flash , url_for
from flask_login import LoginManager ,login_user, logout_user, login_required, current_user
from models import db, bcrypt, User, Note
import sqlite3

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = 'supersecretkey'

db.init_app(app)
bcrypt.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'  # redirect if not logged in
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



# Database setup
def init_db():
    conn = sqlite3.connect('notes.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS notes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered. Please log in or use another email.", "danger")
            return redirect(url_for("register"))
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("index"))  # Redirect to home page after login
        else:
            flash("Login failed. Check email & password", "danger")
    return render_template("login.html")

# Home - show all notes
@app.route('/')
@login_required
def index():
    notes = Note.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', notes=notes)

# Add note
@app.route('/add', methods=['POST'])
@login_required
def add_note():
    title = request.form['title']
    content = request.form['content']
    note = Note(title=title, content=content, user_id=current_user.id)
    db.session.add(note)
    db.session.commit()
    flash('Note added!', 'success')
    return redirect(url_for('index'))

# Delete note
@app.route('/delete/<int:id>')
@login_required
def delete_note(id):
    note = Note.query.get_or_404(id)
    if note.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))
    db.session.delete(note)
    db.session.commit()
    flash('Note deleted!', 'success')
    return redirect(url_for('index'))

# Edit note
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_note(id):
    note = Note.query.get_or_404(id)
    if note.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        note.title = request.form['title']
        note.content = request.form['content']
        db.session.commit()
        flash('Note updated!', 'success')
        return redirect(url_for('index'))
    return render_template('edit.html', note=note)

# Logout

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))
    

if __name__ == '__main__':
    app.run(debug=True)
