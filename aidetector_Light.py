#!/usr/bin/env python3
# detector.py
# AI detector migliorato — combina perplessità + feature stilistiche
# Legge il testo dalla clipboard (pyperclip). Se vuota, chiede di incollare nel terminale.

import math
import re
import sys
import statistics
from collections import Counter
from typing import List

try:
    import pyperclip
except Exception:
    print("pyperclip non trovato. Per favore installalo: pip install pyperclip")
    pyperclip = None

# -------------------------
# Funzioni di utilità
# -------------------------

def read_text_from_clipboard_or_stdin():
    text = ""
    if pyperclip:
        try:
            text = pyperclip.paste()
            if text and text.strip():
                print("Testo letto dalla clipboard.")
                return text
        except Exception:
            pass
    # fallback: leggere da stdin
    print("Clipboard vuota o non disponibile.")
    print("Incolla il testo nel terminale e poi premi Ctrl+Z seguito da Invio (Windows) o Ctrl+D (Unix) per terminare:")
    try:
        lines = sys.stdin.read()
        return lines
    except Exception:
        return ""

def split_sentences(text: str) -> List[str]:
    # divisione semplice in frasi
    # usa punteggiatura come .,!?; e newline
    s = re.split(r'(?<=[\.\!\?;])\s+|\n+', text.strip())
    s = [x.strip() for x in s if x and len(x.strip())>0]
    return s

def type_token_ratio(tokens: List[str]) -> float:
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)

def avg_sentence_length(sentences: List[str]) -> float:
    if not sentences:
        return 0.0
    lens = [len(s.split()) for s in sentences]
    return statistics.mean(lens) if lens else 0.0

def sentence_length_variance(sentences: List[str]) -> float:
    if not sentences or len(sentences) < 2:
        return 0.0
    lens = [len(s.split()) for s in sentences]
    return statistics.pvariance(lens)

def punctuation_ratio(text: str) -> float:
    if not text:
        return 0.0
    punct = sum(1 for ch in text if ch in ".,;:!?\"'()[]{}")
    return punct / max(1, len(text))

def repetition_score(tokens: List[str], n=3) -> float:
    # conta n-gram ripetuti; più alto => più ripetizione (tipica di testi generati)
    if len(tokens) < n:
        return 0.0
    ngrams = [' '.join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]
    c = Counter(ngrams)
    repeated = sum(v for v in c.values() if v > 1)
    return repeated / max(1, len(ngrams))

# -------------------------
# Perplessità (perplexity) con GPT-2
# -------------------------

class PerplexityEstimator:
    def __init__(self, model_name="gpt2"):
        if GPT2LMHeadModel is None or GPT2TokenizerFast is None or torch is None:
            raise RuntimeError("transformers/torch non disponibili. Installa i pacchetti richiesti.")
        print(f"Caricamento modello {model_name} (potrebbe richiedere memoria)...")
        self.tokenizer = GPT2TokenizerFast.from_pretrained(model_name)
        self.model = GPT2LMHeadModel.from_pretrained(model_name)
        self.model.eval()
        if torch.cuda.is_available():
            self.model.to('cuda')
    def perplexity(self, text: str) -> float:
        # calcola perplexity su chunk per non saturare memoria
        enc = self.tokenizer(text, return_tensors="pt", truncation=False)
        input_ids = enc["input_ids"]
        if torch.cuda.is_available():
            input_ids = input_ids.to('cuda')
        with torch.no_grad():
            outputs = self.model(input_ids, labels=input_ids)
            loss = outputs.loss.item()
        return math.exp(loss)

# -------------------------
# Combinazione delle feature in un punteggio 0-100
# -------------------------

def normalize(x, minv, maxv):
    if x <= minv:
        return 0.0
    if x >= maxv:
        return 1.0
    return (x - minv) / (maxv - minv)

def compute_ai_score(features: dict) -> float:
    """
    Combina: perplessità (inverso), type-token (inverso), variance (inverso), repetition (diretto), punctuation (diretto)
    Restituisce probabilità che il testo sia generato da AI (0-100).
    I pesi sono empirici e possono essere adattati.
    """
    # features attese: perplexity, ttr, var_sent_len, repetition, punct_ratio, avg_sent_len
    # Normalizziamo ogni feature in [0,1] con intervalli ragionevoli
    p = features.get("perplexity", 100.0)
    # perplessità: valori bassi => prob AI. Normalizziamo invertendo:
    p_norm = 1.0 - normalize(p, 10, 120)  # 10 molto prevedibile, 120 molto imprevedibile
    ttr = features.get("ttr", 0.5)
    ttr_norm = 1.0 - normalize(ttr, 0.2, 0.8)  # TTR basso => più AI-like
    var = features.get("var_sent_len", 1.0)
    var_norm = 1.0 - normalize(var, 0.0, 20.0)  # var bassa => più AI-like
    rep = features.get("repetition", 0.0)
    rep_norm = normalize(rep, 0.0, 0.2)  # più ripetizione => AI-like
    punct = features.get("punct_ratio", 0.02)
    punct_norm = normalize(punct, 0.0, 0.08)  # punteggiatura insolita normale range
    # avg sentence length: testi AI spesso hanno frasi regolari; valori estremi possono influire
    avg_len = features.get("avg_sent_len", 10.0)
    avg_norm = 1.0 - abs(normalize(avg_len, 2, 30) - 0.5) * 2  # centro favorevole => umano (reduce AI-likeliness)
    # pesi (sommare 1.0)
    weights = {
        "p_norm": 0.35,
        "ttr": 0.15,
        "var": 0.15,
        "rep": 0.15,
        "punct": 0.10,
        "avg": 0.10
    }
    score = (
        p_norm * weights["p_norm"] +
        ttr_norm * weights["ttr"] +
        var_norm * weights["var"] +
        rep_norm * weights["rep"] +
        punct_norm * weights["punct"] +
        (1.0 - avg_norm) * weights["avg"]
    )
    # scala su 0-100
    return max(0.0, min(100.0, score * 100.0))

# -------------------------
# Main
# -------------------------

def analyze_text(text: str, use_perplexity=True):
    text = text.strip()
    if not text:
        print("Nessun testo fornito. Esco.")
        return

    # Preprocess
    tokens = re.findall(r"\w+|[^\w\s]", text, re.UNICODE)
    tokens = [t.lower() for t in tokens if t.strip()]
    sentences = split_sentences(text)

    feats = {}
    feats["ttr"] = type_token_ratio([t for t in tokens if re.match(r"\w+", t)])
    feats["avg_sent_len"] = avg_sentence_length(sentences)
    feats["var_sent_len"] = sentence_length_variance(sentences)
    feats["punct_ratio"] = punctuation_ratio(text)
    feats["repetition"] = repetition_score([t for t in tokens if re.match(r"\w+", t)], n=3)

    if use_perplexity and 'GPT2LMHeadModel' in globals() and GPT2LMHeadModel is not None:
        try:
            estimator = PerplexityEstimator(model_name="gpt2")
            ppx = estimator.perplexity(text)
            feats["perplexity"] = ppx
        except Exception as e:
            print("Impossibile calcolare la perplessità (errore):", e)
            feats["perplexity"] = 100.0
    else:
        feats["perplexity"] = 100.0  # valore neutro se non disponibile

    score = compute_ai_score(feats)
    # Interpretazione
    if score >= 75:
        verdict = "🔴 Molto probabile test generato da AI"
    elif score >= 50:
        verdict = "🟠 Possibile AI (indeterminato)"
    else:
        verdict = "🟢 Probabilmente umano"

    # Output dettagliato
    print("\n=== RISULTATO ===")
    print(f"Punteggio AI stimato: {score:.1f}% -> {verdict}")
    print("\nDettagli features (valori grezzi):")
    print(f"- Perplessità (GPT-2): {feats['perplexity']:.2f}")
    print(f"- Type-Token Ratio (diversità lessicale): {feats['ttr']:.3f}")
    print(f"- Lunghezza media frasi (parole): {feats['avg_sent_len']:.2f}")
    print(f"- Varianza lunghezza frasi: {feats['var_sent_len']:.3f}")
    print(f"- Rapporto punteggiatura/testo: {feats['punct_ratio']:.4f}")
    print(f"- Ripetizione n-gram (3): {feats['repetition']:.4f}")

    print("\nNote:")
    print("- Questo è un approccio euristico: nessun detector è infallibile.")
    print("- Testi molto brevi (< 50 parole) sono difficili da classificare accuratamente.")
    print("- Modifica i pesi o le soglie nel codice per adattarlo al tuo dominio.")
    print("=================\n")

def read_multiline_input():
    print("Incolla il testo da analizzare. Premi Ctrl+Z + Invio per terminare:")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        lines.append(line)
    return "\n".join(lines)

if __name__ == "__main__":
    text = read_multiline_input()
    # Chiama la funzione di analisi con `text`
    analyze_text(text, use_perplexity=False)



