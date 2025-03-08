import os
import uuid
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import dropbox
from threading import Thread

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/temp'
app.config['PROCESSED_FOLDER'] = 'uploads/processed'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

# Dropbox কনফিগারেশন
DROPBOX_ACCESS_TOKEN = 'sl.u.AFm_9w_eiKTRbY2pjU0V39SOfdmriwgqy7tjE9daVTk6U-laPJ-5vebnmC4-eJ6zmXbd4hjSE2fefLPOw1IFosNbyMTPi5iQ8-VM8AWHT2aucFnLxdowHjyCixw37-Ln-Z6s5-JdwMTUDaMTuRRVKuQb9l1ZwaXI-nPTVT1-4qZb3mkcaIq0BGIEahvJUuL35vSZYc8K2Hoofq8tu39bynfHZmZ2szzNOMNrie2dyL3nCPAWcglUEJLW_klM_Pbd7vNlE9zfMxM4zkHwaPN30Bbeo963T8sbUK0ktHmGcEm1lIcpo43FsL2pWkyqZuvekMArMAes2Ol2Jn2PsGVdD_VA_Ke_I8jFDZBYOM6LDlTHN2KvfL3i2oF7hVCVPWwDIYzW-8p4jnrHYE69oRP0fH789q3kUbtXkybwkgL7KPRQpsAnXqa83yJH7Fho6H0BDlUj7h4YRxbLS23D4NNN56ef-luM527kUAoaHbWaoc8dXAl-OXlFLIIUVupNiCYticDVeU6h_Z_SNlEYP1vwwGLa6c0ZFI295ft_CPDgMdE4MmRicuRIW1_nlg-8pCVu32BH-HJKnw_EJeG3OmH72KUuIqetP3_n7h5h-mwE32mzgKQt1VjWatB9-jcLFKOM0WprGdxo9fS3nAaY6NnXbUbK9m4QeCDzBduXT9uSCtkrtc6DlQ7wsCp7mjTBxuWPRHohBxsZeg26uYBXSIa9mLlZGpcFstRuj83G5wxc690Ohn16YG_jI4uOQ4Le4J6xjd1SU7R7Rb4HrXcCoCwpyc5l0V_yR3ILjiVFNBySatlXI3MjJ6VH9MtaXgSEDmLQAGwYMMiGC4dBdmpDG_EDxMR_aF2lI3LUwW5S1GbTkl8vlMrAkcJelkpYTWR2NKoRM6RXtm4nOu_80OJEnPU5hHmdpU-39queXjphoNhHamJFE-z8kns3Al0J5UOcmyjtLNfmTWzFWa1yKNdknTp9bX4o6KM4wYK3-5BB1Yo5AGI4gYlxhOz9h9Fj67AfImUCYKMMIUSffwrKvrLLr34EGtXnK5Gs8XOt1f0crNrjY--3_uzPzFU1kfSP15OCVCpNxyVgpJCuybKiuXXwKKL6Oto4ZEItoSDWIYQapLSnUIsAku2EbglFe7pZpAlotl9y1jAnPYNKz3iIYKrNF42wPBrHPYgtvYdbzlQ5NRSVC3KyJSk4jLp3Gx2NePNm-RIgU5qAdOQFtlqCA0bT9CZSGyoZyW0rXIb_rwC3y1IQBSCyrmQalkT93XNeDDNSOoypquUAID4xZHarO2IoWf1AQOj3sn25PLnbpuzmkm4-z59whAXo7uF_I72GsbDxZ5cOrBQlGxBC0mARMqRlqucFNnXqbXCeh431yC3XzlyY-67torj0J2LHxkktwrIqD14RmwOK8qgJy4_HscpqHmrkEyfsMLOpGwo7axPSjn6P6oLnxg'
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# ফোল্ডার তৈরি করুন
os.makedirs("results", exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_to_dropbox(file_path, file_name):
    try:
        with open(file_path, "rb") as f:
            dbx.files_upload(f.read(), f"/{file_name}", mode=dropbox.files.WriteMode("overwrite"))
        # শেয়ারেবল লিংক তৈরি করুন
        shared_link = dbx.sharing_create_shared_link(f"/{file_name}")
        return shared_link.url
    except Exception as e:
        return f"Error uploading to Dropbox: {str(e)}"

def process_video_background(video_path, output_path, output_filename):
    try:
        # ভিডিও থেকে অডিও আলাদা করুন
        audio_path = os.path.join(app.config['PROCESSED_FOLDER'], f"audio_{uuid.uuid4()}.mp3")
        os.system(f"ffmpeg -i {video_path} -q:a 0 -map a {audio_path}")
        
        # ভিডিও এবং অডিও মার্জ করুন
        os.system(f"ffmpeg -i {video_path} -i {audio_path} -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 {output_path}")
        
        # Dropbox তে আপলোড করুন
        download_url = upload_to_dropbox(output_path, output_filename)
        
        # টেম্প ফাইল ডিলিট করুন
        os.remove(video_path)
        os.remove(audio_path)
        os.remove(output_path)

        # ফলাফল results ফোল্ডারে সংরক্ষণ করুন
        with open(f"results/{output_filename}.txt", "w") as f:
            f.write(download_url)
    except Exception as e:
        with open(f"results/{output_filename}.txt", "w") as f:
            f.write(f"Error: {str(e)}")

@app.route('/')
def upload_page():
    return render_template('upload.html')

@app.route('/process', methods=['POST'])
def process_files():
    if 'video' not in request.files:
        return 'No video file uploaded'
    
    video_file = request.files['video']
    
    if video_file.filename == '':
        return 'No selected file'
    
    if not allowed_file(video_file.filename):
        return 'Invalid file type'

    unique_id = str(uuid.uuid4())
    video_filename = secure_filename(f"{unique_id}_video.{video_file.filename.rsplit('.', 1)[1].lower()}")
    output_filename = f"{unique_id}_output.mp4"
    
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
    output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
    
    video_file.save(video_path)

    Thread(target=process_video_background, args=(video_path, output_path, output_filename)).start()

    return render_template('processing.html', process_id=output_filename)

@app.route('/up', methods=['POST'])
def handle_up():
    if 'video' not in request.files:
        return jsonify({'status': 'error', 'message': 'No video file'}), 400
    
    video_file = request.files['video']
    
    if video_file.filename == '':
        return jsonify({'status': 'error', 'message': 'Empty filename'}), 400
    
    if not allowed_file(video_file.filename):
        return jsonify({'status': 'error', 'message': 'Invalid file type'}), 400

    unique_id = str(uuid.uuid4())
    video_ext = video_file.filename.rsplit('.', 1)[1].lower()
    video_filename = f"{unique_id}_video.{video_ext}"
    output_filename = f"{unique_id}_output.mp4"

    video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
    output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
    
    video_file.save(video_path)

    Thread(target=process_video_background, args=(video_path, output_path, output_filename)).start()

    return jsonify({
        'status': 'processing',
        'process_id': output_filename,
        'check_url': f'/check_status/{output_filename}'
    }), 202

@app.route('/check_status/<process_id>')
def check_status(process_id):
    try:
        with open(f"results/{process_id}.txt", "r") as f:
            result = f.read()
        
        if request.headers.get('Accept') == 'application/json':
            if result.startswith("Error:"):
                return jsonify({'status': 'error', 'message': result}), 400
            else:
                return jsonify({'status': 'success', 'url': result})
        else:
            if result.startswith("Error:"):
                return result
            else:
                return render_template('download.html', download_url=result)
                
    except FileNotFoundError:
        if request.headers.get('Accept') == 'application/json':
            return jsonify({'status': 'processing'}), 202
        else:
            return "Processing in progress..."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
