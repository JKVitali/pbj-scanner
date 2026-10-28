"""Retornos diarios dos tickers dos radares (para o PDF diario do PBJ).
Gera returns_results.csv: yf, data, close, ret_1d, ret_5d, ret_21d, ret_50d, ret_63d, ret_252d,
rsi14, hi52, lo52, dist_hi52, rng_pos. Independente do scan.py. Requer yfinance, pandas, numpy.
Hipotese, nao recomendacao. Todos os retornos sao em % sobre fechamentos ajustados."""
import sys, time
import numpy as np, pandas as pd, yfinance as yf

TICKERS = """GDX GDXJ SIL SILJ SLV IAU PAAS ANGPY NEM B AEM WPM FNV HL CDE KGC GFI HMY GC=F SI=F
PALL PPLT SBSW IMPUY AGPPF PL=F PA=F PLG
IBIT BITB CLSK RIOT MSTR COIN BMNR IREN CIFR WULF HUT CORZ MARA BTC-USD
PLTR CRDO AAOI SOUN POET AI PATH META AMZN TSLA NVDA MSFT GOOGL AVGO TSM MU AMD ORCL
BABA BIDU KWEB MCHI FXI TCEHY
URA CCJ UEC DNN URNM NXE LEU SRUUF
COPX FCX MP UUUU USAR LYSDY REMX
MSOS TLRY CGC IIPR CRON ACB IMCC GTBIF CURLF TCNNF CRLBF VRNOF SNDL""".split()
JANELAS = (1, 5, 21, 50, 63, 252)

def rsi14(c, n=14):
    d = c.diff(); up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return float((100 - 100 / (1 + up / dn.replace(0, np.nan))).iloc[-1])

def linha(t, df):
    c = df["Close"].dropna()
    if len(c) < 30: return None
    r = {"yf": t, "data": str(c.index[-1].date()), "close": float(c.iloc[-1])}
    for n in JANELAS:
        r[f"ret_{n}d"] = (c.iloc[-1] / c.iloc[-1 - n] - 1) * 100 if len(c) > n else np.nan
    w = c.tail(252)
    hi = float(df["High"].dropna().tail(252).max()) if "High" in df else float(w.max())
    lo = float(df["Low"].dropna().tail(252).min()) if "Low" in df else float(w.min())
    r.update(rsi14=rsi14(c), hi52=hi, lo52=lo, dist_hi52=(r["close"] / hi - 1) * 100,
             rng_pos=(r["close"] - lo) / (hi - lo) if hi > lo else np.nan)
    return r

def main(out="returns_results.csv"):
    rows = []
    for i in range(0, len(TICKERS), 40):
        lote = TICKERS[i:i + 40]
        try:
            d = yf.download(lote, period="2y", interval="1d", auto_adjust=True,
                            progress=False, group_by="ticker", threads=True)
        except Exception as e:
            print("falha no lote", i, e); continue
        for t in lote:
            try:
                df = (d[t] if len(lote) > 1 else d).dropna(how="all")
                r = linha(t, df)
                if r: rows.append(r)
            except Exception:
                continue
        time.sleep(1)
    res = pd.DataFrame(rows)
    res.to_csv(out, index=False, float_format="%.4f")
    import os
    os.makedirs("history", exist_ok=True)   # historico diario em texto (CSV), ~10 KB por dia
    stamp = res["data"].max() if len(res) else "sem_dados"
    res.to_csv(f"history/returns_{stamp}.csv", index=False, float_format="%.4f")
    print(f"{len(res)} ativos gravados em {out}")

if __name__ == "__main__":
    main(*sys.argv[1:])
