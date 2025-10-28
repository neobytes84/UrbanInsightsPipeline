import requests, time, subprocess

def stop_producer():
    try:
        requests.post("http://localhost:8000/pause", timeout=2)
    except Exception:
        pass

if __name__ == "__main__":
    print("→ Pausando productor…"); stop_producer()
    print("→ Esperando drenaje (10s)…"); time.sleep(10)
    print("→ docker compose down"); subprocess.run(["docker","compose","down"])
