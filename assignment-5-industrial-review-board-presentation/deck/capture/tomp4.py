import subprocess, sys, imageio_ffmpeg
src, dst, start, speed = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
ff = imageio_ffmpeg.get_ffmpeg_exe()
subprocess.run([ff, "-v", "error", "-y", "-ss", start, "-i", src,
                "-vf", f"crop=1600:860:0:40,setpts=PTS/{speed},scale=1280:-2,fps=30",
                "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "24", "-preset", "slow",
                "-movflags", "+faststart", dst], check=True)
# poster frame
subprocess.run([ff, "-v", "error", "-y", "-ss", "3", "-i", dst, "-frames:v", "1", dst.rsplit(".", 1)[0] + "_poster.jpg"], check=True)
