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
DROPBOX_ACCESS_TOKEN = 'sl.u.AFlIETpeJDrPqME7RkZonbusQlZkzoTrCBiSdYF6duSyBcF2HUdWuC16qqcaR2TzGuCnswfUqwfX0MCqLCrBXxwZbIwNI_aEeKoX4bK9oVPRWl4zFAY89HEQiPumlpioJhPdg-93olNzZxo9oCd5QsOPZD-vGGZ_PNKJje002EZO7_MY8xq_MF0_hct3-BufAuBJpQmAghYNRymd6SKXn2_kU7PumyLK-xt1PvetUSxIzrAAfq8DG1uxC-3Aj2Ms2-Qkjac5jseM5CpMi2RYTKsY0BZoLBYWAj8oCXYLnnGTJE1csE2fe4-4dac_niOwMBmtLeFqEebaBOr3oqffpLFbSMPtJXqSXfe2B6Sn-rqIH2UVno6XDDRMzU_qD6P0nyYuQmEyK_FvhGbT1bDAx26q6hOzxLBblJg1QTk1LHpNasBeywG61vv1keFrgGqY5Qgxe2KRHe-zMm4SC25Dy4Gnwmd-DZQYsMXWxut55lstg-hFFwW509luDc-884Uxq99Kfl_-Z3HJi6-33krZjytSdiUGwVFUcs2qaDmd1pMO-xDryYFPQ_dEmRHJW-G_nSZuIfvKhQyEEB4zJ1WB-uoUFmFQndeIkrNm260UTEZtkNeZAK6My2qZ7RfiiH0WIWl6HtEJwL3PaG3QKlsCwh9Rn1RQ11Eqx4b1qkUSdCoQD3Z-EwuAU-J-FRFiOsanSil09zpEDd-bb_oSMYEceLe0ckKO2eSQWRWi5sked9pGvc6TkjL8SPecEIqJwR8nSGOJG0c8Nw4jVrfToPCBYYLRMmhwTyhHpao67T7e4PZSIE2R2H0YHnRZ5E3c2KNz_Ig7SwKOunXDXeNFOZGOEPwcMkUs9VMCWuT85M7Hov2GRCxv2jub4h9c3QQqLxvndF1aj-NcxaD2TrSt8K5Edv440dsKqTY1zHX1FSmpt8ypMHOmCc8Z2CAINec4moz1W2jP9_nZ_6nmMUJnI0wb5XSDq_2Z7x90BpfiFajvtdP1RH-Ibwx1dhuqDumYyTIHXjECKLuUkl6oCviJvk13JrwY7KNoi0zW5kdhukAKakE7WZnC3ERYvQph-h1-mSxcjCcT86iD2Bvqw016yWp7Z08WCa7v5SkDB9ue97vtPzN7tZm6ev66WPf_W3jya6CUs7r7Csa3rJj9PU1Atb63gscZ4ne5VRn9Dv79Kdm_1q-tkWaZ_jzxFQ2ieJ26GRrd-bwTcurpDiDAsq1S5_DDQj4jTtHNOrHBUMKq85GoQmlRLH9hail2oqhhu4EXK-L5pqgWYuzxwubFu26uPaHVdmHBLrk22hul51BFtz9BLdtSqmL4DH_GcBwmLv6Bo0ShaXYJgJHzf0_1Z7rXGSLBg0hjI3O7X6sJPl6TqwR_N86G_-B0W5jqNQcJ_VBNxrHrA6vauX8j8ubWLhKW5UUYIPDFAv07Ps6wSr5ZCymmA3p0OQ'
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
