"""Indicadores de ETH, SOL, LINK e SKY (ex-MKR) + derivativos de BTC/ETH, historico em CSV.
Fontes gratuitas e sem chave: Coin Metrics (community), DeFiLlama (precos, TVL, stablecoins), Deribit (DVOL, funding, OI),
CoinGecko (dominancia, snapshot). Cada fonte falha isolada: o script segue com as demais e lista o que faltou.
Saidas em data/cripto/: eth_indicadores.csv, sol_indicadores.csv, link_indicadores.csv, sky_indicadores.csv,
  derivativos_diarios.csv (DVOL e funding diario BTC/ETH), snapshots.csv (OI e dominancia: acumula uma linha por execucao),
  ratios_diarios.csv (ETH/BTC, SOL/BTC, LINK/BTC, SKY/ETH). Hipotese/base de analise, nao recomendacao.
Sobre o SKY: o token Sky (SKY) substituiu o MKR na razao 1 MKR = 24.000 SKY; o Coin Metrics so tem o MKR, entao
o historico anterior a set/2024 usa PriceUSD(MKR)/24000 (coluna price_mkr_equiv)."""
import os, time, datetime as dt
import numpy as np, pandas as pd, requests

HDR = {"User-Agent": "Mozilla/5.0 (pbj-scanner)"}
CM = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
ATIVOS = {  # nome: (asset Coin Metrics, metricas, id DeFiLlama/CoinGecko, chain DeFiLlama)
 "eth": ("eth", ["PriceUSD","CapMVRVCur","CapMrktCurUSD","AdrActCnt","TxCnt","FeeTotNtv","IssTotNtv","IssTotUSD","SplyCur","SplyExUSD","FlowInExUSD","FlowOutExUSD"], "ethereum", "Ethereum"),
 "sol": ("sol", ["PriceUSD","CapMrktEstUSD"], "solana", "Solana"),
 "link": ("link", ["PriceUSD","CapMVRVCur","CapMrktCurUSD","AdrActCnt","TxCnt","SplyCur","IssTotNtv"], "chainlink", None),
 "sky": ("mkr", ["PriceUSD","CapMVRVCur","CapMrktCurUSD","AdrActCnt","TxCnt","SplyCur"], "sky", None)}
MKR_PARA_SKY = 24000

def cm(asset, metricas, inicio="2014-01-01"):
    linhas, url, p = [], CM, {"assets": asset, "metrics": ",".join(metricas), "frequency": "1d", "start_time": inicio, "page_size": 10000}
    while url:
        r = requests.get(url, params=p, timeout=90, headers=HDR); r.raise_for_status(); j = r.json()
        linhas += [{"data": x["time"][:10], **{m: x.get(m) for m in metricas}} for x in j.get("data", [])]
        url, p = j.get("next_page_url"), None
    d = pd.DataFrame(linhas)
    for m in metricas: d[m] = pd.to_numeric(d[m], errors="coerce")
    return d.drop_duplicates("data")

def llama_preco(coin, inicio="2017-01-01"):
    """Preco diario pelo DeFiLlama (fonte secundaria); janelas de 500 dias."""
    t0 = int(pd.Timestamp(inicio).timestamp()); out = []
    while t0 < time.time():
        r = requests.get(f"https://coins.llama.fi/chart/coingecko:{coin}", params={"start": t0, "span": 500, "period": "1d"}, timeout=60, headers=HDR)
        r.raise_for_status(); pts = r.json().get("coins", {}).get(f"coingecko:{coin}", {}).get("prices", [])
        out += [(dt.datetime.utcfromtimestamp(x["timestamp"]).strftime("%Y-%m-%d"), x["price"]) for x in pts]
        t0 += 500 * 86400; time.sleep(0.4)
    return pd.DataFrame(out, columns=["data", "price_llama"]).drop_duplicates("data", keep="last")

def llama_tvl_chain(chain):
    r = requests.get(f"https://api.llama.fi/v2/historicalChainTvl/{chain}", timeout=60, headers=HDR); r.raise_for_status()
    d = pd.DataFrame(r.json()); d["data"] = pd.to_datetime(d["date"], unit="s").dt.strftime("%Y-%m-%d")
    return d.rename(columns={"tvl": "tvl_chain_usd"})[["data", "tvl_chain_usd"]].drop_duplicates("data", keep="last")

def llama_stables_chain(chain):
    r = requests.get(f"https://stablecoins.llama.fi/stablecoincharts/{chain}", timeout=60, headers=HDR); r.raise_for_status()
    d = pd.DataFrame([{"data": pd.to_datetime(int(x["date"]), unit="s").strftime("%Y-%m-%d"),
                       "stablecoins_usd": (x.get("totalCirculatingUSD") or {}).get("peggedUSD")} for x in r.json()])
    return d.drop_duplicates("data", keep="last")

def llama_tvl_protocolo(slug, nome):
    r = requests.get(f"https://api.llama.fi/protocol/{slug}", timeout=60, headers=HDR); r.raise_for_status()
    d = pd.DataFrame(r.json().get("tvl", [])); d["data"] = pd.to_datetime(d["date"], unit="s").dt.strftime("%Y-%m-%d")
    return d.rename(columns={"totalLiquidityUSD": nome})[["data", nome]].drop_duplicates("data", keep="last")

def deribit_dvol(moeda, anos=5):
    fim = int(time.time() * 1000); ini = fim - anos * 365 * 86400 * 1000; linhas = []
    while ini < fim:
        r = requests.get("https://www.deribit.com/api/v2/public/get_volatility_index_data",
                         params={"currency": moeda, "start_timestamp": ini, "end_timestamp": min(fim, ini + 900 * 86400 * 1000), "resolution": 86400},
                         timeout=60, headers=HDR); r.raise_for_status()
        d = r.json()["result"]["data"]
        linhas += [(dt.datetime.utcfromtimestamp(x[0] / 1000).strftime("%Y-%m-%d"), x[4]) for x in d]
        ini += 900 * 86400 * 1000; time.sleep(0.3)
    return pd.DataFrame(linhas, columns=["data", f"dvol_{moeda.lower()}"]).drop_duplicates("data", keep="last")

def deribit_funding(moeda, anos=3):
    """Funding medio diario (taxa de 8h anualizada em %) do perpetuo. Janelas de 30 dias."""
    fim = int(time.time() * 1000); ini = fim - anos * 365 * 86400 * 1000; linhas = []
    while ini < fim:
        r = requests.get("https://www.deribit.com/api/v2/public/get_funding_rate_history",
                         params={"instrument_name": f"{moeda}-PERPETUAL", "start_timestamp": ini, "end_timestamp": min(fim, ini + 30 * 86400 * 1000)},
                         timeout=60, headers=HDR)
        if r.status_code == 200: linhas += [(x["timestamp"], x["interest_8h"]) for x in r.json().get("result", [])]
        ini += 30 * 86400 * 1000; time.sleep(0.3)
    if not linhas: return pd.DataFrame(columns=["data", f"funding_{moeda.lower()}_aa_pct"])
    d = pd.DataFrame(linhas, columns=["ts", "f8"]); d["data"] = pd.to_datetime(d["ts"], unit="ms").dt.strftime("%Y-%m-%d")
    g = d.groupby("data")["f8"].sum().reset_index()   # soma das 3 janelas de 8h = taxa do dia
    g[f"funding_{moeda.lower()}_aa_pct"] = g["f8"] * 365 * 100; return g[["data", f"funding_{moeda.lower()}_aa_pct"]]

def snapshot_deribit():
    s = {"data": dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M")}
    for m in ("BTC", "ETH"):
        try:
            r = requests.get("https://www.deribit.com/api/v2/public/get_book_summary_by_currency", params={"currency": m, "kind": "future"}, timeout=60, headers=HDR)
            s[f"oi_futuros_{m.lower()}_usd"] = sum(x.get("open_interest", 0) for x in r.json()["result"])
            r = requests.get("https://www.deribit.com/api/v2/public/get_book_summary_by_currency", params={"currency": m, "kind": "option"}, timeout=60, headers=HDR)
            op = r.json()["result"]; put = sum(x["open_interest"] for x in op if x["instrument_name"].endswith("-P"))
            call = sum(x["open_interest"] for x in op if x["instrument_name"].endswith("-C"))
            s[f"put_call_oi_{m.lower()}"] = put / call if call else np.nan
        except Exception as e: print("falha snapshot deribit", m, e)
    try:
        g = requests.get("https://api.coingecko.com/api/v3/global", timeout=60, headers=HDR).json()["data"]
        s["dominancia_btc_pct"] = g["market_cap_percentage"]["btc"]; s["dominancia_eth_pct"] = g["market_cap_percentage"]["eth"]
        s["mcap_total_usd"] = g["total_market_cap"]["usd"]
    except Exception as e: print("falha coingecko global", e)
    return pd.DataFrame([s])

def tentar(nome, f, falhas):
    try: return f()
    except Exception as e: falhas.append(f"{nome}: {e}"); print("falha", nome, e); return None

def main():
    os.makedirs("data/cripto", exist_ok=True); falhas = []; precos = {}
    for nome, (asset, mets, coin, chain) in ATIVOS.items():
        partes = []
        d = tentar(f"coinmetrics {asset}", lambda: cm(asset, mets), falhas)
        if d is not None: partes.append(d)
        p = tentar(f"preco llama {coin}", lambda: llama_preco(coin, "2020-09-01" if nome == "sky" else "2017-01-01"), falhas)
        if p is not None: partes.append(p)
        if chain:
            for f, n in ((llama_tvl_chain, "tvl"), (llama_stables_chain, "stables")):
                x = tentar(f"{n} {chain}", lambda: f(chain), falhas)
                if x is not None: partes.append(x)
        if nome == "sky":
            x = tentar("tvl sky-lending", lambda: llama_tvl_protocolo("sky-lending", "tvl_sky_lending_usd"), falhas)
            if x is not None: partes.append(x)
        if nome == "eth":
            x = tentar("tvl lido", lambda: llama_tvl_protocolo("lido", "tvl_lido_usd"), falhas)
            if x is not None: partes.append(x)
        if not partes: continue
        t = partes[0]
        for x in partes[1:]: t = t.merge(x, on="data", how="outer")
        t = t.sort_values("data")
      t = t.drop_duplicates("data", keep="last")
        if nome == "eth" and {"FlowInExUSD", "FlowOutExUSD"} <= set(t.columns):
            t["netflow_exchanges_usd"] = t["FlowInExUSD"] - t["FlowOutExUSD"]      # >0: entrada liquida em exchanges (pressao vendedora, hipotese)
            t["netflow_7d_usd"] = t["netflow_exchanges_usd"].rolling(7, min_periods=5).sum()
        if nome == "sky":
            t["price_mkr_equiv"] = t.get("PriceUSD", np.nan) / MKR_PARA_SKY          # historico via MKR
            t["price_sky_usd"] = t["price_llama"].fillna(t["price_mkr_equiv"])
            precos["sky"] = t.set_index("data")["price_sky_usd"]
        else:
            pr = t.set_index("data")
            serie = pr["PriceUSD"] if "PriceUSD" in pr.columns else pd.Series(np.nan, index=pr.index)
            if "price_llama" in pr.columns: serie = serie.fillna(pr["price_llama"])
            precos[nome] = serie
        t.to_csv(f"data/cripto/{nome}_indicadores.csv", index=False, float_format="%.6g"); print(nome, len(t), "dias")
    # BTC (preco) para as razoes
    b = tentar("preco btc", lambda: cm("btc", ["PriceUSD"]), falhas)
    if b is not None: precos["btc"] = b.set_index("data")["PriceUSD"]
    if "btc" in precos:
        r = pd.DataFrame({k: (precos[k] / precos["btc"]) for k in ("eth", "sol", "link") if k in precos})
        r.columns = [f"{c}_btc" for c in r.columns]
        if "sky" in precos and "eth" in precos: r["sky_eth"] = precos["sky"] / precos["eth"]
        r.reset_index().rename(columns={"index": "data"}).to_csv("data/cripto/ratios_diarios.csv", index=False, float_format="%.8g")
    der = None
    for fn, m in [(deribit_dvol, "BTC"), (deribit_dvol, "ETH"), (deribit_funding, "BTC"), (deribit_funding, "ETH")]:
        x = tentar(f"deribit {fn.__name__} {m}", lambda: fn(m), falhas)
        if x is not None and len(x): der = x if der is None else der.merge(x, on="data", how="outer")
    if der is not None: der.sort_values("data").to_csv("data/cripto/derivativos_diarios.csv", index=False, float_format="%.6g")
    s = snapshot_deribit(); arq = "data/cripto/snapshots.csv"
    if os.path.exists(arq): s = pd.concat([pd.read_csv(arq), s])
    s.to_csv(arq, index=False)
    print("falhas:", falhas or "nenhuma")

if __name__ == "__main__":
    main()
