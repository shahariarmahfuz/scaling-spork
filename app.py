import os
import uuid
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import dropbox  # Dropbox API যোগ করুন

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/temp'
app.config['PROCESSED_FOLDER'] = 'uploads/processed'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

# Dropbox কনফিগারেশন
DROPBOX_ACCESS_TOKEN = 'sl.u.AFlFOAhpIyjA-H6DJV3MNJATaSNmI7tFt2uRDDCxXR56lrSx5hboI7c0G0-HTLrMzCf2Q5T-9TJ3147AAsURZg-_Q6Pj0a-5-ri0BhhMWerE8qzUDWwrYhWq2pAS0b-s-BXkrXCXIqwgwbvE8udU17h7TfEj-Rp91ivpFAWTQjdMYgzvBsMmREQ1dMLjYNRCCz4sLbJuocjuXsEErUFQTJQmbGTGUpG_HUkhrWd29W-1npkJJIdCmzhgO_V7pKccMjtBr0PtJHOilMxOGnbSL4MqOLh2sZHKNxHLbuSG6Qy4rdllekjhCW4Euxx1o7vd3tZwEIKEzcfgN9Jm5_Ih1NjO8JVzTCsq0a8MDHNeGEcxU8-Jv26cW7g2Qzt1YUVzGWIwTfTuz36S8oz1o7qHFi0ycTp76gDm8aOtAYr3uQi-wjNx9dZTATbSGzGrHEYWWKiDjVecFY9AZKAH844Kv6KaE9ME5bNTS4czJyLnMuSbeht1ozcnkO9bJKgbeEMKy4te-DwpHzu0ea8CxipIQjehq08FhCYzSVvV53rQo2dZ2_T-N9fzJmKgy0xc5LFDy1Sc2uJBSZZ3Z1zg5asL3HS5Z6D7sm8nxD4oBhB4xO6emlnWR4s0twBmgVtfiGZD21wSJnnY999Jp0qMb3Us5mKAMo0HFt3mgpYppGtWOr88mUVNyRGGOjy1JG42jQuL4dycVQN4lcsk4sAopoAxLWt4ZR7IHgSc_-6ubbFAUMl9yVbjF3nK6EyrTAAp_rVL5tLjbGSj7kjEfO7-4q7xR8R5PHcsjn4jp1TtofW6Ccqox3JOjjnAbH-kPKin4j7YifCRx_RPkFT4naxV_mgrrRZ7Yh1cJ-wcHlPNsbu0HfKcMilMQLcGQHkRQYAg-VDYTWPQhPrPsNfv17ZSfffDbxVruiYWKajDmNKlmwcPAALbgz0cCWKW_yEFYF421jnkDJFRP5OrLcbAYCvowif51nsMTOyS9fPR2CItpAvuYVc8ZSgTQeHIuS_uLE4O4OKyv0a20mp_VuQFcjnXrq4R5RUzj9ciVQGmVF-AgxCXzvVDThnQXb8O2tLFEIjaP22XNyoBMepUpeCF-m2lQHzPrOMnH10FtqwqierucCNwdJc_PZVCMPA9SpX1SAuEOPhLrkpXQNIp5T18httR_fyERFlQB_y32Doqm0G2Mb0LNBxFg1d0ICNfciYd2ky7P7q3DpjFt8NWlw62zENDPbKdG6kJZSfXtRo4gjFOH8WKR6F8f0pPZZmpqpkMBs26aamslDU48UzIQIW-wEs5D3LKpulkO-OenVQbGiFzLr5uQyfWosLyGBLVPLQVjxra46VZgLBMuaBbqW0I9S44kGNsMzVJihnUKnJc9JK4uSBSmP1OKQvKDF25_L7MlyhBeybl0MDxEASF29JI_g8xTRAGzMcrfCz4VMV0iGdRsslMAGQl9Q'
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

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

@app.route('/')
def upload_page():
    return render_template('upload.html')

@app.route('/process', methods=['POST'])
def process_files():
    # Check if the video file is uploaded
    if 'video' not in request.files:
        return 'No video file uploaded'
    
    video_file = request.files['video']
    
    if video_file.filename == '':
        return 'No selected file'
    
    if not allowed_file(video_file.filename):
        return 'Invalid file type'

    # Generate unique ID
    unique_id = str(uuid.uuid4())
    
    # Save the uploaded video file
    video_filename = secure_filename(f"{unique_id}_video.{video_file.filename.rsplit('.', 1)[1].lower()}")
    output_filename = f"{unique_id}_output.mp4"
    
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
    output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
    
    video_file.save(video_path)

    # Process the video using FFmpeg
    try:
        # Merge all audio tracks into one and combine with the video
        os.system(f"ffmpeg -i {video_path} -c:v copy -map 0:v:0 -map 0:a -c:a aac {output_path}")
        
        # Dropbox তে আপলোড করুন
        download_url = upload_to_dropbox(output_path, output_filename)
        
        # টেম্প ফাইল ডিলিট করুন
        os.remove(video_path)
        os.remove(output_path)

        return render_template('download.html', download_url=download_url)
    except Exception as e:
        return f'Error processing video: {str(e)}'

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)
    app.run(host='0.0.0.0', port=8000)
