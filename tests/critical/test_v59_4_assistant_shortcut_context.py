# -*- coding: utf-8 -*-
"""BYS360 v59.4 — assistant shortcut context contract testi.

Bu test, context processor DB/servis hatası yaşasa bile şablonun ihtiyaç duyduğu
anahtarların kaybolmamasını kontrol eder.
"""


def test_v59_4_assistant_shortcut_context_keys_are_always_available(app):
    processors = app.template_context_processors.get(None, [])
    context = {}
    with app.test_request_context("/"):
        for processor in processors:
            try:
                data = processor()
            except Exception:
                __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (tests/critical/test_v59_4_assistant_shortcut_context.py:16)")
                continue
            if isinstance(data, dict):
                context.update(data)

    assert "assistant_shortcut_visibility_map" in context
    assert "assistant_shortcut_visibility_json" in context
    assert "assistant_shortcut_label_map" in context
    assert "assistant_shortcut_label_json" in context
    assert callable(context["assistant_shortcut_visibility_map"])
    assert isinstance(context["assistant_shortcut_visibility_json"], dict)

    # Callable helper hata verirse şablon yine patlamamalı; boş dict kabul edilir.
    value = context["assistant_shortcut_visibility_map"]()
    assert isinstance(value, dict)
