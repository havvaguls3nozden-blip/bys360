# -*- coding: utf-8 -*-
"""
A10Q_COMPATIBILITY_WRAPPER

Bu dosya BYS360 A10Q teknik borç temizliği kapsamında bilerek korunmuştur.
Eski import yolunu kırmamak için yeni modüle yönlendiren compatibility wrapper'dır.

Yeni gerçek modül:
app/refactor/maintenance_merge_registry.py
"""

from .maintenance_merge_registry import *  # noqa: F401,F403
