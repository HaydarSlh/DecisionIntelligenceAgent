# Artifacts — produced by notebook.ipynb

Consumed by: FastAPI backend, LLM zero-shot predictor, RAG pipeline.

## Files

| File | Purpose |
|---|---|
| `priority_model.joblib` | Calibrated sklearn Pipeline. Input: DataFrame w/ `text` + numeric cols. Output: P(urgent). |
| `feature_extractor.py` | Request-time feature extraction (`extract_numeric_features()`) |
| `decision_threshold.json` | Operating threshold |
| `labeling_function.py` | Weak-supervision rule (for LLM zero-shot prompt) |
| `metrics.json` | Comparison-panel numbers |
| `feature_names.json` | Feature inventory / input schema |

## Model info
- Classifier: **LGBMClassifier**
- Test F1 (urgent): **0.9966**
- Test ROC-AUC: **0.9999**
- Mean latency: **70.58 ms/call**
- Cost per call: **$0.00**

## Production usage

```python
import joblib, pandas as pd
from feature_extractor import extract_numeric_features, NUMERIC_FEATURE_COLS
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

pipe = joblib.load("models/priority_model.joblib")
sia = SentimentIntensityAnalyzer()

def predict(text):
    df = pd.DataFrame({"text": [text]})
    num = extract_numeric_features(df["text"])
    v = sia.polarity_scores(text)
    num["vader_neg"] = v["neg"]; num["vader_neu"] = v["neu"]
    num["vader_pos"] = v["pos"]; num["vader_compound"] = v["compound"]
    X = pd.concat([df, num], axis=1)[["text"] + NUMERIC_FEATURE_COLS]
    return float(pipe.predict_proba(X)[0, 1])
```

## Reproduction
Re-run `notebook.ipynb` on `../dataset/twcs.csv` with `random_state=42`.
