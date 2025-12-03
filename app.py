"""
Spyder - Flask Web Application
AI-Powered Supply Chain Security Scanner
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
app.config['SECRET_KEY'] = 'spyder-security-scanner'
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

def run_analysis(mode, target, skip_update, skip_osv):
    """Run the security analysis in a background thread"""
    try:
        analysis_state['running'] = True
        analysis_state['status'] = 'running'
        analysis_state['logs'] = []
        analysis_state['start_time'] = datetime.now().isoformat()
        analysis_state['result_file'] = None
        
        log_message(f"Starting {mode} analysis for: {target}")
        
        # Build command
        cmd = [sys.executable, 'main_github.py']
        
        if mode == 'local':
            cmd.extend(['--local', target])
        elif mode == 'github':
            cmd.extend(['--github', target])
        else:  # sbom
            cmd.extend(['--sbom', target])
        
        cmd.extend(['--confidence-threshold', str(CONFIDENCE_THRESHOLD)])
        
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
            
            # Find the result file (look for any .json file, not just _findings.json)
            output_dir = app.config['OUTPUT_FOLDER']
            if os.path.exists(output_dir):
                files = sorted(
                    [f for f in os.listdir(output_dir) if f.endswith('.json')],
                    key=lambda x: os.path.getmtime(os.path.join(output_dir, x)),
                    reverse=True
                )
                if files:
                    analysis_state['result_file'] = files[0]
                    log_message(f"Results saved to: {files[0]}", 'success')
                else:
                    log_message("Warning: No JSON output file found", 'warning')
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
    skip_update = data.get('skip_update', False)
    skip_osv = data.get('skip_osv', False)
    
    print(f"Mode: {mode}, Target: {target}, Confidence: {CONFIDENCE_THRESHOLD}")  # Debug
    
    if not target:
        print("No target provided")
        return jsonify({'error': 'Target is required'}), 400
    
    # Start analysis in background thread
    print("Starting background thread...")  # Debug
    thread = threading.Thread(
        target=run_analysis,
        args=(mode, target, skip_update, skip_osv)
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
    """Get the analysis report"""
    if not analysis_state['result_file']:
        return jsonify({'error': 'No report available'}), 404
    
    result_path = os.path.join(app.config['OUTPUT_FOLDER'], analysis_state['result_file'])
    
    if not os.path.exists(result_path):
        return jsonify({'error': 'Report file not found'}), 404
    
    try:
        with open(result_path, 'r') as f:
            report_data = json.load(f)
        return jsonify(report_data)
    except Exception as e:
        return jsonify({'error': f'Failed to load report: {str(e)}'}), 500

@app.route('/api/reports')
def list_reports():
    """List all available reports"""
    output_dir = app.config['OUTPUT_FOLDER']
    if not os.path.exists(output_dir):
        return jsonify([])
    
    reports = []
    for filename in os.listdir(output_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(output_dir, filename)
            reports.append({
                'filename': filename,
                'size': os.path.getsize(filepath),
                'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
            })
    
    reports.sort(key=lambda x: x['modified'], reverse=True)
    return jsonify(reports)

@app.route('/outputs/<path:filename>')
def download_file(filename):
    """Download a report file"""
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

@app.route('/api/export-pdf', methods=['POST'])
def export_pdf():
    """Export the current report as a PDF"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from io import BytesIO
        import time
        
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Create PDF
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"spyder_report_{timestamp}.pdf"
        pdf_path = os.path.join(app.config['OUTPUT_FOLDER'], pdf_filename)
        
        print(f"Starting PDF generation for {len(data.get('findings', []))} findings...")
        start_time = time.time()
        
        # Generate PDF using ReportLab (optimized for large reports)
        generate_reportlab_pdf(data, pdf_path)
        
        elapsed = time.time() - start_time
        print(f"PDF generated successfully in {elapsed:.2f} seconds")
        
        return jsonify({
            'success': True,
            'filename': pdf_filename,
            'path': f'/outputs/{pdf_filename}'
        })
        
    except ImportError as e:
        return jsonify({
            'error': f'PDF generation library not installed. Run: pip install reportlab. Error: {str(e)}'
        }), 500
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"PDF Generation Error: {error_details}")
        return jsonify({'error': f'Failed to generate PDF: {str(e)}'}), 500

def generate_reportlab_pdf(data, pdf_path):
    """Generate PDF using ReportLab (pure Python, no system dependencies)"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    
    findings = data.get('findings', data.get('security_findings', []))
    metadata = data.get('metadata', {})
    summary = data.get('summary', {})
    
    # Calculate severity counts
    severity_counts = {
        'critical': len([f for f in findings if f.get('severity') == 'critical']),
        'high': len([f for f in findings if f.get('severity') == 'high']),
        'medium': len([f for f in findings if f.get('severity') == 'medium']),
        'low': len([f for f in findings if f.get('severity') == 'low'])
    }
    
    # Calculate vulnerable packages count
    unique_packages = set()
    for f in findings:
        pkg_key = f"{f.get('package', 'Unknown')}@{f.get('version', 'unknown')}"
        unique_packages.add(pkg_key)
    vulnerable_packages_count = len(unique_packages)
    
    # Create PDF document
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=1*inch,
        bottomMargin=0.75*inch
    )
    
    # Container for PDF elements
    story = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1A1A1A'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#666666'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1A1A1A'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#1A1A1A'),
        spaceAfter=6
    )
    
    # Header
    story.append(Paragraph("🕷️ Spyder Security Analysis Report", title_style))
    story.append(Paragraph("AI-Powered Supply Chain Security Scanner", subtitle_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}", 
                          ParagraphStyle('Date', parent=body_style, alignment=TA_RIGHT, fontSize=9, textColor=colors.HexColor('#666666'))))
    story.append(Spacer(1, 0.3*inch))
    
    # Executive Summary
    story.append(Paragraph("Executive Summary", heading_style))
    
    # Statistics table
    stats_data = [
        ['Vulnerable\nPackages', 'Total\nFindings', 'Critical', 'High', 'Medium', 'Low'],
        [str(vulnerable_packages_count), str(len(findings)), str(severity_counts['critical']), str(severity_counts['high']), 
         str(severity_counts['medium']), str(severity_counts['low'])]
    ]
    
    stats_table = Table(stats_data, colWidths=[1.0*inch]*6)
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FAFAFA')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1A1A1A')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 18),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E5E5')),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#1A1A1A')),  # Vulnerable Packages in black
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),  # White text for Vulnerable Packages
        ('TEXTCOLOR', (2, 1), (2, 1), colors.HexColor('#DC2626')),  # Critical in red
    ]))
    
    story.append(stats_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Metadata
    story.append(Paragraph("Analysis Metadata", heading_style))
    
    metadata_data = [
        ['Target:', str(metadata.get('target', 'N/A'))],
        ['Analysis Type:', str(metadata.get('analysis_type', 'N/A'))],
        ['Start Time:', str(metadata.get('start_time', 'N/A'))],
        ['End Time:', str(metadata.get('end_time', 'N/A'))],
        ['Total Packages:', str(metadata.get('total_packages', summary.get('total_packages', 'N/A')))],
        ['Confidence Threshold:', str(metadata.get('confidence_threshold', 'N/A'))]
    ]
    
    metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
    metadata_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#FAFAFA')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E5E5')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(metadata_table)
    story.append(PageBreak())
    
    # Findings by severity (limit total findings to prevent PDF timeout)
    max_findings_per_severity = {'critical': 20, 'high': 15, 'medium': 10, 'low': 5}
    
    for severity in ['critical', 'high', 'medium', 'low']:
        severity_findings = [f for f in findings if f.get('severity') == severity]
        
        # Limit findings for performance
        original_count = len(severity_findings)
        severity_findings = severity_findings[:max_findings_per_severity[severity]]
        
        if severity_findings:
            # Severity heading
            severity_color = {
                'critical': '#DC2626',
                'high': '#1A1A1A',
                'medium': '#666666',
                'low': '#A0A0A0'
            }[severity]
            
            severity_heading = ParagraphStyle(
                f'{severity}_heading',
                parent=heading_style,
                textColor=colors.HexColor(severity_color)
            )
            
            heading_text = f"{severity.capitalize()} Severity Findings ({len(severity_findings)})"
            if original_count > len(severity_findings):
                heading_text += f" - Showing {len(severity_findings)} of {original_count}"
            
            story.append(Paragraph(heading_text, severity_heading))
            story.append(Spacer(1, 0.1*inch))
            
            # Group by package
            packages = {}
            for finding in severity_findings:
                pkg_key = f"{finding.get('package', 'Unknown')}@{finding.get('version', 'unknown')}"
                if pkg_key not in packages:
                    packages[pkg_key] = {
                        'package': finding.get('package', 'Unknown'),
                        'version': finding.get('version', 'unknown'),
                        'findings': []
                    }
                packages[pkg_key]['findings'].append(finding)
            
            # Render each package
            for pkg_key, pkg_data in packages.items():
                elements = []
                
                # Package header
                pkg_header = Paragraph(
                    f"<b>📦 {pkg_data['package']} v{pkg_data['version']}</b>",
                    ParagraphStyle('PkgHeader', parent=body_style, fontSize=11, spaceAfter=8)
                )
                elements.append(pkg_header)
                
                # Each finding
                for finding in pkg_data['findings']:
                    finding_type = finding.get('finding_type', 'Unknown').replace('_', ' ').title()
                    confidence = finding.get('confidence', 0) * 100
                    is_ai_enhanced = finding.get('source') == 'npm_script_analysis_enhanced'
                    
                    # Finding type with AI Enhanced badge
                    finding_header = f"<b>{finding_type}</b> (Confidence: {confidence:.0f}%)"
                    if is_ai_enhanced:
                        finding_header += " <b>[AI ENHANCED]</b>"
                    
                    elements.append(Paragraph(
                        finding_header,
                        ParagraphStyle('FindingType', parent=body_style, fontSize=10, leftIndent=10)
                    ))
                    
                    # AI-Detected Threats
                    llm_threats = None
                    llm_analysis = None
                    if finding.get('evidence'):
                        for evidence in finding['evidence']:
                            if isinstance(evidence, str):
                                if evidence.startswith('LLM detected:'):
                                    llm_threats = evidence.replace('LLM detected:', '').strip()
                                elif evidence.startswith('Analysis:'):
                                    llm_analysis = evidence.replace('Analysis:', '').strip()
                    
                    if llm_threats:
                        elements.append(Spacer(1, 0.05*inch))
                        elements.append(Paragraph(
                            "<b>AI-DETECTED THREATS:</b>",
                            ParagraphStyle('AIThreatsLabel', parent=body_style, fontSize=9, leftIndent=10, 
                                         textColor=colors.HexColor('#1A1A1A'), spaceAfter=2, spaceBefore=2)
                        ))
                        clean_threats = llm_threats.replace('<', '&lt;').replace('>', '&gt;')
                        if len(clean_threats) > 200:  # Reduced from 300
                            clean_threats = clean_threats[:200] + '...'
                        elements.append(Paragraph(
                            clean_threats,
                            ParagraphStyle('AIThreats', parent=body_style, fontSize=8, leftIndent=20, 
                                         spaceAfter=4, backColor=colors.HexColor('#FFF9E6'))
                        ))
                    
                    if llm_analysis:
                        elements.append(Spacer(1, 0.05*inch))
                        elements.append(Paragraph(
                            "<b>AI ANALYSIS:</b>",
                            ParagraphStyle('AIAnalysisLabel', parent=body_style, fontSize=9, leftIndent=10, 
                                         textColor=colors.HexColor('#1A1A1A'), spaceAfter=2, spaceBefore=2)
                        ))
                        clean_analysis = llm_analysis.replace('<', '&lt;').replace('>', '&gt;')
                        if len(clean_analysis) > 200:  # Reduced from 300
                            clean_analysis = clean_analysis[:200] + '...'
                        elements.append(Paragraph(
                            clean_analysis,
                            ParagraphStyle('AIAnalysis', parent=body_style, fontSize=8, leftIndent=20, 
                                         spaceAfter=4, backColor=colors.HexColor('#F5F5F5'))
                        ))
                    
                    # Evidence (keep all evidence, exclude AI analysis items)
                    if finding.get('evidence'):
                        regular_evidence = [e for e in finding['evidence'] 
                                          if not (isinstance(e, str) and (e.startswith('LLM detected:') or e.startswith('Analysis:')))]
                        if regular_evidence:
                            elements.append(Paragraph("<b>Evidence:</b>", 
                                                     ParagraphStyle('EvidenceLabel', parent=body_style, fontSize=9, leftIndent=10, spaceAfter=2)))
                            for evidence in regular_evidence:
                                # Clean and truncate evidence
                                clean_evidence = str(evidence).replace('<', '&lt;').replace('>', '&gt;')
                                if len(clean_evidence) > 150:
                                    clean_evidence = clean_evidence[:150] + '...'
                                elements.append(Paragraph(
                                    f"• {clean_evidence}",
                                    ParagraphStyle('Evidence', parent=body_style, fontSize=8, leftIndent=20, spaceAfter=2)
                                ))
                    
                    # Recommendations (limit to 3 items)
                    if finding.get('recommendations'):
                        elements.append(Paragraph("<b>Recommendations:</b>", 
                                                 ParagraphStyle('RecLabel', parent=body_style, fontSize=9, leftIndent=10, spaceAfter=2, spaceBefore=4)))
                        for rec in finding['recommendations'][:3]:
                            clean_rec = str(rec).replace('<', '&lt;').replace('>', '&gt;')
                            if len(clean_rec) > 150:
                                clean_rec = clean_rec[:150] + '...'
                            elements.append(Paragraph(
                                f"• {clean_rec}",
                                ParagraphStyle('Rec', parent=body_style, fontSize=8, leftIndent=20, spaceAfter=2)
                            ))
                    
                    elements.append(Spacer(1, 0.1*inch))
                
                # Keep package together if possible
                story.append(KeepTogether(elements))
                story.append(Spacer(1, 0.15*inch))
            
            story.append(PageBreak())
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=body_style,
        fontSize=9,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER
    )
    
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("Generated by Spyder - AI-Powered Supply Chain Security Scanner", footer_style))
    story.append(Paragraph("This report is confidential and intended for authorized personnel only.", footer_style))
    
    # Build PDF
    doc.build(story)

if __name__ == '__main__':
    # Ensure output directory exists
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    
    print("=" * 60)
    print("🕷️  Spyder - AI-Powered Security Scanner")
    print("=" * 60)
    print("\nStarting Flask server...")
    print("Access the application at: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
