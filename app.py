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
DROPBOX_ACCESS_TOKEN = 'sl.u.AFkWg7aLa4ytcLhDZHWtcbP-EDNmXgtSb15xaS28NTutJTmCoI5nzZAxZWGiFFzB81WeiPNEHAj6OBvajJF_ghkjEwCxzWnZQSszxROT-cH7sn481HTX3myKV1gb0TeXUo2FFj2USM26BIiHwzcY6GtYMqAAbcvP85Rkz8JqYToCFDzv2MdUttgtgVEbVyag0JKviFYyWTgynXvbb-S-iCD5fyg6jP7e5_bwDtTtScOhPCCDJ9vJdKSsN9jcXvId8CBe_dTf14VhjYHfTc1Dz5C8BP3DZSUtKeOhy4Px-Hf40-LSQA9hLky4Mop7q7--8c30M09cDJjQhEAXWuXTv6jqvLK9ztYcMHYSXCVIokgxMqge8oHXwK7dHqOhylnZSsVI_GdDlviuD2M1P4gZjnYjYgpnYjewxYiH-UP6IbsjQLz7DKMcG2p3cChHlC67m3iKa9Y0susd8Vr1NIiYZH2rXU-EVNlYd1CWNdWCtMrEsb-64bMgCtQgTFkmuonXqQzfVuVOzSg32SSW2evZ6jzrwFYB3O8aql0dra23gtCrgbWUUyiLYjW1KiQsoGisSC5g0f6lXxS3lH_XDc3sDmTE6silicoJMSaAPgR2c1XkghE63OOkPrmb0tGaaOMRyvsNcv4niiEmUZbAPGyP7rAWBrEgnZK3bjSxjny11P_8FWNnfnF470z_Cl4IoIypHH0TYTPYCJuqG-eQvI9QZ6EyfwwJT6MkkOjB2OWefdFcP5p-5x742Q_inE_R3ySmfRCAAqK5z9EejpVKVtyeTzkdjQAFGC7lLtB4GstGFgmBouHE5k3hm___zWWXCILaQvr1IVwjVQumNPPQ5XYdqcrPhITmcy8hKBtp-CJ-kiTRNCFH_Px29XelhFmTxV4AeOzOBsgE_FR-C8YoYgb4UREkNnTlgNa-vmaIs4c2J0M4hdx-w9_AqwXsjxlvcSN2PDzAbNzkVCu6dEDj3z5igZsWY0qA8GsxJiW0ko-s_k0KKXGiTUSPw8ey4f9URg43nNYYEgOSAeNyFuWWJ-XGq_t0QT3xPpTygY53HyTc4YwFNoHx08l_UkNzUwZHYabL9PO3vFeN5anvY9qij-k66TaM6OKOACpePZ6-8JJlprFwQXlziQ2ETH5BRRRQluySbTS3bU5MnFU914zXFtUHWwZLGasA33YIYZmI2LpdMwi9qK4t5647MS2jOgj8et-mgsbS5z5AkxCTqkjbL6BHs2jFyy7StBnZJ0wtVYyp36i9zjrI5tiT0_-bZuxTyFcsyZOq9eiJ0Uhru6BXwV-EK7F8cHcjnTxHBX_dftsObkhqyY5MSf5U3quqZ6fasZxjQINCYC66hrPdCLeByhyujiuFUfqrN3Etuw9g-czir7qiNrYPl1i6HHHDMcvCupJXRmhzLKovc_gK51uF3Xp7tHExaxs1P14woYhs_UkyHqTfWQ'
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
