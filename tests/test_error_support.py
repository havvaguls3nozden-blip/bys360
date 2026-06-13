from __future__ import annotations

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.error_support import classify_exception, humanize_exception


def test_classify_exception_integrity():
    err = IntegrityError('stmt', 'params', Exception('boom'))
    assert classify_exception(err) == 'integrity'


def test_classify_exception_database():
    assert classify_exception(SQLAlchemyError('db')) == 'database'


def test_humanize_validation_error_uses_message():
    assert humanize_exception(ValueError('Eksik alan')) == 'Eksik alan'
