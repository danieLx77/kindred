from main import read_root


def test_read_root_returns_ok_status():
    assert read_root() == {"status": "ok"}
