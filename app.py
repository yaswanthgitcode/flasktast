import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred)

db = firestore.client()


from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        # Here we store in session (Firebase later)
        session['email'] = email
        session['role'] = role
        if role == 'student':
            return redirect(url_for('student_dashboard'))
        else:
            return redirect(url_for('faculty_dashboard'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # For now, just simulate login (use Firebase later)
        session['email'] = email
        role = request.form['role']
        session['role'] = role
        if role == 'student':
            return redirect(url_for('student_dashboard'))
        else:
            return redirect(url_for('faculty_dashboard'))
    return render_template('login.html')

@app.route('/student/dashboard')
def student_dashboard():
    return render_template('student_dashboard.html', email=session.get('email'))

@app.route('/faculty/dashboard')
def faculty_dashboard():
    return render_template('faculty_dashboard.html', email=session.get('email'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)


@app.route('/upload_marks', methods=['POST'])
def upload_marks():
    email = request.form['student_email']
    subject = request.form['subject']
    marks = request.form['marks']
    
    data = {
        'subject': subject,
        'marks': marks
    }

    # Save to Firestore under a collection for each student
    db.collection('marks').document(email).collection('subjects').add(data)

    return redirect('/faculty/dashboard')
