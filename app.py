import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="NBA 20+ Survivor EV", layout="wide")
st.title("NBA 20+ Points Survivor EV (Exact Enumeration)")

st.caption("Exact EV via full enumeration (best when player list ≤ 15).")

pool_size = st.number_input("Pool size", min_value=1, value=1000, step=100)

st.write("### Inputs")
st.write("Enter Player, Prob_20+ (0–1), Ownership (0–1). Ownership is normalized automatically.")

default = pd.DataFrame(
    {
        "Player": ["wemby", "cade", "durant", "sengun"],
        "Prob_20+": [0.8, 0.8, 0.8, 0.6],
        "Ownership": [0.2, 0.3, 0.2, 0.08],
    }
)

df = st.data_editor(default, num_rows="dynamic", use_container_width=True)

df = df.copy()
df["Player"] = df["Player"].astype(str).str.strip()
df = df[df["Player"] != ""]

if len(df) == 0:
    st.stop()

if len(df) > 15:
    st.error("Max 15 players for exact enumeration. Reduce the list or add a Monte Carlo mode.")
    st.stop()

for c in ["Prob_20+", "Ownership"]:
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)

if (df["Prob_20+"] < 0).any() or (df["Prob_20+"] > 1).any():
    st.error("Prob_20+ must be between 0 and 1.")
    st.stop()

total_own = df["Ownership"].sum()
if total_own <= 0:
    st.error("Total ownership must be > 0.")
    st.stop()

p = df["Prob_20+"].to_numpy(dtype=float)
own = df["Ownership"].to_numpy(dtype=float)
own_norm = own / total_own

N = len(df)
num_scenarios = 1 << N  # 2^N

ev = np.zeros(N, dtype=float)

for s in range(num_scenarios):
    scenario_prob = 1.0
    survivors = 0.0

    for j in range(N):
        hit = (s >> j) & 1
        if hit:
            scenario_prob *= p[j]
            survivors += own_norm[j] * pool_size
        else:
            scenario_prob *= (1.0 - p[j])

    if survivors > 0 and scenario_prob > 0:
        payout = 1.0 / survivors
        for j in range(N):
            if (s >> j) & 1:
                ev[j] += scenario_prob * payout

out = df.copy()
out["Exact EV"] = ev
out["EV Index"] = ev * pool_size

out = out.sort_values("EV Index", ascending=False)

st.write("### Results")
st.dataframe(out, use_container_width=True)

csv = out.to_csv(index=False).encode("utf-8")
st.download_button("Download CSV", data=csv, file_name="nba_survivor_ev.csv", mime="text/csv")
