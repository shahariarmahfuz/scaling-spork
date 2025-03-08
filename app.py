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
DROPBOX_ACCESS_TOKEN = 'sl.u.AFlFqC6QFIJIPwDY4qsCjqzrVovmq7qaf2ACRGRe-1ZCTPS-DrNO32XIhlYsk0TR7TmFnFg90ow7gBtSdnAsJ1XR9RQgK38HU_WI2VhfkFcaGirpLKEkie-3ic14LXxvzh4jy_wtnrsUMhql2FANBagepoHlAG_mbcTBvxlhN_KS1L3sX-4SHkDg3JxNmVcx4TD6BIbNs9E7rv75sINTciIkPunBqBDdrb804zqFwCsEHYq6RV4q09p_Pg3DTVvkhzweLVGHUxVZa3G3RkfW2hWq4CI4tFtzF7uCSAm67cD6oVvKjoF6wf4GN65AgVaGAr3UtoI5AH1zPgrZdO4h0_EmpeRbB2FC1daw0wwO0xQ4b_3n2HvX1ErOliR1p_HJ9AD3E4rNZvQmHWftU3UNNwbYJTyd2fmh0iAfSJqY0nTRYmym17iZVCxZ3KiVsoRMcsF0zCs_ZpihP5zexRBx2ZpBDyZKLhTRi3v8mnKi0HJgazVtF6fWcwMzKSaTuvw95elZpEJzso2A_yj-kh5K3qLmMdGymmPNArzs0GjDFWT5pY_ZH-qAkmf3EWnwds1qaKomvuoaqgmQjdg0tL_Gn_-uqhyKTmu8jimo1hOsNhv0GXMdYmUfMezgLeH4fmMQplCG2B4QGsAoWOUXRaClzwI0dHBP4NyCpn3I0xTUq4F_ZPyiycBCy6dwpMy2I_jPtM7gx1prYAdNobB8g1ggueVv4TAH16yWO_uZkeQRpPoX5QGzF9qAz2iNMXhmyldhBkN3EVOUtxfxmdpKIuAQdbct1PZY3rm2dYC18JutyuTGiJK2UCqkdjtIXp17vxeJ7hMEKXuA3nSDOk_D0pKFCxN16xGpzkQN7B8CH0gteTm1L0MuuGWzNCAm_WSp67idxtfplBsKZiusEItNOuVnb6cIf8T5lpJ_NuAUFYCo3XiW86asMS_86z9nBwh8Sesph9MVUVmE5KoE9CxBbA8pSYgBrOJ5cZUdKNkNXTrxlzdXYMnpWSAS-b55sl0N1pIJnhzv60X6S7pYur4PPBnxdDg6Dt3ra_Y-nlt7pB0Sbv0XuwGZgLdPrndTfQpy1rLgdm6XM_oxvMakDyqCasrdLdjn1pNx8Dy3Hbl3EVru0HUpMeS4png8DiiqIvz_SKiwfVwaE-en9_PB0a7QOXiGklRJFP_xFPsd4MTzK4mURGwJIqM_NyvGoXvihCB7mqDQoHBuTzfY7QMPyofrLaw1BZzgCNaUyZTITtoceVhTn08VTGRCRgo-Jskgvk3papTafIHd6lNVopFg2v_3D8v2gZraROfc4Yu4ChlsgYpkQz-6s474iELWvdi-_Q9JKME9DDHXntCdUAxy3WaWwayopSb0P1Apepftu-pZq05IMGm_eD7-nH7Bj__DDZOa-LyDMwTo9uJ51cnwpyc7dPW_ZXHXDBj4ZoCEllrws_xxO1bOSQ'
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
