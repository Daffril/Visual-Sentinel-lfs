import os
from flask import Flask, render_template, request, redirect, flash
from werkzeug.utils import secure_filename
from flask_cors import CORS
import face_logic, car_logic
import subprocess

app = Flask(__name__, template_folder='templates')
CORS(app)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.secret_key = 'abc126'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'png', 'jpg', 'jpeg'}


def convert_to_h264(input_video_path, output_video_path):
    ffmpeg_command = ['ffmpeg', '-y', '-i', input_video_path, '-c:v', 'h264', output_video_path]
    subprocess.run(ffmpeg_command)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/face_identification', methods=['GET', 'POST'])
def face_identification():
    if request.method == 'POST':
        if 'image1' not in request.files or 'video' not in request.files:
            flash('No file part')
            return redirect(request.url)
        image1 = request.files['image1']
        video = request.files['video']
        if image1.filename == '' or video.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if image1 and allowed_file(image1.filename) and video and allowed_file(video.filename):
            image1_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(image1.filename))
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(video.filename))
            image1.save(image1_path)
            video.save(video_path)
            
            text_result = face_logic.process_video(video_path, image1_path, app.config['UPLOAD_FOLDER'])
            output_video_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename('output_video.mp4'))
            output='static\\uploads\\output.mp4'
            convert_to_h264(output_video_path, output)
            return render_template('face_result.html', result=text_result, img1=image1_path, video=output)
    return render_template('face.html')

@app.route('/number_plate_detection', methods=['GET', 'POST'])
def number_plate_detection():
    if request.method == 'POST':
        if 'video' not in request.files:
            flash('No file part')
            return redirect(request.url)
        video = request.files['video']
        if video.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if video and allowed_file(video.filename):
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(video.filename))
            video.save(video_path)
            
            # Call the main function from car_logic.py to process the video
            car_logic.main(video_path, app.config['UPLOAD_FOLDER'])
            
            # Redirect to a page or render a template to display success message
            return render_template('car_result.html', message="Car detection process completed successfully!")
    return render_template('car.html')

if __name__ == '__main__':
    app.run(debug=True)
