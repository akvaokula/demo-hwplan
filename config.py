class Config:
    SECRET_KEY = b'_5#y2L"F4Q8z\n\xec]/'
    SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnecttor://hwplan:passphrase@hwplan.mysql.pythonanywhere-services.com/hwplan$default"
    SQLALCHEMY_POOL_RECYCLE = 299
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DebugConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
