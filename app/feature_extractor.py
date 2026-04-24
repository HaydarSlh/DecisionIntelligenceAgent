# ============================================================
# Feature Extractor — numeric features for the ML priority model
# ============================================================
# Must stay in sync with the notebook's NUMERIC_FEATURE_COLS.
# Used at training time (notebook) and inference time (backend).
# ============================================================

import re
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

NUMERIC_FEATURE_COLS = [
    'char_len', 'word_len', 'avg_word_len', 'unique_ratio',
    'exclaim_count', 'question_count', 'consecutive_punct', 'ellipsis',
    'mention_count', 'hashtag_count', 'url_count', 'caps_ratio',
    'has_urgency_kw', 'has_negative_word', 'has_money_term', 'has_time_pressure',
    'vader_neg', 'vader_neu', 'vader_pos', 'vader_compound',
]

_URGENCY_KW = {
    'urgent', 'asap', 'emergency', 'immediately', 'broken', 'outage',
    'down', 'not working', 'failed', 'error', 'issue', 'problem',
    'refund', 'cancel', 'help', 'fix', 'please', 'critical', 'crash',
}
_NEGATIVE_KW = {
    'terrible', 'awful', 'horrible', 'worst', 'bad', 'disappointed',
    'frustrating', 'angry', 'upset', 'furious', 'hate', 'useless',
    'unacceptable', 'ridiculous', 'disgrace', 'shameful',
}
_MONEY_TERMS = {
    'charged', 'charge', 'payment', 'bill', 'invoice', 'refund',
    'money', 'fee', 'cost', 'price', 'paid', 'pay', 'fraud',
    'unauthorized', 'transaction', 'stolen', 'overcharged',
}
_TIME_PRESSURE = {
    'asap', 'immediately', 'urgent', 'now', 'today', 'tonight',
    'deadline', 'expires', 'flight', 'appointment', 'hours', 'minutes',
    'soon', 'quickly', 'hurry', 'waiting',
}

_analyzer: SentimentIntensityAnalyzer | None = None


def _get_analyzer() -> SentimentIntensityAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentIntensityAnalyzer()
    return _analyzer


def _extract_one(text: str) -> dict:
    text = str(text) if text is not None else ''
    words = text.split()
    lower = text.lower()
    word_lower = set(lower.split())

    char_len = len(text)
    word_len = len(words)
    avg_word_len = (sum(len(w) for w in words) / word_len) if word_len > 0 else 0.0
    unique_ratio = len(set(words)) / word_len if word_len > 0 else 0.0

    exclaim_count = text.count('!')
    question_count = text.count('?')
    consecutive_punct = len(re.findall(r'[!?]{2,}', text))
    ellipsis = text.count('...')

    mention_count = len(re.findall(r'@\w+', text))
    hashtag_count = len(re.findall(r'#\w+', text))
    url_count = len(re.findall(r'https?://\S+|www\.\S+', text))

    alpha_chars = [c for c in text if c.isalpha()]
    caps_ratio = (
        sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
        if alpha_chars else 0.0
    )

    has_urgency_kw = int(bool(word_lower & _URGENCY_KW))
    has_negative_word = int(bool(word_lower & _NEGATIVE_KW))
    has_money_term = int(bool(word_lower & _MONEY_TERMS))
    has_time_pressure = int(bool(word_lower & _TIME_PRESSURE))

    scores = _get_analyzer().polarity_scores(text)

    return {
        'char_len': char_len,
        'word_len': word_len,
        'avg_word_len': avg_word_len,
        'unique_ratio': unique_ratio,
        'exclaim_count': exclaim_count,
        'question_count': question_count,
        'consecutive_punct': consecutive_punct,
        'ellipsis': ellipsis,
        'mention_count': mention_count,
        'hashtag_count': hashtag_count,
        'url_count': url_count,
        'caps_ratio': caps_ratio,
        'has_urgency_kw': has_urgency_kw,
        'has_negative_word': has_negative_word,
        'has_money_term': has_money_term,
        'has_time_pressure': has_time_pressure,
        'vader_neg': scores['neg'],
        'vader_neu': scores['neu'],
        'vader_pos': scores['pos'],
        'vader_compound': scores['compound'],
    }


def extract_numeric_features(texts) -> pd.DataFrame:
    """Extract numeric features from a list or Series of texts.

    Returns a DataFrame with columns matching NUMERIC_FEATURE_COLS.
    """
    if hasattr(texts, 'tolist'):
        texts = texts.tolist()
    return pd.DataFrame([_extract_one(t) for t in texts])
