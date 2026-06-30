# ============================================
# HAVOCSOC - CLOUD CONTROL PLANE (SIMPLIFIED)
# ============================================

import os
import hashlib
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Store data in memory (simple, no database needed)
customers = {}
telemetry_data = []

@app.route('/')
def home():
    return jsonify({
        'message': '🛡️ HavocSOC Control Plane API',
        'status': 'online',
        'version': '1.0.0',
        'endpoints': {
            'health': '/api/health (GET)',
            'register': '/api/register (POST)',
            'verify_license': '/api/verify-license (POST)',
            'telemetry': '/api/telemetry (POST)',
            'threat_intel': '/api/threat-intel (GET)',
            'customers': '/api/customers (GET)'
        }
    })

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'mode': 'control-plane',
        'version': '1.0.0',
        'customers_registered': len(customers)
    })

@app.route('/api/register', methods=['POST'])
def register_customer():
    data = request.json
    customer_id = data.get('customer_id')
    email = data.get('email', '')
    
    if not customer_id:
        return jsonify({'error': 'customer_id required'}), 400
    
    # Check if customer already exists
    if customer_id in customers:
        return jsonify({'error': 'Customer already registered'}), 400
    
    # Generate license key
    license_key = hashlib.sha256(
        f"{customer_id}:{datetime.now().isoformat()}".encode()
    ).hexdigest()[:16]
    
    # Store customer
    customers[customer_id] = {
        'email': email,
        'license_key': license_key,
        'registered_at': datetime.now().isoformat(),
        'expiry': '2025-12-31T00:00:00',
        'features': ['basic', 'ai_investigation', 'dashboard']
    }
    
    return jsonify({
        'status': 'registered',
        'customer_id': customer_id,
        'license_key': license_key,
        'expiry': '2025-12-31T00:00:00'
    })

@app.route('/api/verify-license', methods=['POST'])
def verify_license():
    data = request.json
    license_key = data.get('license_key')
    
    if not license_key:
        return jsonify({'valid': False, 'message': 'License key required'}), 400
    
    # Find customer by license key
    found_customer = None
    for cid, info in customers.items():
        if info.get('license_key') == license_key:
            found_customer = cid
            break
    
    if not found_customer:
        return jsonify({'valid': False, 'message': 'Invalid license'}), 401
    
    return jsonify({
        'valid': True,
        'customer_id': found_customer,
        'days_remaining': 30,
        'features': customers[found_customer].get('features', [])
    })

@app.route('/api/telemetry', methods=['POST'])
def receive_telemetry():
    data = request.json
    token = request.headers.get('X-API-Token')
    
    if not token:
        return jsonify({'error': 'Token required'}), 401
    
    # Store telemetry
    telemetry_data.append({
        'customer_id': data.get('customer_id', 'anonymous'),
        'threat_type': data.get('threat_type'),
        'anonymized_ip': data.get('anonymized_ip'),
        'confidence': data.get('confidence'),
        'verdict': data.get('verdict'),
        'received_at': datetime.now().isoformat()
    })
    
    # Keep only last 100 entries
    if len(telemetry_data) > 100:
        telemetry_data.pop(0)
    
    return jsonify({'status': 'received'})

@app.route('/api/threat-intel', methods=['GET'])
def get_threat_intel():
    return jsonify({
        'total': len(telemetry_data),
        'recent': telemetry_data[-20:]
    })

@app.route('/api/customers', methods=['GET'])
def list_customers():
    return jsonify({
        'customers': [{'id': cid, 'info': info} for cid, info in customers.items()]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
