"""
Labeling-function definition — importable by FastAPI backend and LLM prompt builder.
Produced by notebook.ipynb (Phase 3). The LLM zero-shot classifier consumes
LLM_PROMPT_DEFINITION so it judges urgency by the same rule the ML model was trained on.
"""
URGENCY_KEYWORDS   = ['refund', 'cancel', 'cancelled', 'canceled', 'hacked', 'stolen', 'fraud', 'unauthorized', 'scam', 'locked out', 'overcharged', 'double charge', 'charged twice', 'broken', 'not working', "doesn't work", "won't work", 'outage', 'down', 'error', 'crash', 'crashed', 'urgent', 'asap', 'emergency', 'immediately', 'help', 'please help', 'ridiculous', 'unacceptable', 'furious', 'disgusting']
NEGATIVE_WORDS     = ['worst', 'terrible', 'horrible', 'awful', 'pathetic', 'useless', 'garbage', 'trash', 'waste', 'nightmare', 'disaster']
MONEY_TERMS        = ['charged', 'payment', 'bill', 'billed', 'money back', 'account locked', 'card declined', 'subscription', 'invoice']
TIME_PRESSURE      = ['still waiting', 'hours ago', 'days ago', 'weeks ago', 'still no', 'no response', 'no reply', 'no update', 'been waiting', 'keep waiting', 'ignoring me', '3 days', '4 days', '5 days', 'a week']
PRIORITY_THRESHOLD = 2

LLM_PROMPT_DEFINITION = """A customer support message is URGENT if it exhibits one or more of:
(a) explicit urgency / emergency keywords (refund, cancel, hacked, stolen, outage, etc.)
(b) strong negative emotional language
(c) intense punctuation (>=3 exclamation marks) or shouting (>=30% caps letters)
(d) strongly negative sentiment
(e) financial / account stakes (unauthorized charges, account locked)
(f) time pressure (still waiting, days/hours ago)

Otherwise it is NORMAL."""
