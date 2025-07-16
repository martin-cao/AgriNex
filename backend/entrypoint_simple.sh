#!/bin/bash
set -e

echo "AgriNex Backend starting..."

# 等待数据库连接
echo "Waiting for database connection..."
python -c "
import time
import pymysql
import os
from urllib.parse import urlparse

def wait_for_db():
    db_url = os.environ.get('DATABASE_URL', 'mysql+pymysql://agrinex_user:agrinex_password@mysql:3306/agrinex')
    parsed = urlparse(db_url)
    
    host = parsed.hostname
    port = parsed.port or 3306
    user = parsed.username
    password = parsed.password
    database = parsed.path.lstrip('/')
    
    for i in range(30):
        try:
            connection = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )
            connection.close()
            print(f'Database connection successful after {i+1} attempts')
            return
        except Exception as e:
            print(f'Database connection attempt {i+1}/30 failed: {e}')
            time.sleep(2)
    
    raise Exception('Could not connect to database after 30 attempts')

wait_for_db()
"

echo "Starting Flask application..."
exec python app.py
