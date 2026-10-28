"""Backfill do maximo historico dos ativos-chave (juros, ouro, prata, indices, dolar, energia, cripto).
Rode UMA vez (Actions > Backfill macro), depois atualize incrementalmente com --atualizar.
Gera, em texto (CSV):
  data/macro/yf/<TICKER>.csv   Yahoo, periodo maximo disponivel (date, open, high, low, close, volume)
  data/macro/fred/<SERIE>.csv  FRED (api.stlouisfed.org, requer secret FRED_API_KEY): date, value  (juros, curva, credito, M2, balanco do Fed...)
  data/macro/bcb/<SGS>_<nome>.csv  BCB SGS (Selic, CDI, IPCA, PTAX...), em janelas de 10 anos
  data/macro/INDICE.csv        resumo: fonte, serie, primeira data, ultima data, linhas
Requer yfinance, pandas, requests. Hipotese/base de analise, nao recomendacao."""
import argparse, io, os, re, time, datetime as dt
import pandas as pd

YF = {  # ticker: descricao
 "GC=F":"ouro futuros","SI=F":"prata futuros","PL=F":"platina futuros","PA=F":"paladio futuros","HG=F":"cobre futuros",
 "CL=F":"WTI","BZ=F":"Brent","NG=F":"gas natural","^TNX":"juro 10a EUA","^TYX":"juro 30a EUA","^FVX":"juro 5a EUA","^IRX":"juro 13 semanas EUA",
 "^GSPC":"S&P 500","^IXIC":"Nasdaq","^DJI":"Dow Jones","^RUT":"Russell 2000","^VIX":"VIX","^BVSP":"Ibovespa","DX-Y.NYB":"DXY","BRL=X":"USD/BRL",
 "EURUSD=X":"EUR/USD","JPY=X":"USD/JPY","CNY=X":"USD/CNY","BTC-USD":"Bitcoin","ETH-USD":"Ether","GLD":"ETF ouro","SLV":"ETF prata",
 "GDX":"mineradoras de ouro","TLT":"Treasuries 20a+","IEF":"Treasuries 7-10a","HYG":"high yield","XLRE":"REITs EUA","VNQ":"REITs EUA","XLE":"energia","XLF":"financeiro","XLK":"tecnologia",
 "EWZ":"Brasil ETF","EEM":"emergentes","FXI":"China ETF","URA":"uranio ETF","COPX":"cobre mineradoras","PALL":"ETF paladio","PPLT":"ETF platina"}
FRED = {  # serie: descricao
 "DGS1MO":"Treasury 1m","DGS3MO":"Treasury 3m","DGS6MO":"Treasury 6m","DGS1":"Treasury 1a","DGS2":"Treasury 2a","DGS3":"Treasury 3a","DGS5":"Treasury 5a",
 "DGS7":"Treasury 7a","DGS10":"Treasury 10a","DGS20":"Treasury 20a","DGS30":"Treasury 30a","DFII5":"TIPS 5a","DFII10":"TIPS 10a","T10YIE":"inflacao implicita 10a",
 "T5YIFR":"inflacao implicita 5a5a","T10Y2Y":"curva 10a-2a","T10Y3M":"curva 10a-3m","FEDFUNDS":"Fed funds efetiva (mensal)","DFF":"Fed funds efetiva (diaria)",
 "SOFR":"SOFR","BAMLH0A0HYM2":"spread high yield","BAMLC0A0CM":"spread grau de investimento","MORTGAGE30US":"hipoteca 30a","UNRATE":"desemprego EUA",
 "CPIAUCSL":"CPI EUA","PCEPILFE":"PCE core","M2SL":"M2 EUA","WALCL":"balanco do Fed","RRPONTSYD":"reverse repo","DTWEXBGS":"dolar amplo (Fed)",
 "VIXCLS":"VIX","DCOILWTICO":"WTI (FRED)","DCOILBRENTEU":"Brent (FRED)","GOLDPMGBD228NLBM":"ouro LBMA PM (se disponivel)","IRLTLT01BRM156N":"juro longo Brasil (OCDE)"}
BCB = {  # codigo SGS: nome
 432:"selic_meta",11:"selic_diaria",4389:"cdi_anualizado",433:"ipca_mensal",13522:"ipca_12m",1:"ptax_venda",21619:"ptax_euro",
 7326:"pib_var_anual",24363:"ibc_br",27841:"saldo_credito_pib"}

def indice_add(lista, fonte, serie, df, col_data="date"):
    if df is None or df.empty: lista.append((fonte, serie, "", "", 0)); return
    lista.append((fonte, serie, str(df[col_data].iloc[0])[:10], str(df[col_data].iloc[-1])[:10], len(df)))

def yf_max(ticker):
    import yfinance as yf
    d = yf.download(ticker, period="max", interval="1d", auto_adjust=True, progress=False)
    if isinstance(d.columns, pd.MultiIndex): d.columns = d.columns.get_level_values(0)
    d = d.dropna(subset=["Close"])
    d.index = pd.to_datetime(d.index).tz_localize(None); d.index.name = "date"
    return d[["Open","High","Low","Close","Volume"]].reset_index()

def fred(serie):
    import os, requests
    chave = os.environ.get("FRED_API_KEY")
    if not chave: raise RuntimeError("defina o secret FRED_API_KEY (GitHub Actions) para usar a API do FRED")
    r = requests.get("https://api.stlouisfed.org/fred/series/observations",
        params={"series_id": serie, "api_key": chave, "file_type": "json"}, timeout=60,
        headers={"User-Agent": "Mozilla/5.0 (pbj-scanner)"})
    r.raise_for_status()
    return parse_fred(r.json().get("observations", []), serie)
    
def parse_fred(observacoes, serie):
    d = pd.DataFrame(observacoes, columns=["date", "value"])
    d["value"] = pd.to_numeric(d["value"], errors="coerce")  # FRED usa "." para vazio
    return d.dropna(subset=["value"]).reset_index(drop=True)

def bcb(codigo, inicio=1995):
    import requests
    partes = []; ano = inicio; hoje = dt.date.today()
    while ano <= hoje.year:   # a API limita series diarias a janelas de 10 anos
        fim = min(ano + 9, hoje.year)
        url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
        r = requests.get(url, params={"formato": "json", "dataInicial": f"01/01/{ano}", "dataFinal": f"31/12/{fim}"}, timeout=60)
        if r.status_code == 200 and r.text.strip().startswith("["): partes.append(parse_bcb(r.text))
        ano = fim + 1; time.sleep(0.5)
    if not partes: return pd.DataFrame(columns=["date", "value"])
    return pd.concat(partes).drop_duplicates("date").sort_values("date").reset_index(drop=True)

def parse_bcb(texto):
    d = pd.read_json(io.StringIO(texto)); 
    if d.empty: return pd.DataFrame(columns=["date", "value"])
    d["date"] = pd.to_datetime(d["data"], format="%d/%m/%Y").dt.strftime("%Y-%m-%d")
    d["value"] = pd.to_numeric(d["valor"], errors="coerce")
    return d[["date", "value"]].dropna()

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--so", choices=["yf", "fred", "bcb"], default=None); a = ap.parse_args()
    for p in ("data/macro/yf", "data/macro/fred", "data/macro/bcb"): os.makedirs(p, exist_ok=True)
    idx = []
    if a.so in (None, "yf"):
        for t in YF:
            try:
                d = yf_max(t); d.to_csv(f"data/macro/yf/{re.sub(r'[^A-Za-z0-9._=-]', '_', t)}.csv", index=False, float_format="%.6g")
                indice_add(idx, "yf", t, d); print("yf", t, len(d))
            except Exception as e: print("falha yf", t, e); indice_add(idx, "yf", t, None)
            time.sleep(0.5)
    if a.so in (None, "fred"):
        for s in FRED:
            try:
                d = fred(s); d.to_csv(f"data/macro/fred/{s}.csv", index=False); indice_add(idx, "fred", s, d); print("fred", s, len(d))
            except Exception as e: print("falha fred", s, e); indice_add(idx, "fred", s, None)
            time.sleep(0.5)
    if a.so in (None, "bcb"):
        for c, n in BCB.items():
            try:
                d = bcb(c); d.to_csv(f"data/macro/bcb/{c}_{n}.csv", index=False); indice_add(idx, "bcb", f"{c}_{n}", d); print("bcb", c, len(d))
            except Exception as e: print("falha bcb", c, e); indice_add(idx, "bcb", f"{c}_{n}", None)
    pd.DataFrame(idx, columns=["fonte", "serie", "primeira_data", "ultima_data", "linhas"]).to_csv("data/macro/INDICE.csv", index=False)
    print("indice gravado: data/macro/INDICE.csv")

if __name__ == "__main__":
    main()
