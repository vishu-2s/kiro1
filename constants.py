"""
Spyder - Security Constants and Signatures
AI-Powered Supply Chain Security Scanner
This file contains malicious package signatures, legitimate packages, and detection patterns.
"""

from typing import Dict, List, Set
from datetime import datetime

# Version and metadata
CONSTANTS_VERSION = "1.0.0"
LAST_UPDATED = "2025-12-01T22:15:07.157127"

# Known malicious packages - will be updated by update_constants.py
KNOWN_MALICIOUS_PACKAGES: Dict[str, List[Dict]] = {
    "npm": [
        {
            "name": "event-stream",
            "version": ">=3.3.6",
            "reason": "Critical severity vulnerability that affects event-stream and flatmap-stream"
        },
        {
            "name": "eslint-scope",
            "version": ">=3.7.2",
            "reason": "Malicious Package in eslint-scope"
        },
        {
            "name": "flatmap-stream",
            "version": "*",
            "reason": "Malicious Package in flatmap-stream"
        },
        {
            "name": "flatmap-stream",
            "version": ">=3.3.6",
            "reason": "Critical severity vulnerability that affects event-stream and flatmap-stream"
        },
        {
            "name": "flatmap-stream",
            "version": ">=0",
            "reason": "Malicious code in flatmap-stream (npm)"
        },
        {
            "name": "getcookies",
            "version": ">=0",
            "reason": "Malicious Package in getcookies"
        },
        {
            "name": "getcookies",
            "version": ">=0",
            "reason": "Malicious code in getcookies (npm)"
        },
        {
            "name": "http-fetch",
            "version": "*",
            "reason": "Known malicious package"
        },
        {
            "name": "nodemv",
            "version": "*",
            "reason": "Known malicious package"
        },
        {
            "name": "crossenv",
            "version": ">=0",
            "reason": "crossenv is malware"
        },
        {
            "name": "babelcli",
            "version": ">=0",
            "reason": "babelcli is malware"
        },
        {
            "name": "cross-env.js",
            "version": ">=0.0.0",
            "reason": "cross-env.js is malware"
        }
    ],
    "pypi": [
        {
            "name": "python3-dateutil",
            "version": "*",
            "reason": "Known malicious package"
        },
        {
            "name": "jeIlyfish",
            "version": "*",
            "reason": "Known malicious package"
        },
        {
            "name": "urllib4",
            "version": "*",
            "reason": "Known malicious package"
        },
        {
            "name": "requessts",
            "version": ">=0",
            "reason": "Malicious code in requessts (PyPI)"
        },
        {
            "name": "beautifulsoup",
            "version": "*",
            "reason": "Known malicious package"
        },
        {
            "name": "ctx",
            "version": ">=0",
            "reason": "Malware in ctx"
        },
        {
            "name": "ctx",
            "version": ">=0.1.2-1",
            "reason": "Embedded Malicious Code in ctx"
        },
        {
            "name": "ctx",
            "version": ">=0.1.2-1",
            "reason": "Security vulnerability"
        },
        {
            "name": "phpass",
            "version": "*",
            "reason": "Known malicious package"
        }
    ],
    "maven": [
        {
            "name": "org.apache.logging.log4j:log4j-core",
            "version": ">=2.13.0",
            "reason": "Incomplete fix for Apache Log4j vulnerability"
        },
        {
            "name": "org.apache.logging.log4j:log4j-core",
            "version": ">=2.0-beta7",
            "reason": "Improper Input Validation and Injection in Apache Log4j2"
        },
        {
            "name": "org.apache.logging.log4j:log4j-core",
            "version": ">=2.0",
            "reason": "Deserialization of Untrusted Data in Log4j"
        },
        {
            "name": "org.apache.logging.log4j:log4j-core",
            "version": ">=2.13.0",
            "reason": "Remote code injection in Log4j"
        },
        {
            "name": "org.apache.logging.log4j:log4j-core",
            "version": ">=2.4.0",
            "reason": "Apache Log4j2 vulnerable to Improper Input Validation and Uncontrolled Recursion"
        },
        {
            "name": "org.apache.logging.log4j:log4j-core",
            "version": ">=1.0.4",
            "reason": "Apache Log4j 1.x (EOL) allows Denial of Service (DoS)"
        },
        {
            "name": "org.apache.logging.log4j:log4j-core",
            "version": ">=2.13.0",
            "reason": "Improper validation of certificate with host mismatch in Apache Log4j SMTP appender"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "XStream can cause a Denial of Service."
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "XStream is vulnerable to an Arbitrary Code Execution attack"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "XStream is vulnerable to an Arbitrary Code Execution attack"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "XStream is vulnerable to an Arbitrary Code Execution attack"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "Server-Side Forgery Request can be activated unmarshalling with XStream"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "XStream is vulnerable to an Arbitrary Code Execution attack"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "XStream is vulnerable to an attack using Regular Expression for a Denial of Service (ReDos)"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "XStream is vulnerable to an Arbitrary Code Execution attack"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "XStream is vulnerable to an Arbitrary Code Execution attack"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "XStream is vulnerable to an Arbitrary Code Execution attack"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "XStream can cause a Denial of Service"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "XStream is vulnerable to an Arbitrary File Deletion on the local host when unmarshalling as long as the executing process has sufficient rights"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "XStream is vulnerable to a Remote Command Execution attack"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "Denial of service in XStream"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "XStream is vulnerable to an Arbitrary Code Execution attack"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "A Server-Side Forgery Request can be activated unmarshalling with XStream to access data streams from an arbitrary URL referencing a resource in an intranet or the local host"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "Command Injection in Xstream"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "A Server-Side Forgery Request can be activated unmarshalling with XStream to access data streams from an arbitrary URL referencing a resource in an intranet or the local host"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "XStream can cause a Denial of Service by injecting deeply nested objects raising a stack overflow"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "XStream is vulnerable to an Arbitrary Code Execution attack"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "XStream is vulnerable to an Arbitrary Code Execution attack"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "Deserialization of Untrusted Data and Code Injection in xstream"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "XStream is vulnerable to a Denial of Service attack due to stack overflow from a manipulated binary input stream"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "XStream is vulnerable to an Arbitrary Code Execution attack"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "XStream is vulnerable to an Arbitrary Code Execution attack"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "A Server-Side Forgery Request can be activated unmarshalling with XStream to access data streams from an arbitrary URL referencing a resource in an intranet or the local host"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "XStream is vulnerable to a Remote Command Execution attack"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "XStream can cause Denial of Service via stack overflow"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "XStream is vulnerable to a Remote Command Execution attack"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "XStream vulnerable to an Arbitrary File Deletion on the local host when unmarshalling"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "XStream can be used for Remote Code Execution"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "XStream is vulnerable to an Arbitrary Code Execution attack"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "XStream is vulnerable to an Arbitrary Code Execution attack"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "XStream is vulnerable to an Arbitrary Code Execution attack"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "XML External Entity Injection in XStream"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "Denial of Service by injecting highly recursive collections or maps in XStream"
        },
        {
            "name": "com.thoughtworks.xstream:xstream",
            "version": ">=0",
            "reason": "A Server-Side Forgery Request can be activated unmarshalling with XStream to access data streams from an arbitrary URL referencing a resource in an intranet or the local host"
        }
    ],
    "rubygems": [
        {
            "name": "rest-client",
            "version": ">=1.6.10",
            "reason": "rest-client Gem Contains Malicious Code"
        },
        {
            "name": "rest-client",
            "version": ">=1.6.1.a",
            "reason": "rest-client Gem Vulnerable to Session Fixation"
        },
        {
            "name": "rest-client",
            "version": ">=0",
            "reason": "rest-client allows local users to obtain sensitive information by reading the log"
        },
        {
            "name": "strong_password",
            "version": ">=0.0.7",
            "reason": "strong_password Ruby gem malicious version causing Remote Code Execution vulnerability"
        },
        {
            "name": "bootstrap-sass",
            "version": ">=0",
            "reason": "XSS vulnerability that affects bootstrap"
        },
        {
            "name": "bootstrap-sass",
            "version": ">=4.0.0",
            "reason": "Bootstrap vulnerable to Cross-Site Scripting (XSS)"
        },
        {
            "name": "bootstrap-sass",
            "version": ">=2.0.4",
            "reason": "Bootstrap Cross-site Scripting vulnerability"
        },
        {
            "name": "bootstrap-sass",
            "version": ">=4.0.0",
            "reason": "Bootstrap Cross-site Scripting vulnerability"
        },
        {
            "name": "bootstrap-sass",
            "version": ">=0",
            "reason": "Bootstrap Vulnerable to Cross-Site Scripting"
        },
        {
            "name": "bootstrap-sass",
            "version": ">=0",
            "reason": "bootstrap Cross-site Scripting vulnerability"
        },
        {
            "name": "bootstrap-sass",
            "version": ">=3.2.0.3",
            "reason": "Bootstrap-sass contains code execution backdoor"
        }
    ],
    "crates.io": [
        {
            "name": "rustdecimal",
            "version": ">=0",
            "reason": "`rustdecimal` is a malicious crate"
        },
        {
            "name": "rustdecimal",
            "version": ">=0",
            "reason": "Malicious code in rustdecimal (crates.io)"
        },
        {
            "name": "rustdecimal",
            "version": ">=0.0.0-0",
            "reason": "malicious crate `rustdecimal`"
        },
        {
            "name": "rand-core",
            "version": "*",
            "reason": "Known malicious package"
        }
    ],
    "go": [
        {
            "name": "github.com/beego/beego",
            "version": ">=2.0.0",
            "reason": "Access control bypass in Beego"
        },
        {
            "name": "github.com/beego/beego",
            "version": ">=0",
            "reason": "Beego allows Reflected/Stored XSS in Beego's RenderForm() Function Due to Unescaped User Input"
        },
        {
            "name": "github.com/beego/beego",
            "version": ">=2.0.0",
            "reason": "Privilege escalation in beego"
        },
        {
            "name": "github.com/beego/beego",
            "version": ">=0",
            "reason": "Path Traversal in Beego"
        },
        {
            "name": "github.com/beego/beego",
            "version": ">=0",
            "reason": "Beego has Collision Hazards of MD5 in Cache Key Filenames"
        },
        {
            "name": "github.com/beego/beego",
            "version": ">=0",
            "reason": "Beego has a file creation race condition"
        },
        {
            "name": "github.com/beego/beego",
            "version": ">=2.0.0",
            "reason": "Privilege escalation in beego"
        },
        {
            "name": "github.com/beego/beego",
            "version": ">=0",
            "reason": "Incorrect Default Permissions in Beego"
        },
        {
            "name": "github.com/beego/beego",
            "version": ">=0",
            "reason": "Access control bypass in beego"
        },
        {
            "name": "github.com/beego/beego",
            "version": ">=0",
            "reason": "Access control bypass due to broad route matching in github.com/beego/beego and beego/v2"
        },
        {
            "name": "github.com/beego/beego",
            "version": ">=0",
            "reason": "Path traversal in github.com/beego/beego and beego/v2"
        },
        {
            "name": "github.com/beego/beego",
            "version": ">=0",
            "reason": "Access control bypass via incorrect route lookup in github.com/beego/beego and beego/v2"
        },
        {
            "name": "github.com/beego/beego",
            "version": ">=0",
            "reason": "Beego has Collision Hazards of MD5 in Cache Key Filenames in github.com/beego/beego"
        },
        {
            "name": "github.com/beego/beego",
            "version": ">=0",
            "reason": "Beego allows Reflected/Stored XSS in Beego's RenderForm() Function Due to Unescaped User Input in github.com/beego/beego"
        },
        {
            "name": "github.com/unknwon/cae",
            "version": ">=0",
            "reason": "github.com/unknwon/cae Path Traversal vulnerability"
        },
        {
            "name": "github.com/unknwon/cae",
            "version": ">=0",
            "reason": "Path Traversal in github.com/unknwon/cae/zip"
        },
        {
            "name": "github.com/unknwon/cae",
            "version": ">=0",
            "reason": "Path Traversal in github.com/unknwon/cae"
        },
        {
            "name": "github.com/unknwon/cae",
            "version": ">=0",
            "reason": "Path traversal in github.com/unknwon/cae"
        }
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


# ============================================================================
# NPM Script Analysis Constants
# ============================================================================

# Lifecycle scripts that should be analyzed for malicious patterns
NPM_LIFECYCLE_SCRIPTS: List[str] = [
    "preinstall",
    "install",
    "postinstall",
    "preuninstall",
    "uninstall",
    "postuninstall",
    "prepublish",
    "preprepare",
    "prepare",
    "postprepare"
]

# Malicious script patterns organized by severity
NPM_SCRIPT_PATTERNS: Dict[str, Dict[str, List[str]]] = {
    "critical": {
        "remote_code_execution": [
            r'curl\s+[^\s]+\s*\|\s*(?:sh|bash|zsh|fish)',  # curl | sh
            r'wget\s+[^\s]+\s*\|\s*(?:sh|bash|zsh|fish)',  # wget | sh
            r'fetch\s+[^\s]+\s*\|\s*(?:sh|bash|zsh|fish)',  # fetch | sh
            r'\|\s*(?:sh|bash|zsh|fish)\s*$',  # pipe to shell
            r'eval\s*\(\s*(?:curl|wget|fetch)',  # eval with network request
            r'bash\s+-c\s+["\'].*(?:curl|wget)',  # bash -c with network
        ],
        "obfuscated_execution": [
            r'eval\s*\(\s*(?:atob|Buffer\.from|fromCharCode)',  # eval with decoding
            r'exec\s*\(\s*(?:atob|Buffer\.from|fromCharCode)',  # exec with decoding
            r'Function\s*\(\s*(?:atob|Buffer\.from)',  # Function constructor with decoding
        ]
    },
    "high": {
        "system_modification": [
            r'rm\s+-rf\s+(?:/|~|\$HOME)',  # dangerous rm
            r'chmod\s+\+[sx]',  # setuid/setgid
            r'chown\s+root',  # change to root ownership
            r'sudo\s+',  # sudo usage
            r'>/etc/',  # write to /etc
            r'export\s+(?:PATH|LD_PRELOAD|LD_LIBRARY_PATH)',  # dangerous env vars
        ],
        "encoded_commands": [
            r'base64\s+-d',  # base64 decode
            r'atob\s*\(',  # JavaScript base64 decode
            r'Buffer\.from\s*\([^,]+,\s*["\']base64["\']',  # Node.js base64
            r'echo\s+[A-Za-z0-9+/=]{20,}\s*\|\s*base64',  # base64 encoded data
            r'0x[0-9a-fA-F]{8,}',  # hex encoded data
        ],
        "file_exfiltration": [
            r'tar\s+.*\s*\|\s*(?:curl|wget)',  # tar and upload
            r'zip\s+.*\s*&&\s*(?:curl|wget)',  # zip and upload
            r'cat\s+.*\s*\|\s*(?:curl|wget)',  # cat and upload
        ]
    },
    "medium": {
        "suspicious_network": [
            r'curl\s+.*\.(?:tk|ml|ga|cf|cc)\b',  # suspicious TLDs
            r'wget\s+.*\.(?:tk|ml|ga|cf|cc)\b',
            r'https?://(?:\d{1,3}\.){3}\d{1,3}',  # direct IP URLs
            r'discord\.com/api/webhooks',  # Discord webhooks
            r't\.me/',  # Telegram
            r'pastebin\.com',  # Pastebin
        ],
        "dynamic_execution": [
            r'\beval\s*\(',  # eval usage
            r'\bexec\s*\(',  # exec usage
            r'new\s+Function\s*\(',  # Function constructor
            r'setTimeout\s*\([^,]+,',  # setTimeout with code
            r'setInterval\s*\([^,]+,',  # setInterval with code
        ],
        "process_manipulation": [
            r'child_process\.exec',  # child process execution
            r'child_process\.spawn',
            r'require\s*\(\s*["\']child_process["\']',
            r'process\.env\.',  # environment variable access
        ]
    }
}

# Benign script patterns that should reduce confidence scores
NPM_BENIGN_PATTERNS: Dict[str, List[str]] = {
    "build_tools": [
        r'^(?:npm|yarn|pnpm)\s+run\s+\w+',  # npm run commands
        r'^(?:tsc|webpack|rollup|vite|esbuild)\b',  # build tools
        r'^(?:babel|swc)\b',  # transpilers
        r'^node\s+(?:build|dist|scripts)/',  # node scripts
        r'^(?:ng|vue-cli-service)\s+build',  # framework CLIs
    ],
    "dev_tools": [
        r'^(?:eslint|prettier|stylelint)\b',  # linters/formatters
        r'^(?:jest|mocha|vitest|ava)\b',  # test runners
        r'^(?:husky|lint-staged)\b',  # git hooks
        r'^(?:nodemon|ts-node-dev)\b',  # dev servers
    ],
    "safe_file_ops": [
        r'^mkdir\s+-p\s+(?:dist|build|out|lib)\b',  # create build dirs
        r'^(?:cp|mv)\s+\S+\s+(?:dist|build|out|lib)/',  # copy to build dirs
        r'^rm\s+-rf\s+(?:dist|build|out|lib|node_modules)\b',  # clean build dirs
        r'^rimraf\s+(?:dist|build|out|lib)\b',  # rimraf clean
    ],
    "package_management": [
        r'^(?:npm|yarn|pnpm)\s+install\b',  # package install
        r'^(?:npm|yarn|pnpm)\s+ci\b',  # clean install
        r'^(?:npm|yarn|pnpm)\s+update\b',  # package update
    ]
}

# Severity level mapping for pattern categories
NPM_PATTERN_SEVERITY: Dict[str, str] = {
    "remote_code_execution": "critical",
    "obfuscated_execution": "critical",
    "system_modification": "high",
    "encoded_commands": "high",
    "file_exfiltration": "high",
    "suspicious_network": "medium",
    "dynamic_execution": "medium",
    "process_manipulation": "medium"
}

# Confidence score weights for different pattern types
NPM_CONFIDENCE_WEIGHTS: Dict[str, float] = {
    "critical": 0.25,
    "high": 0.20,
    "medium": 0.15,
    "benign": -0.10
}
