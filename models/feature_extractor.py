"""
Request-time feature extractor. Mirrors Phase 5 of the notebook.
Import from the backend:
    from feature_extractor import extract_numeric_features, NUMERIC_FEATURE_COLS
"""
import re
import pandas as pd

URGENCY_KEYWORDS = ['refund', 'cancel', 'cancelled', 'canceled', 'hacked', 'stolen', 'fraud', 'unauthorized', 'scam', 'locked out', 'overcharged', 'double charge', 'charged twice', 'broken', 'not working', "doesn't work", "won't work", 'outage', 'down', 'error', 'crash', 'crashed', 'urgent', 'asap', 'emergency', 'immediately', 'help', 'please help', 'ridiculous', 'unacceptable', 'furious', 'disgusting']
NEGATIVE_WORDS   = ['worst', 'terrible', 'horrible', 'awful', 'pathetic', 'useless', 'garbage', 'trash', 'waste', 'nightmare', 'disaster']
MONEY_TERMS      = ['charged', 'payment', 'bill', 'billed', 'money back', 'account locked', 'card declined', 'subscription', 'invoice']
TIME_PRESSURE    = ['still waiting', 'hours ago', 'days ago', 'weeks ago', 'still no', 'no response', 'no reply', 'no update', 'been waiting', 'keep waiting', 'ignoring me', '3 days', '4 days', '5 days', 'a week']

NUMERIC_FEATURE_COLS = ['char_len', 'word_len', 'avg_word_len', 'unique_ratio', 'exclaim_count', 'question_count', 'consecutive_punct', 'ellipsis', 'mention_count', 'hashtag_count', 'url_count', 'caps_ratio', 'has_urgency_kw', 'has_negative_word', 'has_money_term', 'has_time_pressure', 'vader_neg', 'vader_neu', 'vader_pos', 'vader_compound']

_MENTION_URL_HASH = re.compile(r"@\w+|https?://\S+|#\w+")

def _caps_ratio(t):
    cleaned = _MENTION_URL_HASH.sub("", t)
    letters = [c for c in cleaned if c.isalpha()]
    return sum(1 for c in letters if c.isupper()) / max(len(letters), 1)

def extract_numeric_features(texts):
    s = pd.Series(texts) if not isinstance(texts, pd.Series) else texts
    out = pd.DataFrame(index=s.index)
    out["char_len"]          = s.str.len()
    out["word_len"]          = s.str.split().str.len().fillna(0)
    out["avg_word_len"]      = out["char_len"] / out["word_len"].clip(lower=1)
    out["unique_ratio"]      = s.apply(lambda t: len(set(t.lower().split())) / max(len(t.split()), 1))
    out["exclaim_count"]     = s.str.count("!")
    out["question_count"]    = s.str.count(r"\?")
    out["consecutive_punct"] = s.str.count(r"!{{2,}}|\?{{2,}}")
    out["ellipsis"]          = s.str.count(r"\.{{3,}}")
    out["mention_count"]     = s.str.count(r"@\w+")
    out["hashtag_count"]     = s.str.count(r"#\w+")
    out["url_count"]         = s.str.count(r"https?://")
    out["caps_ratio"]        = s.apply(_caps_ratio)
    tl = s.str.lower()
    out["has_urgency_kw"]    = tl.apply(lambda t: int(any(kw in t for kw in URGENCY_KEYWORDS)))
    out["has_negative_word"] = tl.apply(lambda t: int(any(w in t for w in NEGATIVE_WORDS)))
    out["has_money_term"]    = tl.apply(lambda t: int(any(m in t for m in MONEY_TERMS)))
    out["has_time_pressure"] = tl.apply(lambda t: int(any(tt in t for tt in TIME_PRESSURE)))
    return out.astype(float)
