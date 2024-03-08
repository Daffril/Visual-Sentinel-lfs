import os
from flask import Flask, render_template, request, redirect, flash, abort
from werkzeug.utils import secure_filename
import firebase_admin
import datetime
from firebase_admin import credentials, storage
import face_logic

cred = credentials.Certificate('C:\\Users\\LENOVO\\OneDrive\\Desktop\\Visual-Sentinel-main\\video\\visual-sentinel-firebase-adminsdk-nsw54-ff364f6cae.json')
firebase_admin.initialize_app(cred, {
    'storageBucket': 'visual-sentinel.appspot.com'
})

app = Flask(__name__, template_folder='templates')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'png', 'jpg', 'jpeg'}
app.secret_key = '08051613dc'
bucket = storage.bucket()

# Define function to download file from Firebase Storage
def download_from_firebase(destination, local_file_path):
    blob = bucket.blob(destination)
    blob.download_to_filename(local_file_path)

# Define function to check if file has allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Define function to upload file to Firebase Storage
def upload_to_firebase(file_path, destination):
    blob = bucket.blob(destination)
    blob.upload_from_filename(file_path)

# Define function to upload output video to Firebase Storage
def upload_output_video_to_firebase(video_path, destination):
    blob = bucket.blob(destination)
    blob.upload_from_filename(video_path)

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/face_identification', methods=['GET', 'POST'])
def face_identification():
    if request.method == 'POST':
        if 'image1' not in request.files or 'image2' not in request.files or 'video' not in request.files:
            flash('No file part')
            return redirect(request.url)
        image1 = request.files['image1']
        image2 = request.files['image2']
        video = request.files['video']
        if image1.filename == '' or image2.filename == '' or video.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if image1 and allowed_file(image1.filename) and image2 and allowed_file(image2.filename) and video and allowed_file(video.filename):
            image1_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(image1.filename))
            image2_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(image2.filename))
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(video.filename))
            image1.save(image1_path)
            image2.save(image2_path)
            video.save(video_path)
            # Upload files to Firebase Storage
            upload_to_firebase(image1_path, 'images/' + image1.filename)
            upload_to_firebase(image2_path, 'images/' + image2.filename)
            upload_to_firebase(video_path, 'videos/' + video.filename)
            # Process video and retrieve results
            video_result, text_result = face_logic.process_video(video_path, image1_path, image2_path, app.config['UPLOAD_FOLDER'])
            # Upload output video to Firebase Storage
            output_video_path = os.path.join(app.config['UPLOAD_FOLDER'], 'output_videeeo.mp4')
            upload_output_video_to_firebase(output_video_path, 'output_videos/' + 'output_videeeo.mp4')
            
            # Generate signed URLs for images and videos
            image1_url = generate_signed_url('images/' + image1.filename)
            image2_url = generate_signed_url('images/' + image2.filename)
            return render_template('face_result1.html', result=text_result, img1=image1_url, img2=image2_url, video=output_video_path)
    return render_template('face.html')

def generate_signed_url(file_path):
    blob = bucket.blob(file_path)
    return blob.generate_signed_url(expiration=datetime.timedelta(hours=1))  # URL expires in 1 hour

    
@app.route('/number_plate_detection', methods=['GET', 'POST'])
def number_plate_detection():
    if request.method == 'POST':
        # Handle the uploaded video for number plate detection
        # You can add your processing logic here
        return render_template('car.html', upload_success=True)
    return render_template('car.html', upload_success=False)

if __name__ == '__main__':
    app.run(debug=True)
