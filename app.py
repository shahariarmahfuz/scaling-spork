import os
import uuid
import time
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import dropbox
from threading import Thread

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/temp'
app.config['PROCESSED_FOLDER'] = 'uploads/processed'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

# Dropbox কনফিগারেশন
DROPBOX_ACCESS_TOKEN = 'sl.u.AFlDrQUgeqnIzuVL7Nkz-dXRujOIDPc1F9RKbGEqW19qAcY3XINQXUG11hp_ZA2yFpugTA1fxaTagNBUmbf-4zrHphp0p4Bo5hf-qcSJTEzi9OXp9m6XcQdETSxLz9ml7EwSZRW9ro_SBGNlZ9rlPCb9TF_HCQ_nTuUL3xBy57nDrZgiYyBhV3XFTjrikSeYDxANyF_ou2tBLTVJC1fxfuyLGGgK52hkNhNM_3P1EiR-8kaVRhq-NQz91lk9EvQKqpRONiRBzBRsZo2VdJwXlak_TQC2T1VfK0IMo-9eiGq2j5VUVE9A2VtyGtmyH6tnb4Ds_nsXAcUcpVnqVdCFQigvW1coO5WPoNbFMZ57biq4D3J4iDyW1SVznB7zqS2BkVdln4RacsVlp27OgJxHPgEm72X0Sk2UdTCR8cY-ogu8TU6rl09zU2gkGFlm-RridDsAYTWrxlCmUygRWlhx1vdLHvRW_FQmNZhrkcVHbc4XWcEzVBlQM3WtuSWoMDJXPgf-qoqSVclQjyzfrGXc6JsUZm65bo9H3REjmHh1bdTea-B_c1r_SNsIS4UOj9JYP2V10R8S4HwpN5O3HUC_pn15WMbG_RVM3TzGG-x_fnxSDP5zSuuul_OsAtBrwmNcvLNc29Evd5-yhFMBFdhCUSx4XUH5gkR9kckrTkSvD7tRbiqzzQi4c2JI1XbOMfZCdsc8L0WdjkWA9uPn_iNKHLR3yumivf9kG1Kr_UaSiSspIVRuMAT7d4aLY7DirTR9gN97LSHvVSr9R62wU0MUipZElX6Tkx_AUrsgjhv6vmFLUbrBCb6jgSXB7S3oNNomurVI5xXAwLCYv9kB2KFtkxT-C8wPQwBTmWzogyjpXg7khFJyfRcZIV-pNDsQXvwgch8mJCWERLZGcYZqmVFfYoDMNoYuNNZahBIuTr1z9P7oTgN7BwlpLQTQZXpFxdtjU2lQy1T8YcWFM3l0cyhIBN9Vkvw97Sy5bl2nY8UdxjQ1YYIMIboRU3A-nXEZ6sGpLkDH_SIhpSrZE6Cwgnf_0YMvtEovodJW-AjDDrk0-k2kJ7ro214rl4ir3jshbHBv2dFbHdkjuVvF_9Wxkr2_LhkshU3IGEs5k7OTDJnXNRefIGCPQvKDg0FOYvO_4FikVMXoqeZfLlCpKeNf0XphIQk-xl7BhwBTZlmqwWXhQKaCJ66i2Bxiz4gBZe6xpAsCTsOOBTDgV6N0EiiPogK22ekGzEIhD2HZp-BgDDoqXukbVlgFIR-Vxcg4FKfGvtIxhW8pM3YzAZ6dHmCbdPoG08hX38K6k8P52xDgz9Lz9EX-BmA26BhawtxDmQjaFyilemkAzxPlc4mfbeMC0YogkvODVLCWO7pVW0kcBFGDjpC9JA4qRKX-DjljiGhVitEoz8Vc4SpoR7s0-FtmLFPxnAki1qPCJNTbgxyhEijx6YLtJA'
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
        # ১৫ থেকে ২০ সেকেন্ড অপেক্ষা করুন
        time.sleep(15 + (uuid.uuid4().int % 6))  # Random delay between 15 to 20 seconds
        
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

    # প্রসেসিং শুরু করার আগে ১৫ থেকে ২০ সেকেন্ড অপেক্ষা করুন
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

    # প্রসেসিং শুরু করার আগে ১৫ থেকে ২০ সেকেন্ড অপেক্ষা করুন
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
