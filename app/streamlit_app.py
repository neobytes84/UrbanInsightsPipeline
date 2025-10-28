from http import client
from turtle import st
from backend.settings import get_settings
cfg = get_settings()
import os, sys
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path: sys.path.insert(0, ROOT_DIR)


st.subheader("Alertas activas")
alerts = client[cfg.MONGO_DB]["alerts_state"]
rows = list(alerts.find({}, {"_id":0}).sort("alertId", 1))
import pandas as pd
df_alerts = pd.DataFrame(rows)
if df_alerts.empty:
    st.caption("Sin alertas por ahora.")
else:
    st.dataframe(df_alerts, use_container_width=True)
