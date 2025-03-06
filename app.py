import os
import uuid
from flask import Flask, render_template, request, send_from_directory
from werkzeug.utils import secure_filename  # শুধুমাত্র secure_filename ব্যবহার করুন
from urllib.parse import quote  # quote ফাংশন যোগ করুন

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/temp'
app.config['PROCESSED_FOLDER'] = 'uploads/processed'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'mp3', 'wav'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def upload_page():
    return render_template('upload.html')

@app.route('/process', methods=['POST'])
def process_files():
    # Check files
    if 'video' not in request.files or 'audio' not in request.files:
        return 'Missing files'
    
    video_file = request.files['video']
    audio_file = request.files['audio']
    
    if video_file.filename == '' or audio_file.filename == '':
        return 'No selected file'
    
    if not (allowed_file(video_file.filename) and allowed_file(audio_file.filename)):
        return 'Invalid file type'

    # Generate unique ID
    unique_id = str(uuid.uuid4())
    
    # Save files
    video_filename = secure_filename(f"{unique_id}_video.{video_file.filename.rsplit('.', 1)[1].lower()}")
    audio_filename = secure_filename(f"{unique_id}_audio.{audio_file.filename.rsplit('.', 1)[1].lower()}")
    output_filename = f"{unique_id}_output.mp4"
    
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
    output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
    
    video_file.save(video_path)
    audio_file.save(audio_path)

    # Merge using FFmpeg
    try:
        os.system(f"ffmpeg -i {video_path} -i {audio_path} -c:v copy -c:a aac {output_path}")
    except Exception as e:
        return f'Error processing files: {str(e)}'

    # Cleanup temp files
    os.remove(video_path)
    os.remove(audio_path)

    return render_template('download.html', filename=output_filename)

@app.route('/download/<filename>')
def download_file(filename):
    encoded_filename = quote(filename)  # urllib.parse.quote ব্যবহার করুন
    return send_from_directory(app.config['PROCESSED_FOLDER'], encoded_filename, as_attachment=True)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)
    app.run(host='0.0.0.0', port=8000)
