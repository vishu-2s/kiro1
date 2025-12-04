"""
Vision Language Model (VLM) tools for Multi-Agent Security Analysis System.

This module provides functions for:
- Image processing and GPT-4 Vision integration
- Security indicator detection in screenshots
- Visual security analysis and anomaly identification
- Visual-package correlation logic
"""

import base64
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
from PIL import Image
import requests

from tools.sbom_tools import SecurityFinding
from config import config
from tools.api_integration import OpenAIAPIClient

logger = logging.getLogger(__name__)

class VisualSecurityFinding:
    """Represents a security finding from visual analysis."""
    
    def __init__(self, finding_type: str, description: str, confidence: float,
                 severity: str, coordinates: Optional[Tuple[int, int, int, int]] = None,
                 evidence: Optional[List[str]] = None, 
                 metadata: Optional[Dict[str, Any]] = None):
        self.finding_type = finding_type
        self.description = description
        self.confidence = confidence
        self.severity = severity
        self.coordinates = coordinates  # (x, y, width, height)
        self.evidence = evidence or []
        self.metadata = metadata or {}
        self.detected_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert visual finding to dictionary representation."""
        return {
            "finding_type": self.finding_type,
            "description": self.description,
            "confidence": self.confidence,
            "severity": self.severity,
            "coordinates": self.coordinates,
            "evidence": self.evidence,
            "metadata": self.metadata,
            "detected_at": self.detected_at
        }

def validate_image_file(image_path: str) -> Tuple[bool, str]:
    """
    Validate image file for processing.
    
    Args:
        image_path: Path to image file
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        path = Path(image_path)
        
        # Check if file exists
        if not path.exists():
            return False, f"Image file not found: {image_path}"
        
        # Check file size
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > config.MAX_IMAGE_SIZE_MB:
            return False, f"Image file too large: {file_size_mb:.1f}MB (max: {config.MAX_IMAGE_SIZE_MB}MB)"
        
        # Check file extension
        extension = path.suffix.lower().lstrip('.')
        if extension not in config.SUPPORTED_IMAGE_FORMATS:
            return False, f"Unsupported image format: {extension} (supported: {', '.join(config.SUPPORTED_IMAGE_FORMATS)})"
        
        # Try to open with PIL to validate image
        with Image.open(path) as img:
            # Check image dimensions (reasonable limits)
            width, height = img.size
            if width > 4096 or height > 4096:
                return False, f"Image dimensions too large: {width}x{height} (max: 4096x4096)"
            
            if width < 50 or height < 50:
                return False, f"Image dimensions too small: {width}x{height} (min: 50x50)"
        
        return True, ""
    
    except Exception as e:
        return False, f"Error validating image: {e}"

def encode_image_to_base64(image_path: str, resize_if_needed: bool = True) -> str:
    """
    Encode image to base64 format for VLM processing.
    
    Args:
        image_path: Path to image file
        resize_if_needed: Whether to resize large images
    
    Returns:
        Base64 encoded image string
    
    Raises:
        ValueError: If image is invalid or processing fails
    """
    is_valid, error_msg = validate_image_file(image_path)
    if not is_valid:
        raise ValueError(error_msg)
    
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (for JPEG compatibility)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Resize if image is too large and resize is enabled
            if resize_if_needed:
                max_dimension = 2048
                width, height = img.size
                
                if width > max_dimension or height > max_dimension:
                    # Calculate new dimensions maintaining aspect ratio
                    if width > height:
                        new_width = max_dimension
                        new_height = int((height * max_dimension) / width)
                    else:
                        new_height = max_dimension
                        new_width = int((width * max_dimension) / height)
                    
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")
            
            # Save to bytes and encode
            import io
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG', quality=85)
            img_byte_arr = img_byte_arr.getvalue()
            
            return base64.b64encode(img_byte_arr).decode('utf-8')
    
    except Exception as e:
        raise ValueError(f"Failed to encode image {image_path}: {e}")

def analyze_image_with_gpt4_vision(image_path: str, 
                                  analysis_prompt: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze image using GPT-4 Vision for security indicators.
    Uses intelligent caching to avoid redundant API calls.
    
    Args:
        image_path: Path to image file
        analysis_prompt: Custom analysis prompt (uses default if None)
    
    Returns:
        Analysis results from GPT-4 Vision
    
    Raises:
        ValueError: If image processing fails
        requests.RequestException: If API call fails
    """
    from tools.cache_manager import get_cache_manager
    
    if not config.OPENAI_API_KEY:
        raise ValueError("OpenAI API key not configured")
    
    # Encode image
    base64_image = encode_image_to_base64(image_path)
    
    # Default security analysis prompt
    if analysis_prompt is None:
        analysis_prompt = """
        Analyze this image for security-related indicators and anomalies. Look for:
        
        1. Security warnings, alerts, or error messages
        2. Suspicious UI elements or unexpected dialogs
        3. Signs of malware, phishing, or social engineering
        4. Unusual network activity indicators
        5. Suspicious file downloads or installations
        6. Authentication prompts or credential requests
        7. System compromise indicators
        8. Unusual application behavior or UI anomalies
        
        Provide a structured analysis with:
        - Description of any security indicators found
        - Severity level (critical, high, medium, low)
        - Confidence level (0.0 to 1.0)
        - Specific locations in the image if applicable
        - Recommended actions
        
        Format your response as JSON with the following structure:
        {
            "findings": [
                {
                    "type": "security_warning|malware_indicator|phishing_attempt|ui_anomaly|network_activity|other",
                    "description": "Detailed description",
                    "severity": "critical|high|medium|low",
                    "confidence": 0.0-1.0,
                    "location": "Description of where in the image",
                    "evidence": ["List of evidence"],
                    "recommendations": ["List of recommended actions"]
                }
            ],
            "overall_risk": "critical|high|medium|low|none",
            "summary": "Brief summary of analysis"
        }
        """
    
    try:
        # Initialize cache manager
        cache_manager = get_cache_manager()
        
        # Generate cache key from image content and prompt
        # Use image hash + prompt hash for cache key
        cache_content = f"{base64_image[:100]}:{analysis_prompt}"  # Use first 100 chars of base64 for efficiency
        cache_key = cache_manager.generate_cache_key(cache_content, prefix="llm_vision")
        
        # Check cache first (Property 6: Cache-First Lookup)
        cached_result = cache_manager.get_llm_analysis(cache_key)
        if cached_result is not None:
            logger.info(f"Cache hit for vision analysis of '{image_path}'")
            # Add current metadata
            cached_result["analysis_timestamp"] = datetime.now().isoformat()
            cached_result["image_path"] = image_path
            cached_result["cached"] = True
            return cached_result
        
        logger.info(f"Cache miss for vision analysis of '{image_path}', calling Vision API")
        
        # Cache miss - perform vision analysis
        # Prepare API request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.OPENAI_API_KEY}"
        }
        
        payload = {
            "model": config.OPENAI_VISION_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": analysis_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": config.AGENT_MAX_TOKENS,
            "temperature": config.AGENT_TEMPERATURE
        }
        
        # Use the new OpenAI API client
        openai_client = OpenAIAPIClient()
        
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": analysis_prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
        
        response = openai_client.create_vision_completion(messages)
        
        if not response.is_success():
            raise ValueError(f"OpenAI API error: {response.error.message}")
        
        result = response.get_data()
        
        # Extract response content
        content = result["choices"][0]["message"]["content"]
        
        # Try to parse as JSON
        try:
            analysis_result = json.loads(content)
        except json.JSONDecodeError:
            # If not valid JSON, wrap in a structure
            analysis_result = {
                "findings": [],
                "overall_risk": "unknown",
                "summary": content,
                "raw_response": content
            }
        
        # Add metadata
        analysis_result["analysis_timestamp"] = datetime.now().isoformat()
        analysis_result["image_path"] = image_path
        analysis_result["model_used"] = config.OPENAI_VISION_MODEL
        analysis_result["cached"] = False
        
        # Store result in cache for future use
        cache_manager.store_llm_analysis(cache_key, analysis_result)
        logger.info(f"Vision analysis for '{image_path}' completed and cached")
        
        return analysis_result
    
    except Exception as e:
        logger.error(f"Error analyzing image with GPT-4 Vision: {e}")
        # Graceful fallback - continue without caching
        raise ValueError(f"Failed to analyze image: {e}")

def detect_security_indicators(image_path: str) -> List[VisualSecurityFinding]:
    """
    Detect security indicators in image using GPT-4 Vision.
    
    Args:
        image_path: Path to image file
    
    Returns:
        List of VisualSecurityFinding objects
    """
    try:
        analysis_result = analyze_image_with_gpt4_vision(image_path)
        findings = []
        
        for finding_data in analysis_result.get("findings", []):
            finding = VisualSecurityFinding(
                finding_type=finding_data.get("type", "unknown"),
                description=finding_data.get("description", ""),
                confidence=float(finding_data.get("confidence", 0.5)),
                severity=finding_data.get("severity", "medium"),
                evidence=finding_data.get("evidence", []),
                metadata={
                    "location": finding_data.get("location"),
                    "recommendations": finding_data.get("recommendations", []),
                    "analysis_model": config.OPENAI_VISION_MODEL
                }
            )
            findings.append(finding)
        
        return findings
    
    except Exception as e:
        logger.error(f"Failed to detect security indicators in {image_path}: {e}")
        return []

def correlate_visual_findings_with_packages(visual_findings: List[VisualSecurityFinding],
                                          sbom_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Correlate visual security findings with package data.
    
    Args:
        visual_findings: List of visual security findings
        sbom_data: SBOM data containing package information
    
    Returns:
        List of correlation results
    """
    correlations = []
    packages = sbom_data.get("packages", [])
    
    for finding in visual_findings:
        potential_correlations = []
        
        # Look for package names mentioned in finding description or evidence
        finding_text = (finding.description + " " + " ".join(finding.evidence)).lower()
        
        for package in packages:
            package_name = package.get("name", "").lower()
            
            # Check if package name appears in finding text
            if package_name and len(package_name) > 3 and package_name in finding_text:
                correlation_confidence = 0.7  # Medium confidence for text match
                
                potential_correlations.append({
                    "package": package,
                    "correlation_type": "text_mention",
                    "correlation_confidence": correlation_confidence,
                    "evidence": f"Package '{package_name}' mentioned in visual finding"
                })
        
        # Look for ecosystem-specific indicators
        ecosystem_indicators = {
            "npm": ["node_modules", "package.json", "npm install", "yarn"],
            "pypi": ["pip install", "requirements.txt", "python", "conda"],
            "maven": ["maven", "pom.xml", "gradle", ".jar"],
            "rubygems": ["gem install", "gemfile", "ruby", "bundler"],
            "crates": ["cargo", "rust", "crates.io"],
            "go": ["go get", "go.mod", "golang"]
        }
        
        for ecosystem, indicators in ecosystem_indicators.items():
            for indicator in indicators:
                if indicator.lower() in finding_text:
                    # Find packages from this ecosystem
                    ecosystem_packages = [p for p in packages if p.get("ecosystem") == ecosystem]
                    
                    for package in ecosystem_packages:
                        potential_correlations.append({
                            "package": package,
                            "correlation_type": "ecosystem_indicator",
                            "correlation_confidence": 0.5,
                            "evidence": f"Ecosystem indicator '{indicator}' found in visual finding"
                        })
        
        if potential_correlations:
            correlation = {
                "visual_finding": finding.to_dict(),
                "package_correlations": potential_correlations,
                "correlation_timestamp": datetime.now().isoformat()
            }
            correlations.append(correlation)
    
    return correlations

def extract_text_from_image(image_path: str) -> str:
    """
    Extract text from image using GPT-4 Vision (OCR functionality).
    
    Args:
        image_path: Path to image file
    
    Returns:
        Extracted text from image
    """
    ocr_prompt = """
    Extract all visible text from this image. Include:
    - All text content, labels, and messages
    - Error messages and warnings
    - Button text and menu items
    - URLs and file paths
    - Any other readable text
    
    Return only the extracted text, one item per line.
    """
    
    try:
        analysis_result = analyze_image_with_gpt4_vision(image_path, ocr_prompt)
        
        # Extract text from response
        if isinstance(analysis_result, dict):
            return analysis_result.get("summary", "")
        else:
            return str(analysis_result)
    
    except Exception as e:
        logger.error(f"Failed to extract text from {image_path}: {e}")
        return ""

def analyze_ui_anomalies(image_path: str) -> List[VisualSecurityFinding]:
    """
    Analyze image for UI anomalies that might indicate security issues.
    
    Args:
        image_path: Path to image file
    
    Returns:
        List of UI anomaly findings
    """
    ui_analysis_prompt = """
    Analyze this image for UI anomalies and suspicious interface elements that might indicate security issues:
    
    1. Unexpected dialogs or pop-ups
    2. Suspicious permission requests
    3. Fake security warnings or alerts
    4. Phishing-style login prompts
    5. Unusual application behavior indicators
    6. Suspicious download prompts
    7. Malware-style UI elements
    8. Social engineering attempts
    
    Focus on elements that seem out of place, suspicious, or potentially malicious.
    
    Format response as JSON:
    {
        "anomalies": [
            {
                "type": "suspicious_dialog|fake_warning|phishing_prompt|malware_ui|other",
                "description": "What makes this suspicious",
                "severity": "critical|high|medium|low",
                "confidence": 0.0-1.0,
                "location": "Where in the image",
                "indicators": ["List of suspicious indicators"]
            }
        ]
    }
    """
    
    try:
        analysis_result = analyze_image_with_gpt4_vision(image_path, ui_analysis_prompt)
        findings = []
        
        anomalies = analysis_result.get("anomalies", [])
        if isinstance(analysis_result.get("findings"), list):
            anomalies.extend(analysis_result["findings"])
        
        for anomaly in anomalies:
            finding = VisualSecurityFinding(
                finding_type="ui_anomaly",
                description=anomaly.get("description", ""),
                confidence=float(anomaly.get("confidence", 0.5)),
                severity=anomaly.get("severity", "medium"),
                evidence=anomaly.get("indicators", []),
                metadata={
                    "anomaly_type": anomaly.get("type", "unknown"),
                    "location": anomaly.get("location"),
                    "analysis_model": config.OPENAI_VISION_MODEL
                }
            )
            findings.append(finding)
        
        return findings
    
    except Exception as e:
        logger.error(f"Failed to analyze UI anomalies in {image_path}: {e}")
        return []

def process_multiple_images(image_paths: List[str]) -> Dict[str, Any]:
    """
    Process multiple images for security analysis.
    
    Args:
        image_paths: List of paths to image files
    
    Returns:
        Combined analysis results from all images
    """
    all_findings = []
    processing_errors = []
    
    for image_path in image_paths:
        try:
            # Validate image first
            is_valid, error_msg = validate_image_file(image_path)
            if not is_valid:
                processing_errors.append(f"{image_path}: {error_msg}")
                continue
            
            # Detect security indicators
            security_findings = detect_security_indicators(image_path)
            
            # Analyze UI anomalies
            ui_findings = analyze_ui_anomalies(image_path)
            
            # Combine findings
            image_findings = security_findings + ui_findings
            
            # Add image metadata to each finding
            for finding in image_findings:
                finding.metadata["source_image"] = image_path
                finding.metadata["image_size"] = _get_image_dimensions(image_path)
            
            all_findings.extend(image_findings)
        
        except Exception as e:
            error_msg = f"Failed to process {image_path}: {e}"
            logger.error(error_msg)
            processing_errors.append(error_msg)
    
    # Calculate overall risk assessment
    risk_levels = [f.severity for f in all_findings]
    overall_risk = _calculate_overall_visual_risk(risk_levels)
    
    return {
        "analysis_timestamp": datetime.now().isoformat(),
        "images_processed": len(image_paths),
        "images_successful": len(image_paths) - len(processing_errors),
        "total_findings": len(all_findings),
        "findings": [finding.to_dict() for finding in all_findings],
        "processing_errors": processing_errors,
        "overall_risk": overall_risk,
        "summary": {
            "critical_findings": len([f for f in all_findings if f.severity == "critical"]),
            "high_findings": len([f for f in all_findings if f.severity == "high"]),
            "medium_findings": len([f for f in all_findings if f.severity == "medium"]),
            "low_findings": len([f for f in all_findings if f.severity == "low"])
        }
    }

def _get_image_dimensions(image_path: str) -> Tuple[int, int]:
    """Get image dimensions."""
    try:
        with Image.open(image_path) as img:
            return img.size
    except Exception:
        return (0, 0)

def _calculate_overall_visual_risk(risk_levels: List[str]) -> str:
    """Calculate overall risk level from individual findings."""
    if not risk_levels:
        return "none"
    
    if "critical" in risk_levels:
        return "critical"
    elif "high" in risk_levels:
        return "high"
    elif "medium" in risk_levels:
        return "medium"
    elif "low" in risk_levels:
        return "low"
    else:
        return "none"

def generate_visual_security_findings(visual_analysis: Dict[str, Any]) -> List[SecurityFinding]:
    """
    Generate SecurityFinding objects from visual analysis results.
    
    Args:
        visual_analysis: Visual analysis results
    
    Returns:
        List of SecurityFinding objects
    """
    findings = []
    
    for finding_data in visual_analysis.get("findings", []):
        evidence = finding_data.get("evidence", [])
        
        # Add visual-specific evidence
        if finding_data.get("metadata", {}).get("location"):
            evidence.append(f"Location in image: {finding_data['metadata']['location']}")
        
        if finding_data.get("metadata", {}).get("source_image"):
            evidence.append(f"Source image: {finding_data['metadata']['source_image']}")
        
        recommendations = finding_data.get("metadata", {}).get("recommendations", [])
        if not recommendations:
            recommendations = [
                "Review the visual indicator for legitimacy",
                "Investigate the source of the security warning or anomaly",
                "Take appropriate action based on the finding type"
            ]
        
        finding = SecurityFinding(
            package="visual_analysis",
            version="*",
            finding_type=finding_data["finding_type"],
            severity=finding_data["severity"],
            confidence=finding_data["confidence"],
            evidence=evidence,
            recommendations=recommendations,
            source="vlm_tools"
        )
        findings.append(finding)
    
    return findings

def save_visual_analysis(analysis_results: Dict[str, Any], output_dir: str) -> str:
    """
    Save visual analysis results to JSON file.
    
    Args:
        analysis_results: Analysis results to save
        output_dir: Output directory
    
    Returns:
        Path to saved file
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"visual_analysis_{timestamp}.json"
    
    file_path = output_path / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=2, default=str)
    
    logger.info(f"Visual analysis results saved to {file_path}")
    return str(file_path)