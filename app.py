from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import os
import smtplib
from email.message import EmailMessage
from werkzeug.utils import secure_filename # NEW: Safely handles file uploads
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

app = Flask(__name__)
DATABASE = 'reviews.db'
app.secret_key = 'super_secret_studio_key' # Required to keep her logged in securely
CLIENT_PASSWORD = os.getenv("CLIENT_PASSWORD")# NEW: Configure where uploaded portfolio images will be saved
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True) # Creates the folder if it doesn't exist

# ==========================================================
# 1. EMAIL CONFIGURATION (CRITICAL)
# ==========================================================
# The email receiving the notification
ADMIN_RECEIVER_EMAIL = "thevisionthedesignstudioo@gmail.com" 

# The email sending the notification (Usually the same as above)
load_dotenv()

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

ADMIN_RECEIVER_EMAIL = os.getenv("ADMIN_RECEIVER_EMAIL")

# ==========================================================
# DATABASE SETUP
# ==========================================================
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row 
    return conn

def init_db():
    with app.app_context():
        db = get_db_connection()
        # Existing reviews table
        db.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT NOT NULL,
                review_text TEXT NOT NULL,
                rating INTEGER, 
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        # NEW: Projects table for the portfolio
        db.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                image_filename TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        db.commit()

# ==========================================================
# ROUTES
# ==========================================================
# ==========================================================
# CLIENT ADMIN LOGIN ROUTES
# ==========================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # If she enters the right password, log her in!
        if request.form.get('password') == CLIENT_PASSWORD:
            session['is_admin'] = True
            return redirect(url_for('portfolio'))
        else:
            return "<h3 style='color:red; text-align:center; margin-top:50px;'>Incorrect Password</h3>"
            
    # The simple, hidden login screen
    return '''
        <div style="font-family: sans-serif; text-align: center; margin-top: 15vh;">
            <h2>Studio Admin Access</h2>
            <p style="color: gray; margin-bottom: 20px;">Upload new projects & manage reviews</p>
            <form method="post">
                <input type="password" name="password" placeholder="Enter Password" required style="padding: 10px; width: 250px; border: 1px solid #ccc;"><br><br>
                <button type="submit" style="padding: 10px 30px; background: #c0a98e; color: white; border: none; cursor: pointer; text-transform: uppercase;">Log In</button>
            </form>
        </div>
    '''

@app.route('/logout')
def logout():
    session.pop('is_admin', None) # Logs her out
    return redirect(url_for('home'))

@app.route('/')
def home():
    conn = get_db_connection()
    reviews = conn.execute(
        'SELECT * FROM reviews ORDER BY timestamp DESC LIMIT 3'
    ).fetchall()
    conn.close()

    is_admin = session.get('is_admin', False)

    return render_template(
        'home.html',
        reviews=reviews,
        is_admin=is_admin
    )

@app.route('/about')
def about():
    return render_template('about.html')


# ==========================================================
# PORTFOLIO ROUTES
# ==========================================================
@app.route('/portfolio')
def portfolio():
    conn = get_db_connection()
    # Force create table if it's missing
    conn.execute('''CREATE TABLE IF NOT EXISTS projects 
                   (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, category TEXT, image_filename TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    projects = conn.execute('SELECT * FROM projects ORDER BY timestamp DESC').fetchall()
    conn.close()
    
    # CHANGE THIS LINE: It must match the session key you set in /login
    is_admin = session.get('is_admin', False) 
    
    return render_template('portfolio.html', projects=projects, is_admin=is_admin)

@app.route('/add-project', methods=['POST'])
def add_project():
    # NEW: Only allow the upload if she is logged in
    if session.get('is_admin'):
        title = request.form.get('title')
        category = request.form.get('category')
        file = request.files.get('image')

        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            conn = get_db_connection()
            conn.execute('INSERT INTO projects (title, category, image_filename) VALUES (?, ?, ?)', (title, category, filename))
            conn.commit()
            conn.close()
            
    return redirect(url_for('portfolio'))

@app.route('/delete-project/<int:project_id>', methods=['POST'])
def delete_project(project_id):
    # NEW: Only allow deletion if she is logged in
    if session.get('is_admin'):
        conn = get_db_connection()
        project = conn.execute('SELECT image_filename FROM projects WHERE id = ?', (project_id,)).fetchone()
        if project:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], project['image_filename'])
            if os.path.exists(filepath):
                os.remove(filepath)
                
        conn.execute('DELETE FROM projects WHERE id = ?', (project_id,))
        conn.commit()
        conn.close()
        
    return redirect(url_for('portfolio'))

@app.route('/reviews')
def reviews():

    conn = get_db_connection()
    reviews = conn.execute(
        'SELECT * FROM reviews ORDER BY timestamp DESC'
    ).fetchall()
    conn.close()

    is_admin = session.get('is_admin', False)

    return render_template(
        'reviews.html',
        reviews=reviews,
        is_admin=is_admin
    )

@app.route('/submit-review', methods=['POST'])
def submit_review():
    name = request.form.get('review_name')
    text = request.form.get('review_text')
    rating = request.form.get('review_rating')
    if name and text:
        conn = get_db_connection()
        conn.execute('INSERT INTO reviews (client_name, review_text, rating) VALUES (?, ?, ?)', (name, text, rating))
        conn.commit()
        conn.close()
        
    # FIX: Redirect back to the homepage reviews section!
    return redirect(url_for('home') + '#reviews')

@app.route('/delete-review/<int:review_id>', methods=['POST'])
def delete_review(review_id):

    if not session.get('is_admin'):
        return redirect(url_for('home'))

    conn = get_db_connection()
    conn.execute('DELETE FROM reviews WHERE id = ?', (review_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('reviews'))
# ==========================================================
# THE CONSULTATION BOOKING ROUTE
# ==========================================================
@app.route('/contact', methods=['POST'])
def contact():
    # Grab details from the Klift form
    client_name = request.form.get('user_name', 'Unknown')
    client_email = request.form.get('user_email', 'No Email Provided')
    client_phone = request.form.get('user_phone')
    project_type = request.form.get('project_type', 'Not Specified')
    date = request.form.get('preferred_date', 'Not Specified')
    details = request.form.get('project_details', 'No additional details.')

    # Build the Notification Email
    msg = EmailMessage()
    msg['Subject'] = f"New Studio Appointment: {client_name}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = "thevisionthedesignstudioo@gmail.com"
    
    # Allows you to hit 'reply' and respond directly to the client
    msg['Reply-To'] = client_email 

    msg.set_content(f"""
    A new consultation has been booked from the website!
    
    CLIENT DETAILS:
    Name: {client_name}
    Email: {client_email}
    Client Phone: {client_phone}
    Project Type: {project_type}
    Preferred Date: {date}
    
    ADDITIONAL MESSAGE: 
    {details}
    """)

    try:
        # Connect to Gmail and send the email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
            
        # FIX 1: Return a JSON dictionary instead of render_template
        return {"status": "success"}
        
    except Exception as e:
        print(f"\n--- SMTP ERROR --- \n{e}\n------------------\n")
        
        # FIX 2: Return a JSON dictionary instead of render_template
        return {"status": "error"}
# ==========================================================
# CUSTOM 404 ERROR PAGE !!
# ==========================================================
@app.errorhandler(404)
def page_not_found(e):
    # This tells Flask to load our custom luxury 404 page!
    return render_template('404.html'), 404
if __name__ == '__main__':
    with app.app_context():
        # Removed the 'if not os.path.exists' line so it always ensures tables exist!
        init_db()
    app.run()
