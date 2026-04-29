# app.py - Main Application (बहुत छोटी और साफ)
from flask import Flask
from config import Config
from models import db
from utils.helpers import create_directories

# app.py - create_app() फंक्शन के अंदर

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
   
    # ⭐ SQLite Lock Fix
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'connect_args': {
            'timeout': 30,           # 30 सेकंड तक wait करें
            'check_same_thread': False,  # Multiple threads allow
        },
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }
    

    db.init_app(app)
    create_directories(app)
    
    # Register Blueprints
    from blueprints.auth import auth_bp
    from blueprints.profile import profile_bp
    from blueprints.dashboard import dashboard_bp
    from blueprints.jobs import jobs_bp
    from blueprints.main import main_bp
    from blueprints.scraper import scraper_bp, start_job_scraper  # ⭐ scraper import
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(scraper_bp)  # ⭐ scraper blueprint register
    
    # ⭐ Start job scraper
    # start_job_scraper(app)
    
    return app
if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)