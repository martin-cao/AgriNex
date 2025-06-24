from flask import Flask, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello():
    return jsonify({"message": "AgriNex API is running!"})

@app.route('/api/health')
def health():
    return jsonify({"status": "healthy"})

# 注册MCP路由
# from controllers.mcp_controller import mcp_bp
# app.register_blueprint(mcp_bp, url_prefix='/api/v1/mcp')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
