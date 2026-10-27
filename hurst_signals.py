"""Sinais de persistencia/antipersistencia para o scanner 1Listao (PBJ).
Uso no scanner: from hurst_signals import persistence_row; row.update(persistence_row(close_series))
Hipotese/base de analise, nao recomendacao de investimento.
"""
import numpy as np
import pandas as pd

def hurst_dfa(prices, min_box=8, max_frac=0.25, n_scales=12):
    """Hurst via DFA sobre log-retornos (H~0,5 aleatorio; >0,5 persistente; <0,5 antipersistente)."""
    p = np.asarray(pd.Series(prices).dropna(), dtype=float)
    r = np.diff(np.log(p))
    n = len(r)
    if n < 4 * min_box:
        return np.nan
    y = np.cumsum(r - r.mean())
    scales = np.unique(np.logspace(np.log10(min_box), np.log10(max(min_box + 1, int(n * max_frac))), n_scales).astype(int))
    F = []
    for s in scales:
        k = n // s
        seg = y[: k * s].reshape(k, s)
        t = np.arange(s)
        res = []
        for v in seg:
            c = np.polyfit(t, v, 1)
            res.append(np.mean((v - np.polyval(c, t)) ** 2))
        F.append(np.sqrt(np.mean(res)))
    slope = np.polyfit(np.log(scales), np.log(F), 1)[0]
    return float(slope)

def variance_ratio(prices, q):
    """VR(q) de Lo-MacKinlay: >1 persistente, <1 antipersistente."""
    r = np.diff(np.log(np.asarray(pd.Series(prices).dropna(), dtype=float)))
    if len(r) < 3 * q:
        return np.nan
    v1 = np.var(r, ddof=1)
    rq = pd.Series(r).rolling(q).sum().dropna().values
    return float(np.var(rq, ddof=1) / (q * v1))

def autocorr1(prices):
    r = np.diff(np.log(np.asarray(pd.Series(prices).dropna(), dtype=float)))
    return float(pd.Series(r).autocorr(1)) if len(r) > 10 else np.nan

def classify(h, hi=0.55, lo=0.45):
    if np.isnan(h):
        return "pendente"
    return "persistente" if h > hi else "antipersistente" if h < lo else "aleatorio"

def persistence_row(close):
    c = pd.Series(close).dropna()
    h120 = hurst_dfa(c.iloc[-121:]) if len(c) > 120 else np.nan
    h250 = hurst_dfa(c.iloc[-251:]) if len(c) > 250 else np.nan
    h120_prev = hurst_dfa(c.iloc[-141:-20]) if len(c) > 140 else np.nan
    dh = h120 - h120_prev if not np.isnan(h120) and not np.isnan(h120_prev) else np.nan
    return {
        "H120": round(h120, 3), "H250": round(h250, 3),
        "dH120_20d": round(dh, 3) if not np.isnan(dh) else np.nan,
        "regime_H120": classify(h120), "regime_H250": classify(h250),
        "VR5": round(variance_ratio(c, 5), 3), "VR10": round(variance_ratio(c, 10), 3),
        "AC1": round(autocorr1(c), 3),
        "alerta_descontinuidade": bool(not np.isnan(dh) and abs(dh) >= 0.10),
    }

if __name__ == "__main__":
    rng = np.random.default_rng(1)
    n = 600
    rw = 100 * np.exp(np.cumsum(rng.normal(0, .01, n)))
    # persistente: retornos AR(1) positivo; antipersistente: AR(1) negativo
    def ar(phi):
        e = rng.normal(0, .01, n); x = np.zeros(n)
        for i in range(1, n): x[i] = phi * x[i-1] + e[i]
        return 100 * np.exp(np.cumsum(x))
    for name, s in [("aleatorio", rw), ("persistente(phi=+.5)", ar(.5)), ("antipersistente(phi=-.5)", ar(-.5))]:
        print(name, persistence_row(s))
