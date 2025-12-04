---
inclusion: fileMatch
fileMatchPattern: "*_analyzer.py|ecosystem_analyzer.py"
---

# Ecosystem Analyzer Development Guide

## Adding a New Ecosystem Analyzer

### Step 1: Create Analyzer Class

Create a new file in `tools/` following the naming pattern `<ecosystem>_analyzer.py`:

```python
# tools/java_analyzer.py
from typing import List, Dict, Any
from tools.ecosystem_analyzer import EcosystemAnalyzer, registry
from tools.sbom_tools import SecurityFinding

class JavaAnalyzer(EcosystemAnalyzer):
    """Java/Maven ecosystem security analyzer."""
    
    @property
    def ecosystem_name(self) -> str:
        """Return ecosystem identifier."""
        return "maven"
    
    def detect_manifest_files(self, directory: str) -> List[str]:
        """
        Detect Java manifest files (pom.xml, build.gradle).
        
        Args:
            directory: Directory to search
            
        Returns:
            List of manifest file paths
        """
        # Implementation
        pass
    
    def extract_dependencies(self, manifest_path: str) -> List[Dict[str, Any]]:
        """
        Extract dependencies from manifest file.
        
        Args:
            manifest_path: Path to manifest file
            
        Returns:
            List of dependency dictionaries with keys:
            - name: Package name
            - version: Package version
            - type: Dependency type (direct/transitive)
        """
        # Implementation
        pass
    
    def analyze_install_scripts(self, directory: str) -> List[SecurityFinding]:
        """
        Analyze build scripts for malicious patterns.
        
        Args:
            directory: Project directory
            
        Returns:
            List of security findings
        """
        # Implementation
        pass
    
    def get_registry_url(self, package_name: str) -> str:
        """
        Get registry API URL for package metadata.
        
        Args:
            package_name: Package identifier
            
        Returns:
            Registry API URL
        """
        return f"https://search.maven.org/solrsearch/select?q=g:{package_name}"
    
    def get_malicious_patterns(self) -> Dict[str, List[str]]:
        """
        Return ecosystem-specific malicious patterns.
        
        Returns:
            Dictionary mapping severity to regex patterns
        """
        return {
            "critical": [
                r'Runtime\.getRuntime\(\)\.exec',
                r'ProcessBuilder\s*\(',
            ],
            "high": [
                r'java\.net\.URL\s*\(',
                r'java\.io\.FileOutputStream',
            ]
        }

# Register the analyzer
registry.register(JavaAnalyzer())
```

### Step 2: Implement Required Methods

#### detect_manifest_files()
- Search for ecosystem-specific manifest files
- Return absolute paths to found files
- Handle nested directories if needed

#### extract_dependencies()
- Parse manifest file format (JSON, XML, TOML, etc.)
- Extract package names and versions
- Include both direct and transitive dependencies
- Return standardized dictionary format

#### analyze_install_scripts()
- Identify installation/build scripts
- Apply malicious pattern detection
- Use AST parsing when possible (avoid executing code)
- Return SecurityFinding objects

#### get_registry_url()
- Return the package registry API endpoint
- Use package name to construct URL
- Ensure URL returns JSON metadata

#### get_malicious_patterns()
- Define regex patterns for malicious code
- Organize by severity (critical, high, medium, low)
- Include ecosystem-specific dangerous APIs
- Document why each pattern is dangerous

### Step 3: Add Tests

Create test file `tests/unit/test_<ecosystem>_analyzer.py`:

```python
import pytest
from tools.java_analyzer import JavaAnalyzer

class TestJavaAnalyzer:
    """Test suite for JavaAnalyzer."""
    
    def test_ecosystem_name(self):
        """Test ecosystem name is correct."""
        analyzer = JavaAnalyzer()
        assert analyzer.ecosystem_name == "maven"
    
    def test_detect_pom_xml(self, tmp_path):
        """Test detection of pom.xml files."""
        # Create test pom.xml
        pom_file = tmp_path / "pom.xml"
        pom_file.write_text("<project></project>")
        
        analyzer = JavaAnalyzer()
        manifests = analyzer.detect_manifest_files(str(tmp_path))
        
        assert len(manifests) == 1
        assert manifests[0].endswith("pom.xml")
    
    def test_extract_dependencies(self):
        """Test dependency extraction from pom.xml."""
        # Test implementation
        pass
    
    def test_malicious_pattern_detection(self):
        """Test detection of malicious patterns."""
        # Test implementation
        pass
```

### Step 4: Register Analyzer

The analyzer is automatically registered when the module is imported:

```python
# At the end of your analyzer file
registry.register(JavaAnalyzer())
```

To use it in the main application:

```python
# In analyze_supply_chain.py or main_github.py
from tools.java_analyzer import JavaAnalyzer  # Auto-registers
```

## Best Practices

### Security
- **Never execute untrusted code** - Use AST/XML/JSON parsing
- **Validate all inputs** - Package names, versions, file paths
- **Sanitize regex patterns** - Prevent ReDoS attacks
- **Rate limit API calls** - Respect registry rate limits

### Performance
- **Cache registry responses** - Use CacheManager
- **Lazy load dependencies** - Only parse when needed
- **Stream large files** - Don't load entire files into memory
- **Timeout long operations** - Set reasonable timeouts

### Code Quality
- **Type hints everywhere** - Use typing module
- **Comprehensive docstrings** - Document all public methods
- **Error handling** - Catch and log exceptions gracefully
- **Unit test coverage** - Aim for 90%+ coverage

### Pattern Detection
- **Start with known malicious patterns** - Research ecosystem-specific attacks
- **Use AST when possible** - More accurate than regex
- **Avoid false positives** - Test against benign code
- **Document pattern rationale** - Explain why each pattern is dangerous

## Common Pitfalls

### ❌ Don't Do This
```python
# Executing untrusted code
exec(open("setup.py").read())

# Blocking on network calls
response = requests.get(url)  # No timeout

# Hardcoding paths
manifest = "/home/user/project/pom.xml"
```

### ✅ Do This Instead
```python
# Parse safely
import ast
tree = ast.parse(open("setup.py").read())

# Use timeouts
response = requests.get(url, timeout=10)

# Use relative paths
manifest = os.path.join(directory, "pom.xml")
```

## Testing Your Analyzer

### Manual Testing
```bash
# Test with real project
python main_github.py --local /path/to/java/project

# Test with SBOM
python main_github.py --sbom /path/to/sbom.json
```

### Automated Testing
```bash
# Run analyzer tests
pytest tests/unit/test_java_analyzer.py -v

# Run with coverage
pytest tests/unit/test_java_analyzer.py --cov=tools.java_analyzer
```

## Integration Checklist

- [ ] Analyzer class implements all required methods
- [ ] Analyzer is registered with registry
- [ ] Unit tests achieve 90%+ coverage
- [ ] Property tests validate correctness properties
- [ ] Integration test with real project
- [ ] Documentation updated
- [ ] Malicious patterns researched and documented
- [ ] Registry API tested and working
- [ ] Error handling for all edge cases
- [ ] Performance tested with large projects
