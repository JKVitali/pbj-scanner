"""Calcula Hurst/VR/autocorrelacao para os ativos do scan_results.csv e grava hurst_results.csv.
Independente do scan.py. Requer: yfinance, pandas, numpy. Hipotese, nao recomendacao."""
import sys, time
import numpy as np, pandas as pd, yfinance as yf
from hurst_signals import persistence_row

PRIORIDADE = ["GC=F", "SI=F", "CL=F", "BZ=F", "^GSPC", "^IXIC", "^BVSP", "BRL=X", "DX-Y.NYB",
              "BTC-USD", "^TNX", "XLRE", "VNQ", "GLD", "SLV", "TLT"]

def main(src="scan_results.csv", out="hurst_results.csv"):
    base = pd.read_csv(src)
    # remove duplicatas: pares invertidos (CLPUSD=X) e alias de BRL
    ALIAS = {"USDBRL=X": "BRL=X"}
    bruto = [ALIAS.get(t, t) for t in base["yf"].dropna().astype(str)]
    bruto = [t for t in bruto if t != "CLPUSD=X"]
    tickers = list(dict.fromkeys(PRIORIDADE + bruto))
    rows = []
    for i in range(0, len(tickers), 40):
        lote = tickers[i:i + 40]
        try:
            df = yf.download(lote, period="2y", interval="1d", auto_adjust=True,
                             progress=False, group_by="ticker", threads=True)
        except Exception as e:
            print("falha no lote", i, e); continue
        for t in lote:
            try:
                c = (df[t]["Close"] if len(lote) > 1 else df["Close"]).dropna()
                if len(c) < 130: continue
                r = persistence_row(c)
                ultimo = c.index[-1]
                atraso = int(np.busday_count(ultimo.date(), pd.Timestamp.today().date()))
                r.update({"yf": t, "ultimo_close": float(c.iloc[-1]),
                          "data": str(ultimo.date()), "n": len(c),
                          "defasado": atraso > 3})
                if r["defasado"]:
                    r["regime_H120"] = r["regime_H250"] = "defasado"
                rows.append(r)
            except Exception:
                continue
        time.sleep(1)
    res = pd.DataFrame(rows)
    cols = ["yf", "data", "n", "ultimo_close", "H120", "H250", "dH120_20d", "regime_H120",
            "regime_H250", "VR5", "VR10", "AC1", "alerta_descontinuidade", "defasado"]
    res = res.reindex(columns=cols)
    res.to_csv(out, index=False)
    import os
    os.makedirs("history", exist_ok=True)   # historico diario em texto (CSV)
    if len(res) and res["data"].notna().any():
        res.to_csv(f"history/hurst_{res['data'].max()}.csv", index=False)
    print(f"{len(res)} ativos gravados em {out}")

if __name__ == "__main__":
    main(*sys.argv[1:])
