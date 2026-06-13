def apply_faz6_engine_options(app):
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_size": 25,
        "max_overflow": 15,
        "pool_recycle": 1800,
        "pool_pre_ping": True,
    }
    return app