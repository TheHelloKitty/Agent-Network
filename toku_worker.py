BID_LOG = Path("toku/bid_ids.json")

def load_bid_ids():
    if BID_LOG.exists():
        try:
            return set(json.loads(BID_LOG.read_text(encoding="utf-8")))
        except Exception:
            return set()
    return set()

def save_bid_ids(ids):
    Path("toku").mkdir(exist_ok=True)
    BID_LOG.write_text(json.dumps(sorted(ids)), encoding="utf-8")
