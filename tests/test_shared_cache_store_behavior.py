from __future__ import annotations

from flask import Flask


def test_shared_cache_file_backend_roundtrip(tmp_path):
    from app.services.shared_cache_store import delete_prefix, get_json, set_json

    app = Flask(__name__)
    app.config.update(CACHE_BACKEND="file", CACHE_FILE=str(tmp_path / "cache.json"), CACHE_KEY_PREFIX="test")
    with app.app_context():
        assert set_json("feedback:pulse:unit:1", {"ok": True, "rows": [1, 2]}, ttl_seconds=60)
        assert get_json("feedback:pulse:unit:1") == {"ok": True, "rows": [1, 2]}
        assert delete_prefix("feedback:pulse:") >= 1
        assert get_json("feedback:pulse:unit:1") is None
