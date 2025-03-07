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
DROPBOX_ACCESS_TOKEN = 'sl.u.AFmNnG1PmSrCL-VxHMNOVrHoUkKI1431RXsLN-Z7ZIkq70VpW3HAclty7TSEawyCPSXb_s5X8MDEzKE4GuA0lCdKIMHMeaaRn9OVWtNtP7t00yVm8qm-0W3sNKwHY8zZy7qQTAewFoQZW0iTswheX4-8Cl8ZoNbUrlftuPCtEeneTn1_v20hYdD9ic8lePF3XFkmBCP9os6sJM6CfA2o-AQ7PrMdqhDO6OcJtSvQE603IfDSVPP3JWhYxwuEgnUdDNAoY9DbKvSFDZ0woVKlGDQwDvr6nbsW-45sXHGwLaCzPVG1KBzRomv5ji-numIzzrnx3OiEzJ-1yeDyP4Qzvi4tsaQEEqMHKYi9GNAaze-OpF4uWTc_-paHg_RqsBP9x8R2ontvVIsK3lTikyw6YX7J-2iPWXoUL2SrSatIjxLNsSJxOXB41Ibw3mMoSWFLbUkT5v2xKDsqBJFPR_gZWLIXkAYvCbkGILaibFf9lPD_XVIz9FKvoMuPNhMXNmqifiCU8B4flQUTT96OXkKAeXtkZ6OOaQ-ilI3iwdZu0z40xt6Qhr3MeV7xvDxoAcdtF1tsNB8Ml9sew7erBNB4tNWa1d3diSHRUvCqXvqrK_D-C78-UOqHAg7yhobYs6xZDKTKXbRt7v9gh-aY33hhTUuJagtrf4G5Va7fINothH8cOqEi2IyWnbyAGrMliRDf-WNW0-UhtGaETyfmrtPsVvxEYyRRzp_naEZe6Tehr6CVMyzOhlM4tRrMBZ-eDJX43z__K22Nc27_bnUio94uKqNFYByhEz5MdY94ANARmFQURjtjXZXWu5Vj8jjncdmtkTtSY0KyCvIToUdjV2rTAOHZlxJFJe-LGvNDqt3WMwpmBN-7mPtSaYWFhZvCy1NGkOVYmrKQEq2W3i5YWkB72XJ8m0S5CWKCTdy7weWsEj8irYh3wKDB1h4vEflz-JoWRn8VvmWnzH30mmVpQHvsIHQL5deKFGwKVAjOR31fSMNpDqoy5RpiqwVqRfp8rZDLV_Y4p86LWLcDPbhsEiH3PTVla-Xgynr48CjP_y2PHtng8sXkLT7tG3obw6-7OOJkHaGL2-w5Cfjmz65WHZ_eqxIXAZf8TddBHSS66JCAgD9xJz1ZXbqsVHMu8MxgOqpG4gqgPlcELwH_mpQ5JZ71-kvMaEvOaoaj4KO0exEWRMC6Xhtxa-ZpIK5H-zJ8g5FIcFVm-NUaPj8msoDuMl8efwBtBZMm7xFeXd-F8ymA7KypK7ck-5_k1W_Js16ycumh_zYncQnZZPHtZ6mre2Zge8Y3LfnbWGyijZw6lyp8BufbpLA-Pu0dlcH1asehdvqX5nIWcNX7GhMn341CKad4AgBIXYQA_f1ZeINut-CW-KOBZ_YwFd6JrrXCz9rvn8ZIF9GahXTb-UfQfRMW3lQKO8Y3KR-CqBN18L75jYFocVsAyg'
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
