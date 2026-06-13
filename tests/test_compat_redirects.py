from __future__ import annotations

from flask import Blueprint

from app.compat_endpoint_cleanup import _soft_redirect


def test_soft_redirect_targets_endpoint():
    # BYS360_A5_P2C_COMPAT_REDIRECT_TEST_ISOLATION
    # Bu test global/session app fixture kullanmaz.
    # Blueprint kayd? ilk request'ten ?nce yap?lmal?d?r.
    from flask import Flask

    app = Flask(__name__)
    app.secret_key = "bys360-test-secret"
    bp = Blueprint('main', __name__)

    @bp.route('/hedef', endpoint='performance_hierarchy_settings')
    def target():
        return 'ok'

    app.register_blueprint(bp)

    with app.test_request_context('/'):
        response = _soft_redirect('tasindi', 'main.performance_hierarchy_settings')
        assert response.status_code == 302
        assert response.location.endswith('/hedef')
