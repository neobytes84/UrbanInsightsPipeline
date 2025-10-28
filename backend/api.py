# backend/api.py
import os, sys, subprocess, platform, pathlib, signal
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from backend.producer import producer_singleton
from backend.settings import get_settings

ROOT = pathlib.Path(__file__).resolve().parents[1]  # raíz del repo
LOGS = ROOT / "logs"
LOGS.mkdir(exist_ok=True)
PIDFILE = ROOT / "run" / "stream.pid"
PIDFILE.parent.mkdir(exist_ok=True)

app = FastAPI(title="Urban Insights API", version="0.2.0")
cfg = get_settings()

# ---------- UI simple ----------
@app.get("/", response_class=HTMLResponse)
def ui():
    return f"""
    <html><head><title>Urban Insights</title>
    <style>body{{font-family:sans-serif;max-width:860px;margin:32px auto}}button{{padding:8px 14px;margin:6px}}</style>
    </head><body>
      <h1>Urban Insights — Control Panel</h1>
      <p>Kafka: <b>{cfg.KAFKA_BOOTSTRAP_SERVERS}</b> — Mongo: <b>{cfg.MONGO_URI}</b></p>
      <h2>Producer</h2>
      <form action="/play" method="post"><button>▶️ Play</button></form>
      <form action="/pause" method="post"><button>⏸️ Pause</button></form>
      <p><a href="/status">/status</a></p>

      <h2>Streaming (elige modo)</h2>
      <form action="/stream/start" method="post">
        <label><input type="radio" name="mode" value="docker" checked> Docker (recomendado, sin winutils)</label><br/>
        <label><input type="radio" name="mode" value="local"> Local (Windows: requiere winutils)</label><br/>
        <button>🚀 Start</button>
      </form>
      <form action="/stream/stop" method="post">
        <label><input type="radio" name="mode" value="docker" checked> Docker</label>
        <label><input type="radio" name="mode" value="local"> Local</label>
        <button>🛑 Stop</button>
      </form>
      <p><a href="/stream/status">/stream/status</a> — <a href="/stream/logs?mode=docker">logs docker</a> — <a href="/stream/logs?mode=local">logs local</a></p>

      <h2>Diagnóstico</h2>
      <p><a href="/diag">/diag</a></p>
    </body></html>
    """

# ---------- Producer controls ----------
@app.get("/status")
def status():
    return {"running": producer_singleton.is_running(),
            "kafka_topic": cfg.KAFKA_TOPIC,
            "bootstrap": cfg.KAFKA_BOOTSTRAP_SERVERS}

@app.post("/play")
def play():
    producer_singleton.start()
    return {"ok": True, "running": True}

@app.post("/pause")
def pause():
    producer_singleton.stop()
    return {"ok": True, "running": False}

# ---------- Streaming controls ----------
def _start_local() -> dict:
    py = sys.executable
    log = LOGS / "spark_stream.local.log"
    env = os.environ.copy()
    # Para imports y, si insistes en Windows, intentar ayudar con winutils
    env["PYTHONPATH"] = str(ROOT)
    if platform.system() == "Windows":
        env.setdefault("HADOOP_HOME", r"C:\hadoop")
        env["PATH"] = env.get("PATH","")
        if r"C:\hadoop\bin" not in env["PATH"]:
            env["PATH"] = r"C:\hadoop\bin;" + env["PATH"]

    p = subprocess.Popen(
        [py, str(ROOT / "jobs" / "streaming_kafka_to_mongo.py")],
        cwd=str(ROOT),
        env=env,
        stdout=open(log, "ab"),
        stderr=subprocess.STDOUT,
        creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP if platform.system()=="Windows" else 0)
    )
    PIDFILE.write_text(str(p.pid))
    return {"mode": "local", "pid": p.pid, "log": str(log)}

def _stop_local() -> dict:
    if not PIDFILE.exists():
        return {"mode":"local","stopped": False, "reason": "no pidfile"}
    pid = int(PIDFILE.read_text().strip() or "0")
    try:
        if platform.system()=="Windows":
            subprocess.run(["taskkill","/F","/PID",str(pid)], check=False)
        else:
            os.kill(pid, signal.SIGTERM)
        stopped = True
    except Exception as e:
        stopped = False
        return {"mode":"local","stopped": False, "error": str(e)}
    finally:
        PIDFILE.unlink(missing_ok=True)
    return {"mode":"local","stopped": stopped, "pid": pid}

def _start_docker() -> dict:
    cmd = ["docker","compose","-f", str(ROOT/"infra"/"docker-compose.yml"), "-p","urban_insights",
           "up","-d","spark-runner"]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return {"mode":"docker","ok": res.returncode==0, "output": res.stdout}

def _stop_docker() -> dict:
    cmd = ["docker","compose","-f", str(ROOT/"infra"/"docker-compose.yml"), "-p","urban_insights",
           "rm","-sf","spark-runner"]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return {"mode":"docker","ok": res.returncode==0, "output": res.stdout}

@app.post("/stream/start")
def stream_start(mode: str = Query("docker", enum=["docker","local"])):
    return _start_docker() if mode=="docker" else _start_local()

@app.post("/stream/stop")
def stream_stop(mode: str = Query("docker", enum=["docker","local"])):
    return _stop_docker() if mode=="docker" else _stop_local()

@app.get("/stream/status")
def stream_status():
    # docker status
    dcmd = ["docker","compose","-f", str(ROOT/"infra"/"docker-compose.yml"), "-p","urban_insights","ps","spark-runner"]
    dres = subprocess.run(dcmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    # local status
    local = {"running": PIDFILE.exists(), "pid": (PIDFILE.read_text().strip() if PIDFILE.exists() else None)}
    return {"docker": dres.stdout, "local": local}

@app.get("/stream/logs", response_class=PlainTextResponse)
def stream_logs(mode: str = Query("docker", enum=["docker","local"]), tail: int = 300):
    if mode=="docker":
        cmd = ["docker","compose","-f", str(ROOT/"infra"/"docker-compose.yml"), "-p","urban_insights",
               "logs","--no-color","--tail",str(tail),"spark-runner"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        return res.stdout
    else:
        p = LOGS / "spark_stream.local.log"
        if not p.exists():
            return PlainTextResponse("No hay log local aún.", status_code=404)
        with p.open("r", encoding="utf-8", errors="ignore") as f:
            data = f.readlines()[-tail:]
        return "".join(data)

# ---------- Diagnóstico ----------
@app.get("/diag")
def diag():
    info = {
        "platform": platform.platform(),
        "python": sys.version,
        "root": str(ROOT),
        "env": {
            "PYTHONPATH": os.environ.get("PYTHONPATH"),
            "HADOOP_HOME": os.environ.get("HADOOP_HOME"),
        }
    }
    return JSONResponse(info)
