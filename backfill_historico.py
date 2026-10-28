"""Backfill unico do historico dos ativos monitorados (rode UMA vez, ou quando incluir tickers novos).
Gera, em texto (CSV):
  data/prices/<TICKER>.csv        precos diarios (open, high, low, close, volume), ate 10 anos
  history/returns_hist.csv        tabela longa: data, yf, close, ret_1d..ret_252d, rsi14, dist_hi52, rng_pos (ultimos 3 anos, diario)
  history/hurst_hist.csv          tabela longa semanal (sextas): data, yf, H250, VR10, AC1 (ultimos 3 anos)
Uso: python backfill_historico.py [--anos 10] [--janela 3] [--universo scan_results.csv  (opcional: inclui todo o universo do scanner, ~600 ativos)]
Requer yfinance, pandas, numpy. Hipotese/base de analise, nao recomendacao."""
import argparse, os, re, time
import numpy as np, pandas as pd
from ret_scan import TICKERS, rsi14
from hurst_signals import hurst_dfa, variance_ratio, autocorr1
import hurst_scan

JANELAS = (1, 5, 21, 50, 63, 252)

def universo(extra_csv=None):
    t = list(dict.fromkeys(list(TICKERS) + list(hurst_scan.PRIORIDADE)))
    if extra_csv and os.path.exists(extra_csv):
        b = pd.read_csv(extra_csv)["yf"].dropna().astype(str)
        t = list(dict.fromkeys(t + [x for x in b if x != "CLPUSD=X"]))
    return t

def seguro(t): return re.sub(r"[^A-Za-z0-9._=-]", "_", t).replace("^", "_")

def baixa(tickers, anos):
    import yfinance as yf
    out = {}
    for i in range(0, len(tickers), 25):
        lote = tickers[i:i + 25]
        try:
            d = yf.download(lote, period=f"{anos}y", interval="1d", auto_adjust=True,
                            progress=False, group_by="ticker", threads=True)
        except Exception as e:
            print("falha no lote", i, e); continue
        for t in lote:
            try:
                df = (d[t] if len(lote) > 1 else d).dropna(how="all")
                df = df.dropna(subset=["Close"])
                if len(df) > 30: out[t] = df
            except Exception:
                pass
        print(f"lote {i//25+1}/{(len(tickers)-1)//25+1}: {len(out)} ativos"); time.sleep(1)
    return out

def serie_retornos(t, df, desde):
    c = df["Close"]
    r = pd.DataFrame({"data": df.index.strftime("%Y-%m-%d"), "yf": t, "close": c.values})
    for n in JANELAS: r[f"ret_{n}d"] = (c / c.shift(n) - 1).values * 100
    d = c.diff(); up = d.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    r["rsi14"] = (100 - 100 / (1 + up / dn.replace(0, np.nan))).values
    hi = df["High"].rolling(252, min_periods=60).max(); lo = df["Low"].rolling(252, min_periods=60).min()
    r["dist_hi52"] = ((c / hi - 1) * 100).values
    r["rng_pos"] = ((c - lo) / (hi - lo)).values
    return r[pd.to_datetime(r["data"]) >= desde]

def serie_hurst(t, df, desde):
    c = df["Close"].dropna(); linhas = []
    sextas = [d for d in c.index if d.weekday() == 4 and d >= desde]
    for d in sextas:
        w = c.loc[:d]
        if len(w) < 251: continue
        w250 = w.iloc[-251:]
        linhas.append({"data": d.strftime("%Y-%m-%d"), "yf": t, "H250": round(hurst_dfa(w250), 3),
                       "VR10": round(variance_ratio(w250, 10), 3), "AC1": round(autocorr1(w250), 3)})
    return linhas

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anos", type=int, default=10); ap.add_argument("--janela", type=int, default=3)
    ap.add_argument("--universo", default=""); a = ap.parse_args()
    os.makedirs("data/prices", exist_ok=True); os.makedirs("history", exist_ok=True)
    dados = baixa(universo(a.universo), a.anos)
    desde = pd.Timestamp.today().normalize() - pd.DateOffset(years=a.janela)
    R, H = [], []
    for t, df in dados.items():
        df.index = pd.to_datetime(df.index).tz_localize(None)
        p = df[["Open", "High", "Low", "Close", "Volume"]].copy(); p.index.name = "date"
        p.to_csv(f"data/prices/{seguro(t)}.csv", float_format="%.6g")
        R.append(serie_retornos(t, df, desde)); H += serie_hurst(t, df, desde)
    pd.concat(R).to_csv("history/returns_hist.csv", index=False, float_format="%.4f")
    pd.DataFrame(H).to_csv("history/hurst_hist.csv", index=False)
    print(f"{len(dados)} ativos; returns_hist {sum(len(x) for x in R)} linhas; hurst_hist {len(H)} linhas")

if __name__ == "__main__":
    main()
