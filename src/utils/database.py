import pymysql
def get_db_connection():
    return pymysql.connect(
        host = "gateway01.us-east-1.prod.aws.tidbcloud.com",
        port = 4000,
        user = "4LGwjP9LLkyZsPM.root",
        password = "8UtljhBzTizGLCmZ",
        database = "test",
        ssl_verify_cert = True,
        ssl_verify_identity = True,
        ssl_ca = "/etc/ssl/cert.pem"
    )