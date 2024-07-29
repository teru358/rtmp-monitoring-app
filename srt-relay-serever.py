import subprocess
import time

def run_ffmpeg():
    command = [
        "ffmpeg",
        "-i", "srt://0.0.0.0:8080?mode=listener",
        "-c:v", "copy",
        "-c:a", "copy",
        "-f", "flv",
        "rtmp://localhost/live/your_stream_key",
    ]

    while True:
        # FFmpegプロセスの開始
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        print("FFmpeg process started.")

        try:
            # プロセスの出力を監視
            for line in process.stderr:
                print(line.decode().strip())

        except KeyboardInterrupt:
            print("Process interrupted by user.")
            process.terminate()
            break

        # プロセスが終了した場合の処理
        print("FFmpeg process stopped. Restarting in 5 seconds...")
        process.wait()
        time.sleep(5)

if __name__ == "__main__":
    run_ffmpeg()
