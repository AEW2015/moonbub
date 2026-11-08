from pathlib import Path
import subprocess,json,time
r=Path(__file__).resolve().parent/'camera01';r.mkdir(exist_ok=False)
ff='C:/Program Files/ffmpeg-7.1-essentials_build/bin/ffmpeg.exe'
cmd=[ff,'-hide_banner','-y','-f','dshow','-i','video=USB Video Device','-map','0:v:0','-t','300','-an','-c:v','libx264','-preset','ultrafast','-crf','25',str(r/'capture.mp4'),'-map','0:v:0','-t','300','-vf','fps=1','-update','1',str(r/'preview.png')]
(r/'command.json').write_text(json.dumps(cmd,indent=2))
with(r/'capture.log').open('x')as log:
 p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
 (r/'process.json').write_text(json.dumps({'pid':p.pid,'started_unix_us':time.time_ns()//1000,'coverage_seconds_requested':300},indent=2))
 try:code=p.wait(timeout=330)
 except subprocess.TimeoutExpired:p.terminate();code=p.wait(timeout=10)
(r/'result.json').write_text(json.dumps({'returncode':code,'pid':p.pid}))
print('CAMERA_FINISHED',code)
