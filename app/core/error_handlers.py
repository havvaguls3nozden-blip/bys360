from flask import current_app, render_template


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(error):
        current_app.logger.warning("400 hatası: %s", error)
        try:
            return render_template("errors/400.html"), 400
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/core/error_handlers.py:10")
            return "Geçersiz istek", 400

    @app.errorhandler(403)
    def forbidden(error):
        current_app.logger.warning("403 hatası: %s", error)
        try:
            return render_template("errors/403.html"), 403
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/core/error_handlers.py:18")
            return "Yetkisiz erişim", 403

    @app.errorhandler(404)
    def not_found(error):
        current_app.logger.warning("404 hatası: %s", error)
        try:
            return render_template("errors/404.html"), 404
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/core/error_handlers.py:26")
            return "Sayfa bulunamadı", 404

    @app.errorhandler(500)
    def internal_error(error):
        current_app.logger.exception("500 hatası yakalandı: %s", error)
        try:
            return render_template("errors/500.html"), 500
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/core/error_handlers.py:34")
            return "Beklenmeyen bir hata oluştu", 500

    @app.errorhandler(Exception)
    def unhandled_exception(error):
        current_app.logger.exception("Unhandled exception: %s", error)
        try:
            return render_template("errors/500.html"), 500
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/core/error_handlers.py:42")
            return "Beklenmeyen bir hata oluştu", 500
