import os
from flask import Flask

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'ifc_app.sqlite'),
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.update(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from ifc_app import db
    db.init_app(app)
    
    from ifc_app import auth
    app.register_blueprint(auth.bp)

    from ifc_app import views
    app.register_blueprint(views.bp)
    
    return app