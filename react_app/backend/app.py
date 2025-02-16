from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
import subprocess
import threading
import json
import time
import os

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Store active scans
active_scans = {}

def monitor_subfinder_output(domain, output_file):
    previous_subdomains = set()
    
    while domain in active_scans:
        try:
            if os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    current_subdomains = set(line.strip() for line in f)
                
                new_subdomains = current_subdomains - previous_subdomains
                if new_subdomains:
                    # Update the recon.json file
                    recon_file = '../src/recon.json'
                    try:
                        with open(recon_file, 'r') as f:
                            recon_data = json.load(f)
                    except:
                        recon_data = {"name": domain, "type": "root", "children": []}
                    
                    # Add new subdomains
                    for subdomain in new_subdomains:
                        new_node = {
                            "name": subdomain,
                            "type": "subdomain",
                            "children": []
                        }
                        recon_data["children"].append(new_node)
                    
                    # Save updated recon data
                    with open(recon_file, 'w') as f:
                        json.dump(recon_data, f, indent=4)
                    
                    # Emit via websocket
                    socketio.emit('new_subdomains', {
                        'domain': domain,
                        'subdomains': list(new_subdomains)
                    })
                    
                    previous_subdomains = current_subdomains
                
        except Exception as e:
            print(f"Error in monitoring thread: {str(e)}")
            
        time.sleep(0.01)  # 10ms delay

@app.route('/scan', methods=['POST'])
def scan():
    domain = request.args.get('domain')
    if not domain:
        return jsonify({"status": "error", "message": "Domain parameter is required"}), 200
    
    # Handle file upload (store for future use)
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 200
    
    file = request.files['file']
    if not file.filename:
        return jsonify({"status": "error", "message": "No file selected"}), 200
    
    # Create output file for subfinder
    output_file = f"scan_{domain}.txt"
    
    try:
        # Start subfinder process
        process = subprocess.Popen(
            ['subfinder', '-d', domain, '-o', output_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Store process information
        active_scans[domain] = {
            'process': process,
            'output_file': output_file,
            'start_time': time.time()
        }
        
        # Start monitoring thread
        monitor_thread = threading.Thread(
            target=monitor_subfinder_output,
            args=(domain, output_file)
        )
        monitor_thread.daemon = True
        monitor_thread.start()
        
        return jsonify({
            "status": "success",
            "message": f"Started scanning {domain}"
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to start subfinder: {str(e)}"
        }), 200

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)
