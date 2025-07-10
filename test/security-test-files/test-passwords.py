# SECURITY TEST FILE - CRITICAL VIOLATIONS
# This file contains intentional security violations for testing Security Agent detection

# Critical violations - should trigger automatic veto
DATABASE_PASSWORD = 'hardcoded_password_123'
admin_password = 'admin123'
root_password = 'root'
default_password = 'password'

# Database connection strings with passwords
db_connection = 'postgresql://user:password123@localhost/db'
mysql_connection = 'mysql://admin:secret123@localhost:3306/mydb'
mongodb_connection = 'mongodb://user:pass123@localhost:27017/db'

# Various password patterns
USER_PASSWORD = 'P@ssw0rd123'
SECRET_KEY = 'my_super_secret_key_12345'
PRIVATE_KEY = 'private_key_content_here'
ENCRYPTION_PASSWORD = 'encrypt_me_123'

# Configuration dictionaries with passwords
DATABASE_CONFIG = {
    'host': 'localhost',
    'user': 'admin',
    'password': 'admin_password_123',
    'database': 'production_db'
}

REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'password': 'redis_password_456'
}

# Authentication credentials
SMTP_CONFIG = {
    'host': 'smtp.gmail.com',
    'port': 587,
    'username': 'user@gmail.com',
    'password': 'gmail_app_password_789'
}

# Weak/common passwords
passwords = [
    'password',
    '123456',
    'admin',
    'root',
    'guest',
    'user',
    'test',
    'password123',
    'admin123'
]

# Base64 encoded passwords (still detectable)
import base64
encoded_password = base64.b64encode(b'secret_password_123').decode()

# URL-encoded passwords
url_with_password = 'https://user:password123@api.example.com/data'
ftp_with_password = 'ftp://admin:admin123@ftp.example.com/files'

# SSH connection strings
ssh_command = 'ssh user@server.com -p 22 # password: ssh_password_123'

# Function with hardcoded password
def connect_to_database():
    password = 'hardcoded_db_password_456'
    return f'postgresql://user:{password}@localhost/db'

# Class with password attribute
class DatabaseConnection:
    def __init__(self):
        self.password = 'class_password_789'
        self.secret_key = 'class_secret_key_abc'
        
    def get_connection_string(self):
        return f'mysql://user:{self.password}@localhost/db'

# Password in comments
# Default password: default_password_123
# TODO: Change password from temp_password_456 to something secure
"""
Database credentials:
username: admin
password: admin_password_789
"""