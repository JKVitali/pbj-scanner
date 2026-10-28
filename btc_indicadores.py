"""Indicadores on-chain e de sentimento do Bitcoin, historico completo, em CSV.
Fontes gratuitas e sem chave: Coin Metrics (community API), alternative.me (Fear & Greed), blockchain.com (charts).
Gera: data/btc/btc_indicadores.csv (uma linha por dia, colunas abaixo) e data/btc/raw_*.csv por fonte.
Colunas: data, price_usd, mvrv, mvrv_z (aprox.), market_cap, realized_cap, nvt_adj, hash_rate_ths (blockchain.com, TH/s),
hash_rate_cm (Coin Metrics), difficulty, miners_revenue_usd, hashprice_usd_ths_dia, puell (receita / media 365d),
hash_ribbon (MM30 / MM60 do hash rate; <1 = capitulacao de mineradores), fees_usd, tx_count, active_addr, fear_greed.
Uso: python btc_indicadores.py [--incremental]. Hipotese/base de analise, nao recomendacao."""
import argparse, io, os, time
import numpy as np, pandas as pd, requests

CM = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
CM_METRICAS = {"PriceUSD": "price_usd", "CapMVRVCur": "mvrv", "CapMrktCurUSD": "market_cap", "CapRealUSD": "realized_cap",
               "NVTAdj": "nvt_adj", "HashRate": "hash_rate_cm", "FeeTotUSD": "fees_usd", "TxCnt": "tx_count", "AdrActCnt": "active_addr"}
BC = {"hash-rate": "hash_rate_ths", "difficulty": "difficulty", "miners-revenue": "miners_revenue_usd"}
HDR = {"User-Agent": "Mozilla/5.0 (pbj-scanner)"}

def coinmetrics(metrica, inicio="2010-07-18"):
    linhas, url, params = [], CM, {"assets": "btc", "metrics": metrica, "frequency": "1d", "start_time": inicio, "page_size": 10000}
    while url:
        r = requests.get(url, params=params, timeout=90, headers=HDR); r.raise_for_status(); j = r.json()
        linhas += [(x["time"][:10], x.get(metrica)) for x in j.get("data", [])]
        url, params = j.get("next_page_url"), None
    d = pd.DataFrame(linhas, columns=["data", CM_METRICAS[metrica]])
    d[CM_METRICAS[metrica]] = pd.to_numeric(d[CM_METRICAS[metrica]], errors="coerce")
    return d.drop_duplicates("data")

def fear_greed():
    r = requests.get("https://api.alternative.me/fng/", params={"limit": 0, "format": "json"}, timeout=90, headers=HDR); r.raise_for_status()
    d = pd.DataFrame(r.json()["data"])
    d["data"] = pd.to_datetime(d["timestamp"].astype(int), unit="s").dt.strftime("%Y-%m-%d")
    d["fear_greed"] = pd.to_numeric(d["value"]); return d[["data", "fear_greed"]].drop_duplicates("data")

def blockchain(grafico, nome):
    r = requests.get(f"https://api.blockchain.info/charts/{grafico}", params={"timespan": "all", "format": "json", "sampled": "false"},
                     timeout=120, headers=HDR); r.raise_for_status()
    d = pd.DataFrame(r.json()["values"]); d["data"] = pd.to_datetime(d["x"], unit="s").dt.strftime("%Y-%m-%d")
    return d.rename(columns={"y": nome})[["data", nome]].drop_duplicates("data")

def derivados(t):
    t = t.sort_values("data").reset_index(drop=True)
    if {"hash_rate_ths", "miners_revenue_usd"} <= set(t.columns):
        t["hashprice_usd_ths_dia"] = t["miners_revenue_usd"] / t["hash_rate_ths"]
    if "miners_revenue_usd" in t:
        t["puell"] = t["miners_revenue_usd"] / t["miners_revenue_usd"].rolling(365, min_periods=200).mean()
    if "hash_rate_ths" in t:
        t["hash_ribbon"] = t["hash_rate_ths"].rolling(30, min_periods=20).mean() / t["hash_rate_ths"].rolling(60, min_periods=40).mean()
    if {"market_cap", "realized_cap"} <= set(t.columns):
        sd = t["market_cap"].expanding(min_periods=365).std()
        t["mvrv_z"] = (t["market_cap"] - t["realized_cap"]) / sd   # aproximacao do MVRV Z-Score (desvio expansivo do valor de mercado)
    return t

def main():
    os.makedirs("data/btc", exist_ok=True); partes = []
    for m in CM_METRICAS:
        try: d = coinmetrics(m); d.to_csv(f"data/btc/raw_coinmetrics_{m}.csv", index=False); partes.append(d); print("coinmetrics", m, len(d))
        except Exception as e: print("falha coinmetrics", m, e)
        time.sleep(0.5)
    try: d = fear_greed(); d.to_csv("data/btc/raw_fear_greed.csv", index=False); partes.append(d); print("fear_greed", len(d))
    except Exception as e: print("falha fear_greed", e)
    for g, n in BC.items():
        try: d = blockchain(g, n); d.to_csv(f"data/btc/raw_blockchain_{g}.csv", index=False); partes.append(d); print("blockchain", g, len(d))
        except Exception as e: print("falha blockchain", g, e)
        time.sleep(0.5)
    if not partes: print("nada baixado"); return
    t = partes[0]
    for p in partes[1:]: t = t.merge(p, on="data", how="outer")
    t = derivados(t)
    ordem = ["data","price_usd","mvrv","mvrv_z","market_cap","realized_cap","nvt_adj","hash_rate_ths","hash_rate_cm","difficulty",
             "miners_revenue_usd","hashprice_usd_ths_dia","puell","hash_ribbon","fees_usd","tx_count","active_addr","fear_greed"]
    t = t.reindex(columns=[c for c in ordem if c in t.columns]).sort_values("data")
    t.to_csv("data/btc/btc_indicadores.csv", index=False, float_format="%.6g")
    print(f"{len(t)} dias, {t['data'].iloc[0]} a {t['data'].iloc[-1]} em data/btc/btc_indicadores.csv")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--incremental", action="store_true"); ap.parse_args(); main()
