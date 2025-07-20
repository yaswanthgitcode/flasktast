from flask import Flask, render_template, request, redirect, url_for, session
import firebase_admin
from firebase_admin import credentials, firestore
import pyrebase
import os
from werkzeug.utils import secure_filename


from supabase import create_client

SUPABASE_URL = "https://rdcrbkqqcqwpkegczrch.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJkY3Jia3FxY3F3cGtlZ2N6cmNoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzAxNjg5NywiZXhwIjoyMDY4NTkyODk3fQ.jsvyURQz1axGfJPo6Bx0MrL7eDh7_VjTwYzVH9_CdzA"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
app.secret_key = 'my_secret_key_123'

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Firebase Web SDK config
firebase_config = {
    "apiKey": "AIzaSyAVnTRKIbB-dkZzGPjFtFNRXCrjolCDyYg",
    "authDomain": "flask-test-12b9d.firebaseapp.com",
    "projectId":  "flask-test-12b9d",
    "storageBucket": "flask-test-12b9d.firebasestorage.app",
    "messagingSenderId": "885068989186",
    "appId": "1:885068989186:web:7cd2992b1bda102e54f81b",
    "databaseURL": ""
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.route('/')
def home():
    return redirect('/login')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        try:
            auth.create_user_with_email_and_password(email, password)
            db.collection('users').document(email).set({
                'email': email,
                'name': name,
                'role': role,
                'image': 'https://via.placeholder.com/150'
            })
            session['email'] = email
            session['role'] = role
            session['name'] = name
            return redirect('/student/dashboard' if role == 'student' else '/faculty/dashboard')
        except Exception as e:
            return f"Signup error: {e}"
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            auth.sign_in_with_email_and_password(email, password)
            user_data = db.collection('users').document(email).get().to_dict()
            session['email'] = user_data['email']
            session['role'] = user_data['role']
            session['name'] = user_data['name']
            return redirect('/student/dashboard' if user_data['role'] == 'student' else '/faculty/dashboard')
        except Exception as e:
            return f"Login error: {e}"
    return render_template('login.html')

from datetime import datetime

@app.route('/student/dashboard', methods=['GET', 'POST'])
def student_dashboard():
    if not session.get('email'):
        return redirect('/login')
    email = session.get('email')

    if request.method == 'POST':
        file = request.files['profile_image']
        if file:
            filename = f"{email.replace('@', '_')}_{datetime.now().timestamp()}.jpg"
            file_bytes = file.read()

            # Upload to Supabase
            supabase.storage.from_('student-images').upload(filename, file_bytes)
            public_url = f"{SUPABASE_URL}/storage/v1/object/public/student-images/{filename}"

            # Save URL to Firestore
            db.collection('users').document(email).update({'image': public_url})
            session['image'] = public_url

    user_doc = db.collection('users').document(email).get().to_dict()
    session['image'] = user_doc.get('image', 'https://via.placeholder.com/150')
    marks_docs = db.collection('marks').document(email).collection('subjects').stream()
    marks = [doc.to_dict() for doc in marks_docs]
    return render_template('student_dashboard.html', email=email, name=session.get('name'), image=session.get('image'), marks=marks)


@app.route('/faculty/dashboard')
def faculty_dashboard():
    if not session.get('email'):
        return redirect('/login')
    student_docs = db.collection('users').where('role', '==', 'student').stream()
    students = [doc.to_dict() for doc in student_docs]
    return render_template('faculty_dashboard.html', email=session.get('email'), students=students)

@app.route('/upload_marks', methods=['POST'])
def upload_marks():
    student_email = request.form['student_email']
    subject = request.form['subject']
    marks = request.form['marks']
    try:
        db.collection('marks').document(student_email).collection('subjects').add({
            'subject': subject,
            'marks': marks
        })
        print("✅ Marks uploaded for:", student_email)
    except Exception as e:
        print("❌ Firebase Error:", e)
    return redirect('/faculty/dashboard')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
