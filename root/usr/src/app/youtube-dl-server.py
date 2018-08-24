import json
import os
import subprocess
from queue import Queue
from bottle import route, run, Bottle, request, static_file
from threading import Thread
from os import listdir
from os.path import isfile, join

app = Bottle()

@app.route('/youtube-dl')
def dl_queue_list():
    return static_file('index.html', root='./')

@app.route('/youtube-dl/static/:filename#.*#')
def server_static(filename):
    return static_file(filename, root='./static')

@app.route('/youtube-dl/completed', method='GET')
def q_size():
    downloadPath = '/youtube-dl'
    completed = [f for f in listdir(downloadPath) if isfile(join(downloadPath, f))]
    return { "success" : True, "files" : list(completed) }

@app.route('/youtube-dl/q', method='GET')
def q_size():
    return { "success" : True, "size" : json.dumps(list(dl_q.queue)) }

@app.route('/youtube-dl/q', method='POST')
def q_put():
    url = request.forms.get( "url" )
    audio = request.forms.get( "audio", "" )
    if "" != url:
        dl_q.put( { "url": url, "only_audio":  bool(audio) } )
        print("Added url " + url + " to the download queue")
        return { "success" : True, "url" : url }
    else:
        return { "success" : False, "error" : "dl called without a url" }

def dl_worker():
    while not done:
        item = dl_q.get()
        download(item)
        dl_q.task_done()

def download(item):
    l_command = ["youtube-dl",
        "-o", "/youtube-dl/.incomplete/" + os.getenv("YTBDL_O", "%(title)s.%(ext)s"),
        "-f", os.getenv("YTBDL_F", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]")]
    if item.get("only_audio"):
        l_command += ["-x"]
    url = item.get("url")
    print("Starting download of " + url)
    subprocess.run(l_command + ["--exec", "touch {} && mv {} /youtube-dl/", "--merge-output-format", "mp4", url])
    print("Finished downloading " + url)

dl_q = Queue();
done = False;
dl_thread = Thread(target=dl_worker)
dl_thread.start()

print("Started download thread")

app.run(host='0.0.0.0', port=8080, debug=True)
done = True
dl_thread.join()