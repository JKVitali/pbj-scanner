"""Resume os indicadores cripto numa tabela pequena (data/cripto_resumo.csv) para a rotina e o PDF diario.
Le: data/btc/btc_indicadores.csv, data/cripto/*_indicadores.csv, derivativos_diarios.csv, ratios_diarios.csv, snapshots.csv.
Para cada indicador: valor mais recente, data, variacao 1d/7d/30d (% ou pontos), percentil no historico completo e uma faixa de leitura
(limiares sao HIPOTESES de leitura, nao recomendacao). Colunas: grupo, ativo, indicador, valor, data, var_1d, var_7d, var_30d, tipo_var, percentil, faixa."""
import os
import numpy as np, pandas as pd

# (grupo, ativo, indicador, arquivo, coluna, tipo_var 'pct' ou 'abs', faixas [(limite_superior, rotulo)...] em ordem crescente, suavizar_dias)
R = [
 ("Preço e sentimento","BTC","Preço (US$)","data/btc/btc_indicadores.csv","price_usd","pct",None,1),
 ("Preço e sentimento","BTC","Fear & Greed (0–100)","data/btc/btc_indicadores.csv","fear_greed","abs",[(25,"medo extremo"),(45,"medo"),(55,"neutro"),(75,"ganância"),(101,"ganância extrema")],1),
 ("Valuation on-chain","BTC","MVRV","data/btc/btc_indicadores.csv","mvrv","abs",[(1.0,"abaixo do custo realizado"),(2.4,"faixa intermediária"),(3.7,"aquecido"),(99,"euforia")],1),
 ("Valuation on-chain","BTC","MVRV Z (aprox.)","data/btc/btc_indicadores.csv","mvrv_z","abs",[(0,"baixo"),(3,"intermediário"),(7,"alto"),(99,"extremo")],1),
 ("Valuation on-chain","BTC","NVT ajustado","data/btc/btc_indicadores.csv","nvt_adj","pct",None,1),
 ("Mineradores","BTC","Hash rate (média 7d, TH/s)","data/btc/btc_indicadores.csv","hash_rate_ths","pct",None,7),
 ("Mineradores","BTC","Hash ribbon (MM30/MM60)","data/btc/btc_indicadores.csv","hash_ribbon","abs",[(1.0,"capitulação de mineradores"),(99,"recuperação/expansão")],1),
 ("Mineradores","BTC","Hashprice (US$/TH/s/dia, média 7d)","data/btc/btc_indicadores.csv","hashprice_usd_ths_dia","pct",None,7),
 ("Mineradores","BTC","Puell (receita/MM365)","data/btc/btc_indicadores.csv","puell","abs",[(0.5,"receita baixa"),(1.5,"intermediário"),(99,"receita alta")],1),
 ("Mineradores","BTC","Dificuldade","data/btc/btc_indicadores.csv","difficulty","pct",None,1),
 ("Atividade","BTC","Endereços ativos (média 7d)","data/btc/btc_indicadores.csv","active_addr","pct",None,7),
 ("Derivativos","BTC","DVOL (vol. implícita 30d)","data/cripto/derivativos_diarios.csv","dvol_btc","abs",None,1),
 ("Derivativos","BTC","Funding perpétuo (% a.a.)","data/cripto/derivativos_diarios.csv","funding_btc_aa_pct","abs",[(0,"vendedores pagam"),(15,"normal"),(99,"alavancagem comprada")],3),
 ("Preço e sentimento","ETH","Preço (US$)","data/cripto/eth_indicadores.csv","PriceUSD","pct",None,1),
 ("Preço e sentimento","ETH","ETH/BTC","data/cripto/ratios_diarios.csv","eth_btc","pct",None,1),
 ("Valuation on-chain","ETH","MVRV","data/cripto/eth_indicadores.csv","CapMVRVCur","abs",[(1.0,"abaixo do custo realizado"),(2.4,"faixa intermediária"),(99,"aquecido")],1),
 ("Atividade","ETH","Endereços ativos (média 7d)","data/cripto/eth_indicadores.csv","AdrActCnt","pct",None,7),
 ("Fluxos","ETH","Netflow exchanges, 7d (US$)","data/cripto/eth_indicadores.csv","netflow_7d_usd","abs",[(0,"saída líquida (acumulação, hipótese)"),(99e18,"entrada líquida (pressão vendedora, hipótese)")],1),
 ("DeFi","ETH","TVL da rede (US$)","data/cripto/eth_indicadores.csv","tvl_chain_usd","pct",None,1),
 ("DeFi","ETH","Stablecoins na rede (US$)","data/cripto/eth_indicadores.csv","stablecoins_usd","pct",None,1),
 ("Derivativos","ETH","DVOL (vol. implícita 30d)","data/cripto/derivativos_diarios.csv","dvol_eth","abs",None,1),
 ("Derivativos","ETH","Funding perpétuo (% a.a.)","data/cripto/derivativos_diarios.csv","funding_eth_aa_pct","abs",[(0,"vendedores pagam"),(15,"normal"),(99,"alavancagem comprada")],3),
 ("Preço e sentimento","SOL","Preço (US$)","data/cripto/sol_indicadores.csv","PriceUSD","pct",None,1),
 ("Preço e sentimento","SOL","SOL/BTC","data/cripto/ratios_diarios.csv","sol_btc","pct",None,1),
 ("DeFi","SOL","TVL da rede (US$)","data/cripto/sol_indicadores.csv","tvl_chain_usd","pct",None,1),
 ("DeFi","SOL","Stablecoins na rede (US$)","data/cripto/sol_indicadores.csv","stablecoins_usd","pct",None,1),
 ("Preço e sentimento","LINK","Preço (US$)","data/cripto/link_indicadores.csv","PriceUSD","pct",None,1),
 ("Preço e sentimento","LINK","LINK/BTC","data/cripto/ratios_diarios.csv","link_btc","pct",None,1),
 ("Valuation on-chain","LINK","MVRV","data/cripto/link_indicadores.csv","CapMVRVCur","abs",[(1.0,"abaixo do custo realizado"),(2.4,"faixa intermediária"),(99,"aquecido")],1),
 ("Atividade","LINK","Endereços ativos (média 7d)","data/cripto/link_indicadores.csv","AdrActCnt","pct",None,7),
 ("Preço e sentimento","SKY","Preço (US$)","data/cripto/sky_indicadores.csv","price_sky_usd","pct",None,1),
 ("Preço e sentimento","SKY","SKY/ETH","data/cripto/ratios_diarios.csv","sky_eth","pct",None,1),
 ("Valuation on-chain","SKY","MVRV do MKR","data/cripto/sky_indicadores.csv","CapMVRVCur","abs",[(1.0,"abaixo do custo realizado"),(2.4,"faixa intermediária"),(99,"aquecido")],1),
 ("DeFi","SKY","TVL do Sky Lending (US$)","data/cripto/sky_indicadores.csv","tvl_sky_lending_usd","pct",None,1),
]

def faixa(v, faixas):
    if not faixas or pd.isna(v): return ""
    return next((r for lim, r in faixas if v < lim), faixas[-1][1])

def linha(grupo, ativo, nome, arq, col, tipo, faixas, suav, cache):
    if arq not in cache: cache[arq] = pd.read_csv(arq) if os.path.exists(arq) else None
    d = cache[arq]
    if d is None or col not in d.columns: return None
    s = d[["data", col]].dropna().sort_values("data")
    if s.empty: return None
    x = s.set_index("data")[col].astype(float)
    if suav > 1: x = x.rolling(suav, min_periods=max(2, suav // 2)).mean().dropna()
    if x.empty: return None
    v = x.iloc[-1]
    def var(n):
        if len(x) <= n or pd.isna(x.iloc[-1 - n]): return np.nan
        a = x.iloc[-1 - n]
        return (v - a) if tipo == "abs" else ((v / a - 1) * 100 if a else np.nan)
    pct = float((x < v).mean() * 100)
    return dict(grupo=grupo, ativo=ativo, indicador=nome, valor=v, data=x.index[-1], var_1d=var(1), var_7d=var(7), var_30d=var(30),
                tipo_var=tipo, percentil=round(pct, 0), faixa=faixa(v, faixas))

def main():
    cache = {}; L = []
    for r in R:
        try:
            x = linha(*r, cache)
            if x: L.append(x)
        except Exception as e: print("falha", r[1], r[2], e)
    if os.path.exists("data/cripto/snapshots.csv"):
        s = pd.read_csv("data/cripto/snapshots.csv").iloc[-1]
        for col, nome, ativo in (("dominancia_btc_pct","Dominância do BTC (%)","BTC"),("dominancia_eth_pct","Dominância do ETH (%)","ETH"),
                                 ("put_call_oi_btc","Put/call OI BTC (Deribit)","BTC"),("put_call_oi_eth","Put/call OI ETH (Deribit)","ETH"),
                                 ("oi_futuros_btc_usd","OI futuros BTC (Deribit, contratos)","BTC")):
            if col in s and pd.notna(s[col]):
                L.append(dict(grupo="Derivativos", ativo=ativo, indicador=nome, valor=float(s[col]), data=str(s["data"])[:10], var_1d=np.nan, var_7d=np.nan, var_30d=np.nan, tipo_var="abs", percentil=np.nan, faixa="snapshot do dia"))
    res = pd.DataFrame(L)
    res.to_csv("data/cripto_resumo.csv", index=False, float_format="%.6g")
    print(len(res), "indicadores em data/cripto_resumo.csv")

if __name__ == "__main__":
    main()
