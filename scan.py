# ==========================================================================
#  PBJ SCANNER — análise técnica + alarmes da 1Listão (arquivo único p/ Colab)
#  Cole tudo numa célula do Google Colab e rode (Shift+Enter).
#  Gera: alarmes impressos na tela + scan_results.csv (download automático).
# ==========================================================================
import importlib, subprocess, sys, re, time, warnings, datetime as dt
warnings.filterwarnings("ignore")

# ---- instala dependências se faltarem (Colab já tem pandas/numpy) ----
for pkg in ("yfinance", "pandas", "numpy"):
    try:
        importlib.import_module(pkg)
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", pkg])
import numpy as np
import pandas as pd
import yfinance as yf

# ==========================  CONFIGURAÇÃO  ================================
LIMIT = None          # ex.: 20 para testar só os 20 primeiros; None = todos
ONLY  = None          # ex.: ["NASDAQ:CLSK","NASDAQ:RIOT"]; None = todos
PERIOD = "2y"         # histórico baixado
MIN_SCORE_PRINT = 1   # só mostra ativos com score >= isto
# =========================================================================

# ==========================  1LISTÃO (embutida)  =========================
WATCHLIST = """
###BOLSAS,NASDAQ:TSLA,SP:SPX,NASDAQ:MCHI,TVC:IXIC,CBOE:INDA,BMFBOVESPA:IBOV.USD,BMFBOVESPA:IBOV,AMEX:EZA,AMEX:EWZ,AMEX:EWW,CME_MINI:ES1!,AMEX:EEM,CBOE:ECH,TVC:DJI,AMEX:BZQ,BMFBOVESPA:BOVA11,###AÇÕES DE CRIPTOGRAFIA,NASDAQ:RIOT,NASDAQ:MSTR,NASDAQ:IBIT,CBOE:HODL,CBOE:FBTC,CBOE:EZBC,NASDAQ:ETHA,NASDAQ:COIN,NASDAQ:CLSK,CBOE:BTCW,CBOE:BTCO,NASDAQ:BRRR,AMEX:BITB,CBOE:ARKB,AMEX:BMNR,OTC:GLASF,###CRIPTOS,BINANCE:ZILUSDT,BINANCE:XRPUSDT,BINANCE:USDTBRL,BITSTAMP:UNIUSD,COINBASE:UNIUSD,CRYPTOCAP:TOTALDEFI,CRYPTOCAP:TOTAL3,CRYPTOCAP:TOTAL2,CRYPTOCAP:TOTAL,BINANCE:SOLUSDT,BINANCE:SOLBTC,OKX:SKYUSDT,BITFINEX:SKYBTC,BINANCE:SHIBUSDT,BINANCE:SANDUSDT,BYBIT:POLUSDT,GATE:POLUSDT,CRYPTOCAP:OTHERS,BINANCE:NEARUSDT,BINANCE:NEARBTC,BINANCE:LUNAUSDT,COINBASE:LTCUSD,BINANCE:LINKUSDT,BINANCE:LINKBTC,CRYPTOCAP:LINK.D,CRYPTOCAP:LINK,BYBIT:LDOUSDT,HTX:IMXUSDT,BINANCE:ILVUSDT,BINANCE:GRTUSDT,POLONIEX:FLOKIUSDT,BINANCE:FETUSDT,BITSTAMP:ETHUSD,COINBASE:ETHDVOL,BINANCE:ETHBTC,BINANCE:ETHBRL,CRYPTOCAP:ETH.D,CRYPTOCAP:ETH,KUCOIN:ERGUSDT,BINANCE:ENJUSDT,KUCOIN:ELONUSDT,BINANCE:EGLDUSDT,COINBASE:DVOL,BINANCE:DOTUSDT,BINANCE:DCRUSDT,OKX:CROUSDT,BINANCE:CAKEUSDT,BITFINEX:BTCUSDSHORTS,BITFINEX:BTCUSDLONGS,BITSTAMP:BTCUSD,COINBASE:BTCUSD,BINANCE:BTCUSD,BINANCE:BTCBRL,CRYPTOCAP:BTC.D,CRYPTOCAP:BTC,BINANCE:AXSUSDT,BINANCE:AVAXUSDT,BINANCE:AUDIOUSDT,COINEX:APEUSDT,BINANCE:ADAUSDT,BINANCE:AAVEUSDT,BINANCE:AUDIOBTC,BINANCE:MANAUSD,BINANCE:ILVBTC,BINANCE:FTMUSDT,BINANCE:EGLDBTC,BINANCE:MKRUSDT,BINANCE:FTMBTC,BINANCE:AXSBTC,BINANCE:ROSEBTC,BINANCE:SCRTBTC,BINANCE:SCRTUSD,BINANCE:LRCUSDT,BITFINEX:WILDUSD,BITFINEX:XTZUSD,###METAIS PRECIOSOS E DERIVADOS,EASYMARKETS:XPTUSD,SAXO:XPTUSD,OANDA:XAUUSD,BITFINEX:XAUTUSD,AMEX:SLV,TVC:SILVER,AMEX:SILJ,AMEX:SIL,NYSE:SBSW,AMEX:PLTM,TVC:PLATINUM/TVC:SILVER,TVC:PLATINUM/TVC:GOLD,BINANCE:PAXGUSDT,GEMINI:PAXGUSDC,COINBASE:PAXGUSDC,TVC:PALLADIUM,AMEX:PALL,NYSE:PAAS,OTC:IMPUY,AMEX:IAU,TVC:GOLD/SP:SPX,TVC:GOLD/TVC:SILVER,TVC:GOLD/COMEX:HG1!,TVC:GOLD/TVC:DXY,TVC:GOLD/FRED:CPIAUCSL,TVC:GOLD,AMEX:GDXJ,AMEX:GDX,COMEX:GC1!,OTC:ANGPY,OTC:AGPPF,###INDICE DE MEDO,CBOE:VXX,CBOE:VVIX,TVC:VIX,CBOE:VIX,###TAXA DE JUROS,TVC:US30Y-TVC:US05Y,TVC:US30Y-TVC:US02Y,TVC:US30Y-TVC:US01Y,TVC:US30Y,TVC:US20Y,TVC:US10Y-TVC:US05Y,TVC:US10Y-TVC:US03MY,TVC:US10Y-TVC:US02Y,TVC:US10Y-TVC:US01Y,TVC:US10Y,TVC:US07Y,TVC:US05Y-TVC:US02Y,TVC:US05Y,TVC:US03MY,TVC:US02Y,TVC:US01Y,TVC:US01MY,TVC:JP10Y-TVC:JP02Y,TVC:JP10Y,TVC:JP02Y,COMEX:HG1!,TVC:GB10Y-TVC:GB02Y,TVC:GB10Y,TVC:GB02Y,NYSE:FCX,BMFBOVESPA:DI1F2035-BMFBOVESPA:DAPK2035,BMFBOVESPA:DI1F2035,BMFBOVESPA:DI1F2034,BMFBOVESPA:DI1F2033,BMFBOVESPA:DI1F2032,BMFBOVESPA:DI1F2031,BMFBOVESPA:DI1F2030-BMFBOVESPA:DAPQ2030,BMFBOVESPA:DI1F2030,BMFBOVESPA:DI1F2029,BMFBOVESPA:DI1F2028,BMFBOVESPA:DI1F2027-BMFBOVESPA:DAPK2027,BMFBOVESPA:DI1F2027,BMFBOVESPA:DI1F2026-BMFBOVESPA:DAPQ2026,BMFBOVESPA:DI1F2026,BMFBOVESPA:DI1F2025,TVC:DE10Y-TVC:DE02Y,TVC:DE10Y,TVC:DE02Y,BMFBOVESPA:DAPQ2050,BMFBOVESPA:DAPQ2040,BMFBOVESPA:DAPQ2032,BMFBOVESPA:DAPQ2030,BMFBOVESPA:DAPQ2028,BMFBOVESPA:DAPK2055,BMFBOVESPA:DAPK2045,BMFBOVESPA:DAPK2035,BMFBOVESPA:DAPK2033,BMFBOVESPA:DAPK2029,BMFBOVESPA:DAPK2027,BMFBOVESPA:DAPF2026,TVC:BR10Y,###MOEDAS,FX:USDTRY,RUS:USDRUB_TOD,FX_IDC:USDJPY,FX_IDC:USDEUR,FX:USDCNH,FX_IDC:USDCLP,FX_IDC:USDBRL,FX_IDC:USDARS,CBOE:HEEM,FX:GBPUSD,AMEX:FXF,TVC:EXY,FX_IDC:EURBRL,TVC:DXY,BMFBOVESPA:DOL1!,FX_IDC:CLPUSD,TVC:AXY,CME:6L1!,CME:GE1!,###URÂNIO,COMEX:UXF2022,COMEX:UX2!,COMEX:UX1!,AMEX:URA,AMEX:UEC,LSIN:KAP,AMEX:DNN,NYSE:CCJ,###COMMODITIES,CBOT:ZS1!,CBOT:ZC1!,CBOT_MINI:XW1!,BMFBOVESPA:VALE3,NYSE:VALE,TVC:UKOIL,TVC:TRJEFFCRB,SP:SPGSCI,NYMEX:NG1!,AMEX:GSG,SGX:FEF2!,AMEX:DBC,AMEX:CPER,AMEX:CORN,NYMEX:CL1!,MCX:ALUMINIUM1!,###BONDS,NASDAQ:TLT,AMEX:TIP,AMEX:STIP,AMEX:SPIB,TVC:MOVE,NASDAQ:IGIB,NASDAQ:IEF,AMEX:HYG,NASDAQ:BND,AMEX:BIL,NASDAQ:SHV,###REITERS,NYSE:WPC,NYSE:STAG,NYSE:PLD,NYSE:IIPR,NYSE:GTY,NASDAQ:GLPI,NYSE:EXR,NASDAQ:EQIX,NYSE:DLR,NYSE:CUBE,NASDAQ:CRSPRE1,NYSE:CHCT,NYSE:ARE,NYSE:AMT,###FII BRASIL,BMFBOVESPA:VSLH11,BMFBOVESPA:VILG11,BMFBOVESPA:RECR11,BMFBOVESPA:RBVA11,BMFBOVESPA:LVBI11,BMFBOVESPA:KNCR11,BMFBOVESPA:KIVO11,BMFBOVESPA:IFIX,BMFBOVESPA:HGRU11,BMFBOVESPA:HCTR11,BMFBOVESPA:CXTL11,BMFBOVESPA:CXCO11,BMFBOVESPA:CXCI11,BMFBOVESPA:CXAG11,BMFBOVESPA:CPTS11,BMFBOVESPA:CNES11,BMFBOVESPA:BRCR11,BMFBOVESPA:BCRI11,OTC:SIVBQ,BMFBOVESPA:SRVD11,BMFBOVESPA:RELG11,###STOCKS BRASIL,NASDAQ:XP,AMEX:USO,TVC:US10,BMFBOVESPA:SMAL11,BMFBOVESPA:SIMH3,BMFBOVESPA:PRIO3,BMFBOVESPA:PETR3,NYSE:PBR,NASDAQ:NFLX,BMFBOVESPA:MGLU3,NASDAQ:META,BMFBOVESPA:JHSF3,BMFBOVESPA:IRBR3,BMFBOVESPA:INEP4,BMFBOVESPA:IMOB,TVC:HGX,BMFBOVESPA:FESA4,BMFBOVESPA:ETER3,BMFBOVESPA:ESPA3,BMFBOVESPA:DEXP3,BMFBOVESPA:CXSE3,BMFBOVESPA:CSNA3,BMFBOVESPA:COGN3,BMFBOVESPA:CMIN3,BMFBOVESPA:CASH3,BMFBOVESPA:BERU39,BMFBOVESPA:BBAS3,BMFBOVESPA:AZEV4,NASDAQ:AMZN,BMFBOVESPA:AMBP3,BMFBOVESPA:ELET3,NYSE:AXIA,BMFBOVESPA:AZUL54,BMFBOVESPA:TRAD3,HKEX:3333,BMFBOVESPA:BPAN4,BMFBOVESPA:BIDI11,###ECONOMY,FRED:UNRATE,FRED:RRPONTSYD,FRED:MYAGM2JPM189S,FRED:MYAGM2EZM196N,FRED:MYAGM2CNM189N,FRED:M2SL,FRED:FEDFUNDS,ECONOMICS:CNM2,ECONOMICS:BRM2,FRED:BOGMBASE,###SETORES EUA,AMEX:XLY,AMEX:XLV,AMEX:XLU,AMEX:XLRE,AMEX:XLP,AMEX:XLK,AMEX:XLI,AMEX:XLF,AMEX:XLE,AMEX:XLC,AMEX:XLB,###CANNABIS,NASDAQ:ZION,AMEX:YOLO,BITFINEX:XAGUST.P,OKX:XAGUSDT.P,BMFBOVESPA:WIN1!,NYSE:WAL,FX_IDC:USDINR,ACTIVTRADES:USDBRL,ECONOMICS:USCCPI,NYSE:USB,NASDAQ:TLRY,NYSE:TFC,NYSE:STT,AMEX:SPPP,NASDAQ:SOUN,FRED:SOFRVOL,FRED:SOFRINDEX,FRED:SOFR30DAYAVG,FRED:SOFR,BMFBOVESPA:SLCE3,BYBIT:SKYUSDT,FRED:SAHMCURRENT,BMFBOVESPA:RURA11,NASDAQ:POET,NASDAQ:PLTR,NYSE:PATH,OTC:NLCP,NYSE:MTB,AMEX:MSOS,NYSE:MCB,DEFILLAMA:MATIC_TVL,AMEX:KWEB,NYSE:KEY,CRYPTO:KAGUSD,FX_IDC:JPYAUD,AMEX:ITEQ,NASDAQ:INTR,NASDAQ:IMCC,OTC:GTBIF,AMEX:FXI,NYSE:FRC,AMEX:EWY,AMEX:EWH,FRED:DFII10,NYSE:DB,BMFBOVESPA:DAPQ2060,OTC:CURLF,BMFBOVESPA:CSED3,NASDAQ:CRON,NASDAQ:CRDO,AMEX:COPX,NYSE:COF,NYSE:CNNE,NYSE:CHGG,NASDAQ:CGC,NYSE:CFG,GLASSNODE:BTC_HASHRATE,ECONOMICS:BRTOT,ECONOMICS:BRM1,BMFBOVESPA:BRKM5,NYSE:BRK.B,BMFBOVESPA:BRCO11,TVC:BR05Y,NYSE:BNY,BINANCE:BNBUSDT,NYSE:BKSY,NASDAQ:BIDU,BMFBOVESPA:BBDC4,BMFBOVESPA:BBDC3,NYSE:BABA,BMFBOVESPA:AMER3,BMFBOVESPA:AMAR3,NYSE:AI,NASDAQ:AFCG,NASDAQ:ACB,BMFBOVESPA:ABEV3,NASDAQ:AAOI,CBOE:TOKE,OTC:TCNNF,BMFBOVESPA:BRFS3,BMFBOVESPA:OIBR3,BMFBOVESPA:OIBR4,NYSE:NSA,NASDAQ:FITB,NASDAQ:PNFP,ECONOMICS:USCPMI,ECONOMICS:JPNMPMI,ECONOMICS:CNNMPMI,ECONOMICS:BRCOMPPMI,BITMART:KAGUSDT,###AGRO SOFTS,ICEUS:SB1!,ICEUS:OJ1!,ICEUS:KC1!,BMFBOVESPA:ETH1!,ICEUS:CT1!,BMFBOVESPA:BGI1!,###BOLSAS MUNDO,FTSE:UKX,STOXX:SX5E,NSE:NIFTY,TVC:NI225,HSI:HSI,XETR:DAX,FX:CHN50,###IA,NASDAQ:NVDA,NASDAQ:MSFT,NASDAQ:GOOGL,NASDAQ:AVGO,NYSE:TSM,NASDAQ:MU,NASDAQ:AMD,NYSE:ORCL,NASDAQ:ASML,NASDAQ:AMAT,NASDAQ:LRCX,NYSE:DELL,NASDAQ:ARM,NYSE:ANET,NASDAQ:MRVL,NYSE:VRT,NASDAQ:ALAB,NYSE:COHR,NASDAQ:NBIS,NASDAQ:CRWV,NASDAQ:IREN,NASDAQ:SMCI,NASDAQ:APLD,NASDAQ:INOD,NYSE:BBAI,NASDAQ:RMBS,NYSE:CLS,NASDAQ:CBRS,NASDAQ:TSEM,NASDAQ:LSCC,NASDAQ:TEM,NYSE:FN,###CANNABIS BLOCO,OTC:GTBIF,OTC:TCNNF,OTC:CURLF,OTC:CRLBF,OTC:VRNOF,NASDAQ:TLRY,NASDAQ:CGC,NASDAQ:SNDL,NYSE:IIPR,###TERRAS RARAS,NYSE:MP,AMEX:UUUU,NASDAQ:USAR,OTC:LYSDY,AMEX:REMX,###URANIO EXTRA,AMEX:URNM,NYSE:NXE,AMEX:LEU,OTC:SRUUF,###IA CHINA EXTRA,OTC:TCEHY,###MINERADORAS BTC IA,NASDAQ:CIFR,NASDAQ:WULF,NASDAQ:HUT,NASDAQ:CORZ,NASDAQ:MARA,###OURO E PRATA MINERADORAS,NYSE:NEM,NYSE:B,NYSE:AEM,NYSE:WPM,NYSE:FNV,NYSE:HL,NYSE:CDE,NYSE:KGC,NYSE:GFI,NYSE:HMY,###PLATINOIDES,TVC:PLATINUM,AMEX:PLG
"""

# ==========================  MAPEADOR  ===================================
INDEX_MAP = {"SP:SPX": "^GSPC", "TVC:IXIC": "^IXIC", "TVC:DJI": "^DJI",
             "FTSE:UKX": "^FTSE", "STOXX:SX5E": "^STOXX50E", "NSE:NIFTY": "^NSEI",
             "TVC:NI225": "^N225", "HSI:HSI": "^HSI", "XETR:DAX": "^GDAXI",
             "BMFBOVESPA:IBOV": "^BVSP"}
SPECIAL_MAP = {"TVC:GOLD": "GC=F", "OANDA:XAUUSD": "GC=F", "COMEX:GC1!": "GC=F",
               "TVC:SILVER": "SI=F", "TVC:PLATINUM": "PL=F", "AMEX:PLTM": "PPLT",
               "TVC:PALLADIUM": "PA=F", "COMEX:HG1!": "HG=F", "NYMEX:CL1!": "CL=F",
               "NYMEX:NG1!": "NG=F", "TVC:UKOIL": "BZ=F", "CBOT:ZS1!": "ZS=F",
               "CBOT:ZC1!": "ZC=F", "CBOT_MINI:XW1!": "ZW=F", "ICEUS:KC1!": "KC=F",
               "ICEUS:SB1!": "SB=F", "ICEUS:OJ1!": "OJ=F", "ICEUS:CT1!": "CT=F",
               "CME_MINI:ES1!": "ES=F", "TVC:VIX": "^VIX", "CBOE:VIX": "^VIX",
               "CBOE:VXX": "VXX", "CBOE:VVIX": "^VVIX", "TVC:DXY": "DX-Y.NYB",
               "TVC:US10Y": "^TNX", "TVC:US30Y": "^TYX", "TVC:US05Y": "^FVX",
               "TVC:US03MY": "^IRX"}
CRYPTO_EXCH = {"BINANCE", "COINBASE", "BITSTAMP", "OKX", "BYBIT", "KUCOIN", "HTX",
               "GATE", "BITFINEX", "GEMINI", "POLONIEX", "COINEX", "BITMART", "CRYPTO"}
QUOTES = ["USDT", "USDC", "USD", "BRL"]
US_EQ_EXCH = {"NASDAQ", "NYSE", "AMEX", "CBOE", "OTC", "BATS", "ARCA"}
SKIP_PREFIXES = ("FRED:", "ECONOMICS:", "CRYPTOCAP:", "DEFILLAMA:", "GLASSNODE:",
                 "COINBASE:DVOL", "COINBASE:ETHDVOL")


def _crypto_base(tv):
    sym = tv.split(":", 1)[1]
    for q in QUOTES:
        if sym.endswith(q) and len(sym) > len(q):
            return sym[:-len(q)]
    return sym


def map_symbol(tv):
    tv = tv.strip()
    if not tv or tv.startswith("###"):
        return None
    if tv.startswith(SKIP_PREFIXES):
        return {"tv": tv, "yf": None}
    if "/" in tv or re.search(r"[A-Z0-9]:[A-Z0-9]+-[A-Z]+:", tv) or ":" not in tv:
        return {"tv": tv, "yf": None}
    exch, sym = tv.split(":", 1)
    if tv in INDEX_MAP:
        return {"tv": tv, "yf": INDEX_MAP[tv], "kind": "index"}
    if tv in SPECIAL_MAP:
        return {"tv": tv, "yf": SPECIAL_MAP[tv], "kind": "commodity/rate"}
    if exch == "BMFBOVESPA":
        if re.match(r"^(DI1F|DAP|DOL|WIN|WDO|IND|BGI|ETH|CCM|ICF)\w*\d", sym) or sym.endswith("1!"):
            return {"tv": tv, "yf": None}
        if sym in {"IFIX", "IMOB", "IMAT", "IBOV.USD"}:
            return {"tv": tv, "yf": None}
        return {"tv": tv, "yf": f"{sym}.SA", "kind": "b3"}
    if exch in {"FX", "FX_IDC", "ACTIVTRADES", "RUS", "SAXO", "EASYMARKETS"}:
        if re.match(r"^[A-Z]{6}$", sym):
            return {"tv": tv, "yf": f"{sym}=X", "kind": "fx"}
        return {"tv": tv, "yf": None}
    if exch in CRYPTO_EXCH:
        if sym.endswith("BTC"):
            return {"tv": tv, "yf": f"{sym[:-3]}-USD", "kind": "crypto_btc", "base": sym[:-3]}
        if sym.endswith("BRL"):
            return {"tv": tv, "yf": None}
        b = _crypto_base(tv)
        return {"tv": tv, "yf": f"{b}-USD", "kind": "crypto", "base": b}
    if exch in US_EQ_EXCH:
        if sym.endswith("1!"):
            return {"tv": tv, "yf": None}
        return {"tv": tv, "yf": sym.replace(".", "-"), "kind": "us_equity"}
    return {"tv": tv, "yf": None}


def parse_watchlist(text):
    tokens = [t.strip() for t in text.replace("\n", ",").split(",") if t.strip()]
    cat, out, seen = "SEM CATEGORIA", [], set()
    for t in tokens:
        if t.startswith("###"):
            cat = t.lstrip("#").strip(); continue
        if t in seen:
            continue
        seen.add(t); out.append((cat, t))
    return out


# ==========================  INDICADORES  ================================
def ema(s, n): return s.ewm(span=n, adjust=False).mean()


def rsi(s, n=14):
    d = s.diff(); up = d.clip(lower=0); dn = -d.clip(upper=0)
    ru = up.ewm(alpha=1 / n, adjust=False).mean(); rd = dn.ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + ru / rd.replace(0, np.nan))


def macd(s, f=12, sl=26, sg=9):
    m = ema(s, f) - ema(s, sl); si = ema(m, sg); return m, si, m - si


def atr(df, n=14):
    h, l, c = df["High"], df["Low"], df["Close"]; pc = c.shift()
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def bollinger(s, n=20, k=2):
    mid = s.rolling(n).mean(); sd = s.rolling(n).std()
    up, lo = mid + k * sd, mid - k * sd
    return mid, up, lo, (up - lo) / mid * 100


def obv(df):
    return (np.sign(df["Close"].diff()).fillna(0) * df["Volume"].fillna(0)).cumsum()


def _slope(s, n):
    y = s.dropna().tail(n)
    if len(y) < n or y.iloc[0] == 0: return np.nan
    return (y.iloc[-1] - y.iloc[0]) / abs(y.iloc[0]) * 100


WEIGHT = {"ROMPIMENTO_ALTA": 5, "ROMPIMENTO_BAIXA": 5, "NOVA_MAX_52S": 4,
          "NOVA_MIN_52S": 4, "ACUMULACAO": 5, "DISTRIBUICAO": 4, "SQUEEZE": 2,
          "GOLDEN_CROSS": 4, "DEATH_CROSS": 4, "MACD_CRUZOU_ALTA": 2,
          "MACD_CRUZOU_BAIXA": 2, "RECLAMOU_EMA200": 3, "PERDEU_EMA200": 3,
          "VOLUME_ANORMAL": 2, "RSI_SOBREVENDIDO": 2, "RSI_SOBRECOMPRADO": 2,
          "DIVERG_ALTA_RSI": 3, "DIVERG_BAIXA_RSI": 3}


def analyze(df):
    df = df.dropna(subset=["Close"]).copy()
    if len(df) < 60:
        return None, []
    c, h, l, v = df["Close"], df["High"], df["Low"], df["Volume"]
    close = float(c.iloc[-1]); prev = float(c.iloc[-2])
    chg = (close / prev - 1) * 100 if prev else np.nan
    e50, e200 = ema(c, 50), ema(c, 200)
    r = rsi(c); _, _, mh = macd(c); _, _, _, bbw = bollinger(c); ob = obv(df)
    rsi_now = float(r.iloc[-1]); hist_now, hist_prev = float(mh.iloc[-1]), float(mh.iloc[-2])
    bbw_now = float(bbw.iloc[-1])
    bbw_pct = float((bbw.tail(120) < bbw_now).mean()) if bbw.tail(120).notna().sum() > 30 else np.nan
    hi20, lo20 = float(h.iloc[-21:-1].max()), float(l.iloc[-21:-1].min())
    w = min(252, len(df)); hi52, lo52 = float(h.tail(w).max()), float(l.tail(w).min())
    rng = (close - lo52) / (hi52 - lo52) if hi52 > lo52 else 0.5
    avgv = float(v.tail(20).mean()) if v.tail(20).notna().sum() else np.nan
    relvol = (float(v.iloc[-1]) / avgv) if avgv else np.nan
    obv_sl = _slope(ob, 20)
    m = dict(close=close, chg=chg, rsi=rsi_now, bbw_pct=bbw_pct, hi52=hi52, lo52=lo52,
             rng_pos=rng, relvol=relvol, obv_slope=obv_sl,
             dist_hi52=(close / hi52 - 1) * 100, dist_lo52=(close / lo52 - 1) * 100)
    # retornos em % (1, 5, 21, 63 e 252 sessoes); NaN se faltar historico
    for _n in (1, 5, 21, 63, 252):
        m[f"ret_{_n}d"] = (close / float(c.iloc[-1 - _n]) - 1) * 100 if len(c) > _n else np.nan
    s = []; rv = relvol if not np.isnan(relvol) else 1.0
    if close > hi20 and rv > 1.3: s.append("ROMPIMENTO_ALTA")
    if close < lo20 and rv > 1.3: s.append("ROMPIMENTO_BAIXA")
    if close >= hi52 * 0.995: s.append("NOVA_MAX_52S")
    if close <= lo52 * 1.005: s.append("NOVA_MIN_52S")
    if (not np.isnan(bbw_pct)) and bbw_pct < 0.12:
        s.append("SQUEEZE")
        if obv_sl > 0 and rng < 0.5: s.append("ACUMULACAO")
        if obv_sl < 0 and rng > 0.5: s.append("DISTRIBUICAO")
    if rsi_now < 30: s.append("RSI_SOBREVENDIDO")
    elif rsi_now > 70: s.append("RSI_SOBRECOMPRADO")
    if hist_prev <= 0 < hist_now: s.append("MACD_CRUZOU_ALTA")
    if hist_prev >= 0 > hist_now: s.append("MACD_CRUZOU_BAIXA")
    cr = e50 - e200
    if cr.iloc[-6] < 0 < cr.iloc[-1]: s.append("GOLDEN_CROSS")
    if cr.iloc[-6] > 0 > cr.iloc[-1]: s.append("DEATH_CROSS")
    ab = c > e200
    if (not ab.iloc[-4]) and ab.iloc[-1]: s.append("RECLAMOU_EMA200")
    if ab.iloc[-4] and (not ab.iloc[-1]): s.append("PERDEU_EMA200")
    if rv > 2.5: s.append("VOLUME_ANORMAL")
    if len(df) > 40:
        if close < float(c.iloc[-21]) and rsi_now > float(r.iloc[-21]) and rsi_now < 50:
            s.append("DIVERG_ALTA_RSI")
        if close > float(c.iloc[-21]) and rsi_now < float(r.iloc[-21]) and rsi_now > 50:
            s.append("DIVERG_BAIXA_RSI")
    return m, s


def score(sigs): return sum(WEIGHT.get(x, 0) for x in sigs)


# ==========================  EXECUÇÃO  ===================================
def chunked(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def run():
    items = parse_watchlist(WATCHLIST)
    uni, seen = [], set()
    for cat, tv in items:
        m = map_symbol(tv)
        if not m or not m.get("yf") or m["yf"] in seen:
            continue
        seen.add(m["yf"]); uni.append((cat, tv, m["yf"], m.get("kind", ""), m.get("base", "")))
    if ONLY:
        uni = [r for r in uni if r[2] in ONLY or r[1] in ONLY]
    if LIMIT:
        uni = uni[:LIMIT]
    tickers = [r[2] for r in uni]
    print(f"Baixando {len(tickers)} tickers (de {len(items)} símbolos da 1Listão)...")
    data = {}
    for i, ch in enumerate(chunked(tickers, 40)):
        try:
            d = yf.download(ch, period=PERIOD, interval="1d", auto_adjust=True,
                            group_by="ticker", progress=False, threads=True)
            for t in ch:
                try:
                    df = (d if len(ch) == 1 else d[t]).dropna(how="all")
                    if len(df) >= 60:
                        data[t] = df
                except Exception:
                    pass
        except Exception as e:
            print("  erro lote:", e)
        print(f"  lote {i+1}/{(len(tickers)-1)//40+1}: total baixado {len(data)}")
        time.sleep(1)

    rows = []
    for cat, tv, yft, kind, base in uni:
        df = data.get(yft)
        if df is None:
            continue
        try:
            m, s = analyze(df)
        except Exception:
            continue
        if m is None:
            continue
        rows.append(dict(cat=cat, tv=tv, yf=yft, score=score(s),
                         signals="|".join(s), **m))
    if not rows:
        print("\nNada baixado — verifique a internet do ambiente.")
        return
    res = pd.DataFrame(rows).sort_values("score", ascending=False)
    res.to_csv("scan_results.csv", index=False)
    import os
    os.makedirs("history", exist_ok=True)
    stamp = dt.date.today().strftime("%Y-%m-%d")
    res.to_csv(f"history/scan_{stamp}.csv", index=False)
    report(res)            # imprime no log do Actions
    report_md(res)         # grava relatorio.md
    return res


def report(res):
    today = dt.date.today().strftime("%d/%m/%Y")
    has = lambda t: res["signals"].str.contains(t, na=False)
    print("\n" + "=" * 70)
    print(f"  SCANNER TÉCNICO 1LISTÃO — {today}")
    print(f"  Analisados: {len(res)} | Com alarme: {(res['score']>0).sum()}")
    print("=" * 70)

    def sec(title, mask, extra=lambda r: ""):
        sub = res[mask]
        if len(sub) == 0:
            return
        print(f"\n### {title} ({len(sub)})")
        for _, r in sub.iterrows():
            tk = r.tv.split(':')[-1]
            line = f"  {tk:<12} {r.close:>10,.2f}  ({r.chg:+5.1f}%)  RSI {r.rsi:>3.0f}"
            e = extra(r)
            print(line + ("  " + e if e else ""))

    sec("ROMPIMENTO DE ALTA", has("ROMPIMENTO_ALTA"),
        lambda r: f"vol {r.relvol:.1f}x | {r.dist_hi52:+.0f}% da máx52s")
    sec("ROMPIMENTO DE BAIXA", has("ROMPIMENTO_BAIXA"),
        lambda r: f"vol {r.relvol:.1f}x")
    sec("NOVA MÁXIMA 52 SEMANAS", has("NOVA_MAX_52S"))
    sec("NOVA MÍNIMA 52 SEMANAS", has("NOVA_MIN_52S"))
    sec("ACUMULAÇÃO (squeeze+OBV↑, fundo range)", has("ACUMULACAO"),
        lambda r: f"BB {r.bbw_pct*100:.0f}ºpct | range {r.rng_pos*100:.0f}%")
    sec("DISTRIBUIÇÃO (squeeze+OBV↓, topo range)", has("DISTRIBUICAO"))
    sec("SQUEEZE (rompimento iminente)",
        has("SQUEEZE") & ~has("ACUMULACAO") & ~has("DISTRIBUICAO"),
        lambda r: f"BB {r.bbw_pct*100:.0f}ºpct")
    sec("GOLDEN CROSS", has("GOLDEN_CROSS"))
    sec("DEATH CROSS", has("DEATH_CROSS"))
    sec("RECONQUISTOU EMA200", has("RECLAMOU_EMA200"))
    sec("PERDEU EMA200", has("PERDEU_EMA200"))
    sec("MACD CRUZOU P/ ALTA", has("MACD_CRUZOU_ALTA"))
    sec("MACD CRUZOU P/ BAIXA", has("MACD_CRUZOU_BAIXA"))
    sec("DIVERGÊNCIA DE ALTA (RSI)", has("DIVERG_ALTA_RSI"))
    sec("DIVERGÊNCIA DE BAIXA (RSI)", has("DIVERG_BAIXA_RSI"))
    sec("VOLUME ANORMAL (>2.5x)", has("VOLUME_ANORMAL"), lambda r: f"vol {r.relvol:.1f}x")
    sec("RSI SOBREVENDIDO (<30)", has("RSI_SOBREVENDIDO"))
    sec("RSI SOBRECOMPRADO (>70)", has("RSI_SOBRECOMPRADO"))
    print("\n(CSV completo: scan_results.csv)")



def report_md(res):
    today = dt.date.today().strftime("%d/%m/%Y")
    has = lambda t: res["signals"].str.contains(t, na=False)
    tk = lambda s: str(s).split(":")[-1]
    L = [f"# Scanner tecnico 1Listao - {today}",
         f"",
         f"Analisados: **{len(res)}** | Com alarme: **{(res['score']>0).sum()}**",
         f"",
         f"> Ruido conhecido: BIL/SHV/STIP (tipo-caixa) e alts sub-centavo (ELON/ZIL/WILD) podem aparecer com sinal espurio.",
         f""]
    def sec(title, mask, extra=lambda r: ""):
        sub = res[mask]
        if len(sub) == 0:
            return
        L.append(f"\n## {title} ({len(sub)})\n")
        for _, r in sub.sort_values("score", ascending=False).iterrows():
            e = extra(r)
            L.append(f"- **{tk(r['tv'])}** {r['close']:,.2f} ({r['chg']:+.1f}%) RSI {r['rsi']:.0f}" + (f" - {e}" if e else ""))
    sec("Rompimento de ALTA", has("ROMPIMENTO_ALTA"), lambda r: f"vol {r['relvol']:.1f}x, {r['dist_hi52']:+.0f}% da max52s")
    sec("Rompimento de BAIXA", has("ROMPIMENTO_BAIXA"), lambda r: f"vol {r['relvol']:.1f}x")
    sec("Nova maxima 52 semanas", has("NOVA_MAX_52S"))
    sec("Nova minima 52 semanas", has("NOVA_MIN_52S"))
    sec("ACUMULACAO (squeeze + OBV sobe, fundo range)", has("ACUMULACAO"), lambda r: f"BB {r['bbw_pct']*100:.0f}pct, range {r['rng_pos']*100:.0f}%")
    sec("DISTRIBUICAO (squeeze + OBV cai, topo range)", has("DISTRIBUICAO"))
    sec("Squeeze (rompimento iminente)", has("SQUEEZE") & ~has("ACUMULACAO") & ~has("DISTRIBUICAO"))
    sec("Golden cross", has("GOLDEN_CROSS"))
    sec("Death cross", has("DEATH_CROSS"))
    sec("Reconquistou EMA200", has("RECLAMOU_EMA200"))
    sec("Perdeu EMA200", has("PERDEU_EMA200"))
    sec("MACD cruzou p/ alta", has("MACD_CRUZOU_ALTA"))
    sec("MACD cruzou p/ baixa", has("MACD_CRUZOU_BAIXA"))
    sec("Divergencia de ALTA (RSI)", has("DIVERG_ALTA_RSI"))
    sec("Divergencia de BAIXA (RSI)", has("DIVERG_BAIXA_RSI"))
    sec("Volume anormal", has("VOLUME_ANORMAL"), lambda r: f"vol {r['relvol']:.1f}x")
    sec("RSI sobrevendido (<30)", has("RSI_SOBREVENDIDO"))
    sec("RSI sobrecomprado (>70)", has("RSI_SOBRECOMPRADO"))
    open("relatorio.md","w",encoding="utf-8").write("\n".join(L))


if __name__ == "__main__":
    run()
