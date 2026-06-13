
import os

from app import create_app

app = create_app()


def _host() -> str:
    default_host = "127.0.0.1" if app.config.get("APP_ENV") == "development" else "0.0.0.0"
    return os.getenv("APP_HOST", default_host)


def _port() -> int:
    return int(os.getenv("APP_PORT", "8000"))


def _waitress_threads() -> int:
    return int(os.getenv("WAITRESS_THREADS", str(app.config.get("WAITRESS_THREADS", 8))))


if __name__ == "__main__":
    host = _host()
    port = _port()
    app_env = (app.config.get("APP_ENV") or "development").strip().lower()
    print(f"BYS360 başlatılıyor ({app_env}): http://{host}:{port}")

    if app_env in {"production", "staging"}:
        from waitress import serve

        serve(app, host=host, port=port, threads=_waitress_threads())
    else:
        app.run(host=host, port=port, debug=False)
