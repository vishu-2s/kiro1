"""
Security constants and signatures for Multi-Agent Security Analysis System.
This file contains malicious package signatures, legitimate packages, and detection patterns.
"""

from typing import Dict, List, Set
from datetime import datetime

# Version and metadata
CONSTANTS_VERSION = "1.0.0"
LAST_UPDATED = datetime.now().isoformat()

# Known malicious packages - will be updated by update_constants.py
KNOWN_MALICIOUS_PACKAGES: Dict[str, List[Dict]] = {
    "npm": [
        {"name": "event-stream", "version": "3.3.6", "reason": "Backdoor in dependency"},
        {"name": "eslint-scope", "version": "3.7.2", "reason": "Credential harvesting"},
        {"name": "flatmap-stream", "version": "0.1.1", "reason": "Cryptocurrency theft"},
        {"name": "getcookies", "version": "*", "reason": "Data exfiltration"},
        {"name": "http-fetch", "version": "*", "reason": "Typosquat of node-fetch"},
        {"name": "nodemv", "version": "*", "reason": "Malicious code execution"},
        {"name": "crossenv", "version": "*", "reason": "Environment variable theft"},
        {"name": "babelcli", "version": "*", "reason": "Typosquat of babel-cli"},
        {"name": "cross-env.js", "version": "*", "reason": "Typosquat of cross-env"}
    ],
    "pypi": [
        {"name": "python3-dateutil", "version": "*", "reason": "Typosquat of python-dateutil"},
        {"name": "jeIlyfish", "version": "*", "reason": "Typosquat of jellyfish (capital i as l)"},
        {"name": "urllib4", "version": "*", "reason": "Typosquat of urllib3"},
        {"name": "requessts", "version": "*", "reason": "Typosquat of requests"},
        {"name": "beautifulsoup", "version": "*", "reason": "Typosquat of beautifulsoup4"},
        {"name": "pip-tools", "version": "6.6.0", "reason": "Malicious version"},
        {"name": "colorama", "version": "0.4.6", "reason": "Backdoored version"},
        {"name": "ctx", "version": "*", "reason": "Password harvesting"},
        {"name": "phpass", "version": "*", "reason": "Credential theft"}
    ],
    "maven": [
        {"name": "org.apache.logging.log4j:log4j-core", "version": "2.14.1", "reason": "Log4Shell vulnerability"},
        {"name": "com.thoughtworks.xstream:xstream", "version": "1.4.15", "reason": "Remote code execution"},
        {"name": "org.springframework:spring-core", "version": "5.3.18", "reason": "Spring4Shell vulnerability"}
    ],
    "rubygems": [
        {"name": "rest-client", "version": "1.6.10", "reason": "Code injection vulnerability"},
        {"name": "strong_password", "version": "0.0.7", "reason": "Backdoor"},
        {"name": "bootstrap-sass", "version": "3.2.0.2", "reason": "Malicious code"}
    ],
    "crates": [
        {"name": "rustdecimal", "version": "0.2.1", "reason": "Typosquat of rust_decimal"},
        {"name": "rand-core", "version": "0.3.0", "reason": "Compromised randomness"}
    ],
    "go": [
        {"name": "github.com/beego/beego", "version": "1.12.0", "reason": "Session hijacking"},
        {"name": "github.com/unknwon/cae", "version": "0.0.0", "reason": "Backdoor"}
    ]
}

# Popular packages that are commonly typosquatted
TYPOSQUAT_TARGETS: Dict[str, List[str]] = {
    "npm": [
        "react", "lodash", "express", "axios", "webpack", "babel", "eslint",
        "typescript", "vue", "angular", "jquery", "bootstrap", "moment"
    ],
    "pypi": [
        "requests", "numpy", "pandas", "flask", "django", "tensorflow",
        "scikit-learn", "matplotlib", "pillow", "beautifulsoup4", "urllib3"
    ],
    "maven": [
        "spring-boot", "junit", "log4j", "jackson", "hibernate", "apache-commons",
        "slf4j", "mockito", "guava", "gson"
    ],
    "rubygems": [
        "rails", "rake", "bundler", "rspec", "nokogiri", "devise", "puma",
        "sidekiq", "activerecord", "sinatra"
    ],
    "crates": [
        "serde", "tokio", "clap", "rand", "regex", "log", "anyhow", "thiserror",
        "chrono", "uuid"
    ],
    "go": [
        "gin", "echo", "gorm", "cobra", "viper", "logrus", "testify", "mux",
        "grpc", "protobuf"
    ]
}

# Suspicious keywords and patterns
SUSPICIOUS_KEYWORDS: List[str] = [
    # Network/Communication
    "http.get", "urllib.request", "requests.get", "fetch", "axios.get",
    "socket.connect", "net.dial", "tcp.connect", "XMLHttpRequest",
    "curl", "wget", "httplib", "urllib2", "aiohttp",
    
    # System/Shell execution
    "os.system", "subprocess.call", "exec", "eval", "shell_exec",
    "system(", "popen(", "Runtime.exec", "ProcessBuilder",
    "cmd.exe", "/bin/sh", "/bin/bash", "powershell",
    "child_process.spawn", "child_process.exec",
    
    # File system access
    "os.remove", "fs.unlink", "file.delete", "rm -rf", "del /f",
    "os.walk", "glob.glob", "find . -name", "os.listdir",
    "shutil.rmtree", "fs.rmdir", "Files.delete",
    
    # Encoding/Obfuscation
    "base64.decode", "atob(", "btoa(", "hex.decode", "rot13",
    "eval(atob(", "eval(Buffer.from(", "unescape(",
    "String.fromCharCode", "parseInt(", "decodeURIComponent",
    
    # Cryptocurrency/Mining
    "bitcoin", "ethereum", "mining", "crypto", "wallet", "blockchain",
    "stratum", "pool.mining", "xmrig", "monero", "litecoin",
    "cryptonight", "scrypt", "sha256", "mining.pool",
    
    # Data exfiltration
    "document.cookie", "localStorage", "sessionStorage", "process.env",
    "os.environ", "System.getenv", "ENV[", "getenv(",
    "navigator.userAgent", "screen.width", "screen.height",
    
    # Suspicious domains/IPs
    ".tk", ".ml", ".ga", ".cf", "bit.ly", "tinyurl", "pastebin",
    "discord.com/api/webhooks", "telegram.org/bot", "t.me/",
    "raw.githubusercontent.com", "paste.ee", "hastebin",
    
    # Reverse shells and backdoors
    "nc -l", "netcat", "/dev/tcp/", "bash -i", "sh -i",
    "python -c", "perl -e", "ruby -e", "php -r",
    "reverse_tcp", "bind_tcp", "meterpreter",
    
    # Keyloggers and surveillance
    "keylogger", "screenshot", "webcam", "microphone",
    "GetAsyncKeyState", "SetWindowsHookEx", "keydown",
    "addEventListener('keypress'", "onkeypress",
    
    # Privilege escalation
    "sudo", "su -", "runas", "UAC", "privilege",
    "setuid", "chmod +s", "admin", "administrator",
    
    # Anti-analysis
    "debugger", "IsDebuggerPresent", "ptrace", "strace",
    "vm", "virtual", "sandbox", "analysis", "honeypot"
]

# Legitimate package patterns (to reduce false positives)
LEGITIMATE_PATTERNS: Dict[str, List[str]] = {
    "npm": [
        "@types/", "@babel/", "@angular/", "@vue/", "@react/",
        "eslint-", "babel-", "webpack-", "rollup-"
    ],
    "pypi": [
        "django-", "flask-", "pytest-", "sphinx-", "setuptools-",
        "wheel-", "pip-", "numpy-", "scipy-"
    ],
    "maven": [
        "org.springframework", "org.apache", "com.fasterxml.jackson",
        "org.junit", "org.slf4j", "org.hibernate"
    ],
    "rubygems": [
        "rails-", "activerecord-", "activesupport-", "actionpack-",
        "rspec-", "capybara-"
    ],
    "crates": [
        "serde_", "tokio-", "async-", "futures-", "hyper-", "reqwest-"
    ],
    "go": [
        "github.com/", "golang.org/x/", "google.golang.org/",
        "gopkg.in/", "go.uber.org/"
    ]
}

# Ecosystem-specific file patterns
ECOSYSTEM_FILES: Dict[str, List[str]] = {
    "npm": ["package.json", "package-lock.json", "yarn.lock", "npm-shrinkwrap.json"],
    "pypi": ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile", "Pipfile.lock"],
    "maven": ["pom.xml", "build.gradle", "gradle.properties"],
    "rubygems": ["Gemfile", "Gemfile.lock", "*.gemspec"],
    "crates": ["Cargo.toml", "Cargo.lock"],
    "go": ["go.mod", "go.sum", "vendor/modules.txt"]
}

# Cache configuration
CACHE_FILE = "malicious_packages_cache.json"
CACHE_DURATION_HOURS = 24

def get_ecosystem_from_file(filename: str) -> str:
    """Determine ecosystem from package file name."""
    filename_lower = filename.lower()
    
    for ecosystem, files in ECOSYSTEM_FILES.items():
        for pattern in files:
            if pattern.replace("*", "") in filename_lower:
                return ecosystem
    
    return "unknown"

def is_suspicious_package_name(package_name: str, ecosystem: str) -> bool:
    """Check if package name matches suspicious patterns."""
    package_lower = package_name.lower()
    
    # Check against typosquat targets
    if ecosystem in TYPOSQUAT_TARGETS:
        for target in TYPOSQUAT_TARGETS[ecosystem]:
            target_lower = target.lower()
            
            # Skip if names are identical (legitimate package)
            if package_lower == target_lower:
                continue
                
            # 1. Single character substitution (same length, 1 char different)
            if len(package_lower) == len(target_lower):
                diff_count = sum(c1 != c2 for c1, c2 in zip(package_lower, target_lower))
                if diff_count == 1:
                    return True
            
            # 2. Single character addition (target + 1 char)
            if len(package_lower) == len(target_lower) + 1:
                for i in range(len(package_lower)):
                    if package_lower[:i] + package_lower[i+1:] == target_lower:
                        return True
            
            # 3. Single character deletion (target - 1 char)
            if len(package_lower) == len(target_lower) - 1:
                for i in range(len(target_lower)):
                    if target_lower[:i] + target_lower[i+1:] == package_lower:
                        return True
            
            # 4. Common character substitutions
            substitutions = [
                ('o', '0'), ('i', '1'), ('l', '1'), ('s', '5'), ('e', '3'),
                ('a', '@'), ('g', '9'), ('t', '7'), ('b', '6')
            ]
            
            for original, replacement in substitutions:
                if target_lower.replace(original, replacement) == package_lower:
                    return True
                if package_lower.replace(original, replacement) == target_lower:
                    return True
            
            # 5. Adjacent character swapping (transposition)
            if len(package_lower) == len(target_lower):
                for i in range(len(target_lower) - 1):
                    swapped = list(target_lower)
                    swapped[i], swapped[i+1] = swapped[i+1], swapped[i]
                    if ''.join(swapped) == package_lower:
                        return True
    
    return False

def contains_suspicious_keywords(content: str) -> List[str]:
    """Check content for suspicious keywords."""
    found_keywords = []
    content_lower = content.lower()
    
    for keyword in SUSPICIOUS_KEYWORDS:
        if keyword.lower() in content_lower:
            found_keywords.append(keyword)
    
    return found_keywords

def calculate_typosquat_confidence(package_name: str, target: str) -> float:
    """Calculate confidence score for typosquat detection (0.0 to 1.0)."""
    package_lower = package_name.lower()
    target_lower = target.lower()
    
    if package_lower == target_lower:
        return 0.0  # Identical names are not typosquats
    
    # Length difference penalty
    len_diff = abs(len(package_lower) - len(target_lower))
    if len_diff > 2:
        return 0.0  # Too different to be a typosquat
    
    confidence = 0.0
    
    # Single character operations (high confidence)
    if len(package_lower) == len(target_lower):
        diff_count = sum(c1 != c2 for c1, c2 in zip(package_lower, target_lower))
        if diff_count == 1:
            confidence = 0.9  # Single substitution
        elif diff_count == 2:
            # Check for adjacent character swap
            for i in range(len(target_lower) - 1):
                swapped = list(target_lower)
                swapped[i], swapped[i+1] = swapped[i+1], swapped[i]
                if ''.join(swapped) == package_lower:
                    confidence = 0.8  # Character transposition
                    break
    
    # Single character addition/deletion (medium-high confidence)
    elif len_diff == 1:
        if len(package_lower) > len(target_lower):
            # Check for character addition
            for i in range(len(package_lower)):
                if package_lower[:i] + package_lower[i+1:] == target_lower:
                    confidence = 0.7
                    break
        else:
            # Check for character deletion
            for i in range(len(target_lower)):
                if target_lower[:i] + target_lower[i+1:] == package_lower:
                    confidence = 0.7
                    break
    
    # Common character substitutions (medium confidence)
    substitutions = [
        ('o', '0'), ('i', '1'), ('l', '1'), ('s', '5'), ('e', '3'),
        ('a', '@'), ('g', '9'), ('t', '7'), ('b', '6')
    ]
    
    for original, replacement in substitutions:
        if target_lower.replace(original, replacement) == package_lower:
            confidence = max(confidence, 0.6)
        if package_lower.replace(original, replacement) == target_lower:
            confidence = max(confidence, 0.6)
    
    return confidence

def is_legitimate_package_pattern(package_name: str, ecosystem: str) -> bool:
    """Check if package follows legitimate naming patterns."""
    if ecosystem not in LEGITIMATE_PATTERNS:
        return False
    
    package_lower = package_name.lower()
    patterns = LEGITIMATE_PATTERNS[ecosystem]
    
    for pattern in patterns:
        if package_lower.startswith(pattern.lower()):
            return True
    
    return False

def detect_suspicious_network_patterns(content: str) -> List[Dict[str, str]]:
    """Detect suspicious network patterns in package content."""
    import re
    
    suspicious_patterns = []
    
    # IP address patterns
    ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    ips = re.findall(ip_pattern, content)
    for ip in ips:
        # Skip common local/private IPs
        if not (ip.startswith('127.') or ip.startswith('192.168.') or 
                ip.startswith('10.') or ip.startswith('172.')):
            suspicious_patterns.append({
                "type": "suspicious_ip",
                "value": ip,
                "confidence": 0.6
            })
    
    # Suspicious URLs
    url_patterns = [
        r'https?://[a-zA-Z0-9.-]+\.(?:tk|ml|ga|cf|cc)\b',  # Suspicious TLDs
        r'https?://(?:\d{1,3}\.){3}\d{1,3}',  # Direct IP URLs
        r'discord\.com/api/webhooks/[0-9]+/[a-zA-Z0-9_-]+',  # Discord webhooks
        r't\.me/[a-zA-Z0-9_]+',  # Telegram links
    ]
    
    for pattern in url_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            suspicious_patterns.append({
                "type": "suspicious_url",
                "value": match,
                "confidence": 0.8
            })
    
    return suspicious_patterns