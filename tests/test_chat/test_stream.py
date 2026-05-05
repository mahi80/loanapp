from src.chat.stream import format_text_delta, format_data_event


def test_format_text_delta():
    event = format_text_delta("txt_1", "Hello world")
    assert '"type": "text-delta"' in event or '"type":"text-delta"' in event
    assert '"delta": "Hello world"' in event or '"delta":"Hello world"' in event


def test_format_data_event():
    event = format_data_event("status", {"phase": "intake"})
    assert '"type": "data-status"' in event or '"type":"data-status"' in event
    assert '"phase": "intake"' in event or '"phase":"intake"' in event
