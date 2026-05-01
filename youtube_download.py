import os
import yt_dlp as youtube_dl

def download_video(url, output_path):
    """
    Download video using yt-dlp (more reliable than pytube)
    """
    # Ensure folder exists
    folder = os.path.dirname(output_path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)

    ydl_opts = {
        'outtmpl': output_path,     # save exact filename
        'format': 'bestvideo+bestaudio/best',  # highest quality
        'merge_output_format': 'mp4'
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    print("Downloaded to:", output_path)


download_video(
    'https://www.youtube.com/watch?v=fsQgc9pCyDU',
    '/Users/nethra/Desktop/video/video_new.mp4'
)
