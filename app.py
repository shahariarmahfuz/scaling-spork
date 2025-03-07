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
DROPBOX_ACCESS_TOKEN = 'sl.u.AFlSngf8RvUpbcEF714Ceo-tXD5hcCeOD68lQ_YRvmdiZlhBUUf4mGrGeto7YHbQhGPS2gxOjh0k_Biwg5L9dOauLYbYQNujYL9QEggL62SM3eU6TNLd3ftm2P6KZrk3tqtVe37Ep5hjFB4Gu2_HPsmh-blOBT_SL-wws1dLfqHlbg-FKAM6Y3iUvUHA-CuwgzEj2WnUGWl1e6B2AwvNUSndJGtLOKtSmAUgbFjy0tbOKMNNId1nWz3eCpJDv7Si-HBN10b57S5Pauu0lPa3wlaxy7jR-JhTTNqpA0ZIvIfoZsdMJwUeaAuxQJoKmX9HK-19RGPiRM0BIMJ_F7hhBnGIaAWO9MqenEQUZO8J7k8T7jhsrVKsR-5NLboTrrPuROZHhZn8NPuIiBOBZEzygL7nlVPRx_zIgRu9cQQB0TQImADHOKBK6HCg8ZTNheEEAHqwEyA-s6-_Kw2Mf2gVFD8kxS3kBRMdVDSW-qKLUjgwFK0IeDk3ObO0fpyeuaRAc0YA52nmscvAEXX7W5QnaCdlDkwclKWc5cUMwgTN3LNASgcPBEVaxtmk-FMTCZ_JOa6lwF3r7GS0toyoDDlSZTLTvCJfrcBca9gXMnlMIgR9KFIBGAl0N7CM9v7O_dcB2zTymcNUTaTvxp1ybZQiwi6CB433LGKg6Yp_b4JslOQpIa19owF-_fJ_rtm2_YLzSBvC6_82qFfiuQpWSAak3PilA71HR89W-n8Yo5roEq_6BfdBtofxzVSj_CKlprQxsorucYaKOSMUMlQRuV8zkP7pXadwtR_UgWhujrdAhTNI80ClmlC2GVt8AANxd19evCDR3OXWef-XHb5wOMXaZzmKoZnbQrCKzMpw3np_T9RlH96vqBWn7V1YJYYofMtuwgRddTQvB6bIwas_JPJ2QOAVEe-JkgLvuc1VLxkyAX_f3GbMtGYYESozt1c892MQl6ftq_aPHm1h5PSYLRV5C5TiVFEizN93FQDts9my0kMc6AsiNCzFMBI8leg0DQ6aQV3qWq2picjMT9oQefshipRN9u6YvHpuT9siSIJPqPe3FJlBw4HLUYVPaxsdDe91m5MymD2ScN1Q9s-F0GMMFuItlRt6rfuCes4HXYGbggVQV0Ljw-j0ZdYvMt4pT2iVOqEmdudL7ARDJ_i--E8C6TbrXV2AwueTMBe9f0bMWYBgtYUjU5YGK21Kxa6JRP2W3ARMwQ905uKZu6_jiwVhskS7v3siek_001hg0dNTtBr7rvO91NxUjFWhcTLCOnp0NFOmPreVTkRWS8hYlJ0YOQ04GXFzTmBSmUeYqgK04_lpad9dRY4NSuHPERkPeT7HZZVTyYp1Ym2bmjs4K4eOjQyinJlj8l1DWoSr_p4B2YeVyCRWzXtbgznE7CErhRIGDbFUlctU1wBoeDtnAhUqzGQPJ94gXMAVUAE_Xy9Vxr467Q'
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
