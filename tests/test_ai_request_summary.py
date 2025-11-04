import dashboard_server as server


def summarize(entries):
    return server._summarize_ai_requests(entries)


def test_summarize_ai_requests_falls_back_to_headline_symbol():
    entries = [
        {
            "ts": "2025-11-04T19:08:48+00:00",
            "kind": "decision",
            "headline": "AI rejected ADAUSDT",
            "body": "Signal blocked by safety filters",
            "data": None,
        }
    ]

    result = summarize(entries)

    assert len(result) == 1
    record = result[0]
    assert record["symbol"] == "ADAUSDT"
    assert record["status"] == "rejected"
    assert record["events"][0]["kind"] == "decision"


def test_summarize_ai_requests_generates_key_for_budget_events():
    entry = {
        "ts": "2025-11-04T19:00:00+00:00",
        "kind": "alert",
        "headline": "AI budget exhausted",
        "data": {
            "ai_request": True,
            "request_kind": "plan",
            "request_estimate": 0.75,
        },
    }

    result = summarize([entry])

    assert len(result) == 1
    record = result[0]
    assert record["id"].startswith("auto::")
    assert record["origin"] == "plan"
    assert record["status"] == "pending"
    assert record["events"][0]["kind"] == "alert"

