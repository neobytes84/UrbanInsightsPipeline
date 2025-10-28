import shutil, os, time
SRC = os.getenv("CHECKPOINT_DIR","./chk/traffic")
DST = f"./resilience_engine/ckpt_snapshots/ckpt_{int(time.time())}"
if os.path.isdir(SRC):
    os.makedirs(os.path.dirname(DST), exist_ok=True)
    shutil.copytree(SRC, DST)
    print(f"✅ Snapshot de checkpoints en {DST}")
else:
    print("ℹ️ No hay checkpoints aún.")
