# Python বেস ইমেজ ব্যবহার করুন
FROM python:3.9-slim

# ওয়ার্কডিরেক্টরি সেট করুন
WORKDIR /app

# প্রয়োজনীয় প্যাকেজ ইনস্টল করুন
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt কপি করুন এবং প্যাকেজ ইনস্টল করুন
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# অ্যাপ্লিকেশন ফাইল কপি করুন
COPY . .

# ফোল্ডার তৈরি করুন
RUN mkdir -p uploads/temp uploads/processed results

# পোর্ট এক্সপোজ করুন
EXPOSE 8000

# অ্যাপ্লিকেশন চালান
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
