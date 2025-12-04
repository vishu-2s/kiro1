"""
Flask web application for Multi-Agent Security Analysis System
Provides a web UI for analyzing GitHub repositories and local directories
"""
import os
import json
import threading
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import subprocess
import sys

app = Flask(__name__)
app.config['SECRET_KEY'] = 'multi-agent-security-analysis'
app.config['OUTPUT_FOLDER'] = 'outputs'

# Load confidence threshold from environment or use default
CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.7'))

# Global state for tracking analysis
analysis_state = {
    'running': False,
    'logs': [],
    'status': 'idle',
    'result_file': None,
    'start_time': None,
    'end_time': None
}

def log_message(message, level='info'):
    """Add a log message to the analysis state"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = {
        'timestamp': timestamp,
        'level': level,
        'message': message
    }
    analysis_state['logs'].append(log_entry)
    print(f"[{timestamp}] [{level.upper()}] {message}")

def run_analysis(mode, target, skip_update, skip_osv, ecosystem='auto'):
    """Run the security analysis in a background thread"""
    try:
        # Clear logs only when starting a NEW analysis
        analysis_state['logs'] = []
        analysis_state['running'] = True
        analysis_state['status'] = 'running'
        analysis_state['start_time'] = datetime.now().isoformat()
        analysis_state['result_file'] = None
        
        log_message(f"Starting {mode} analysis for: {target} (ecosystem: {ecosystem})")
        
        # Build command
        cmd = [sys.executable, 'main_github.py']
        
        if mode == 'local':
            cmd.extend(['--local', target])
        elif mode == 'github':
            cmd.extend(['--github', target])
        else:  # sbom
            cmd.extend(['--sbom', target])
        
        cmd.extend(['--confidence-threshold', str(CONFIDENCE_THRESHOLD)])
        
        # Add ecosystem parameter
        if ecosystem and ecosystem != 'auto':
            cmd.extend(['--ecosystem', ecosystem])
        
        if skip_update:
            cmd.append('--skip-db-update')
        
        if skip_osv:
            cmd.append('--no-osv')
        
        log_message(f"Executing command: {' '.join(cmd)}")
        
        # Run the analysis
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Stream output
        for line in process.stdout:
            line = line.strip()
            if line:
                log_message(line)
        
        process.wait()
        
        if process.returncode == 0:
            log_message("Analysis completed successfully", 'success')
            analysis_state['status'] = 'completed'
            
            # Always use the fixed report filename
            report_file = 'demo_ui_comprehensive_report.json'
            report_path = os.path.join(app.config['OUTPUT_FOLDER'], report_file)
            
            if os.path.exists(report_path):
                analysis_state['result_file'] = report_file
                log_message(f"Results saved to: {report_file}", 'success')
            else:
                log_message("Warning: Report file not found", 'warning')
        else:
            log_message(f"Analysis failed with exit code {process.returncode}", 'error')
            analysis_state['status'] = 'failed'
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        log_message(f"Error during analysis: {str(e)}", 'error')
        log_message(f"Traceback: {error_details}", 'error')
        analysis_state['status'] = 'failed'
        print(f"ERROR in run_analysis: {error_details}")  # Also print to console
    
    finally:
        analysis_state['running'] = False
        analysis_state['end_time'] = datetime.now().isoformat()
        print(f"Analysis finished. Status: {analysis_state['status']}")  # Debug print

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Start a new analysis"""
    print("=== /api/analyze endpoint called ===")  # Debug
    
    if analysis_state['running']:
        print("Analysis already running, rejecting request")
        return jsonify({'error': 'Analysis already running'}), 400
    
    data = request.json
    print(f"Request data: {data}")  # Debug
    
    mode = data.get('mode', 'github')
    target = data.get('target', '')
    ecosystem = data.get('ecosystem', 'auto')
    skip_update = data.get('skip_update', False)
    skip_osv = data.get('skip_osv', False)
    
    print(f"Mode: {mode}, Target: {target}, Ecosystem: {ecosystem}, Confidence: {CONFIDENCE_THRESHOLD}")  # Debug
    
    if not target:
        print("No target provided")
        return jsonify({'error': 'Target is required'}), 400
    
    # Start analysis in background thread
    print("Starting background thread...")  # Debug
    thread = threading.Thread(
        target=run_analysis,
        args=(mode, target, skip_update, skip_osv, ecosystem)
    )
    thread.daemon = True
    thread.start()
    print(f"Thread started: {thread.is_alive()}")  # Debug
    
    return jsonify({'status': 'started'})

@app.route('/api/status')
def get_status():
    """Get current analysis status and logs"""
    return jsonify({
        'running': analysis_state['running'],
        'status': analysis_state['status'],
        'logs': analysis_state['logs'],
        'result_file': analysis_state['result_file'],
        'start_time': analysis_state['start_time'],
        'end_time': analysis_state['end_time']
    })

@app.route('/api/report')
def get_report():
    """Get the analysis report - always uses demo_ui_comprehensive_report.json"""
    # Always use the fixed report filename
    report_path = os.path.join(app.config['OUTPUT_FOLDER'], 'demo_ui_comprehensive_report.json')
    
    if not os.path.exists(report_path):
        return jsonify({'error': 'No report available. Please run an analysis first.'}), 404
    
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        # Create response with cache-busting headers
        response = jsonify(report_data)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        return jsonify({'error': f'Failed to load report: {str(e)}'}), 500

@app.route('/api/reports')
def list_reports():
    """List all available reports including backups"""
    output_dir = app.config['OUTPUT_FOLDER']
    if not os.path.exists(output_dir):
        return jsonify({'reports': [], 'backups': []})
    
    reports = []
    backups = []
    
    for filename in os.listdir(output_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(output_dir, filename)
            file_info = {
                'filename': filename,
                'size': os.path.getsize(filepath),
                'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
            }
            
            # Separate backups from regular reports
            if 'backup' in filename.lower():
                backups.append(file_info)
            else:
                reports.append(file_info)
    
    # Sort by modified date (newest first)
    reports.sort(key=lambda x: x['modified'], reverse=True)
    backups.sort(key=lambda x: x['modified'], reverse=True)
    
    return jsonify({
        'reports': reports,
        'backups': backups
    })

@app.route('/outputs/<path:filename>')
def download_file(filename):
    """Download a report file"""
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

@app.route('/api/restore-backup', methods=['POST'])
def restore_backup():
    """Restore a backup file as the current report"""
    data = request.json
    backup_filename = data.get('backup_filename', '')
    
    if not backup_filename:
        return jsonify({'error': 'Backup filename is required'}), 400
    
    output_dir = app.config['OUTPUT_FOLDER']
    backup_path = os.path.join(output_dir, backup_filename)
    current_path = os.path.join(output_dir, 'demo_ui_comprehensive_report.json')
    
    # Verify backup file exists
    if not os.path.exists(backup_path):
        return jsonify({'error': 'Backup file not found'}), 404
    
    try:
        # Create backup of current report before restoring
        if os.path.exists(current_path):
            backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_backup_path = os.path.join(output_dir, f"demo_ui_comprehensive_report_backup_{backup_timestamp}.json")
            import shutil
            shutil.copy2(current_path, new_backup_path)
            log_message(f"Created backup of current report: {new_backup_path}")
        
        # Restore the backup
        import shutil
        shutil.copy2(backup_path, current_path)
        log_message(f"Restored backup: {backup_filename}")
        
        return jsonify({
            'success': True,
            'message': f'Backup restored successfully',
            'restored_from': backup_filename
        })
        
    except Exception as e:
        log_message(f"Error restoring backup: {str(e)}", 'error')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Ensure output directory exists
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    
    print("=" * 60)
    print("Multi-Agent Security Analysis System - Web UI")
    print("=" * 60)
    print("\nStarting Flask server...")
    print("Access the application at: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    
    # Disable auto-reload to prevent interrupting analysis
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True, use_reloader=False)
