"""
Reputation Analysis Agent for the multi-agent security analysis system.

This agent assesses package trustworthiness by analyzing metadata from npm and PyPI
registries, calculating reputation scores based on age, downloads, author history,
and maintenance patterns.

**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
"""

import os
import time
import json
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

from agents.base_agent import SecurityAgent
from agents.types import SharedContext
from tools.reputation_service import ReputationScorer
from tools.cache_manager import get_cache_manager

# Load environment variables
load_dotenv()


class ReputationAnalysisAgent(SecurityAgent):
    """
    Agent that assesses package trustworthiness using registry metadata.
    
    This agent:
    - Fetches metadata from npm and PyPI registries
    - Calculates reputation scores based on multiple factors
    - Identifies specific risk factors for packages
    - Analyzes author history and maintenance patterns
    - Provides risk assessment with confidence scores
    - Uses caching to optimize performance
    
    **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
    """
    
    def __init__(self):
        """Initialize the Reputation Analysis Agent."""
        system_message = """You are a package reputation analysis expert. Your role is to:
1. Fetch package metadata from npm and PyPI registries
2. Calculate reputation scores based on age, downloads, author, and maintenance
3. Identify specific risk factors (new package, low downloads, unknown author, etc.)
4. Analyze author history for suspicious patterns
5. Provide detailed risk assessments with confidence scores

Always provide evidence-based assessments and explain your reasoning."""
        
        super().__init__(
            name="ReputationAnalysisAgent",
            system_message=system_message,
            tools=[
                self.fetch_npm_metadata,
                self.fetch_pypi_metadata,
                self.calculate_reputation_score
            ]
        )
        
        # Initialize reputation scorer
        self.reputation_scorer = ReputationScorer(rate_limit_per_second=10.0)
        
        # Initialize cache manager
        self.cache_manager = get_cache_manager(
            backend="sqlite",
            cache_dir=".cache",
            ttl_hours=int(os.getenv("CACHE_DURATION_HOURS", "24")),
            max_size_mb=100
        )
        
        # Ecosystem mapping
        self.ecosystem_mapping = {
            "npm": "npm",
            "pypi": "pypi",
            "python": "pypi"
        }
    
    def analyze(self, context: SharedContext, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyze reputation for all packages in the context.
        
        **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
        
        Args:
            context: Shared context with package information
            timeout: Optional timeout override
        
        Returns:
            Dictionary with reputation analysis results for each package
        """
        start_time = time.time()
        
        # Validate context
        if not self._validate_context(context):
            return self._format_error_result("Invalid context provided", 0.0)
        
        packages = self._get_packages_to_analyze(context)
        ecosystem = context.ecosystem
        
        self._log(f"Analyzing reputation for {len(packages)} packages")
        self._log(f"Ecosystem: {ecosystem}")
        
        # Analyze each package
        package_results = []
        for package_name in packages:
            try:
                # Check timeout
                if timeout and (time.time() - start_time) > timeout:
                    self._log(f"Timeout reached, analyzed {len(package_results)}/{len(packages)} packages", "WARNING")
                    break
                
                # Analyze package reputation
                package_result = self._analyze_package_reputation(package_name, ecosystem, context)
                package_results.append(package_result)
                
                # Log progress
                score = package_result.get("reputation_score", 0)
                risk = package_result.get("risk_level", "unknown")
                if risk in ["high", "critical"]:
                    self._log(f"  [!] {package_name}: score {score:.2f} ({risk} risk)")
                else:
                    self._log(f"  [+] {package_name}: score {score:.2f} ({risk} risk)")
                
            except Exception as e:
                self._log(f"Error analyzing reputation for {package_name}: {str(e)}", "ERROR")
                # Continue with other packages
                package_results.append({
                    "package_name": package_name,
                    "reputation_score": 0.5,
                    "risk_level": "unknown",
                    "error": str(e),
                    "confidence": 0.0
                })
        
        duration = time.time() - start_time
        
        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(package_results)
        
        # Calculate statistics
        high_risk_count = sum(1 for p in package_results if p.get("risk_level") == "high")
        medium_risk_count = sum(1 for p in package_results if p.get("risk_level") == "medium")
        
        return {
            "packages": package_results,
            "total_packages_analyzed": len(package_results),
            "high_risk_packages": high_risk_count,
            "medium_risk_packages": medium_risk_count,
            "confidence": overall_confidence,
            "duration_seconds": duration,
            "source": "registry_metadata"
        }
    
    def _analyze_package_reputation(
        self,
        package_name: str,
        ecosystem: str,
        context: SharedContext
    ) -> Dict[str, Any]:
        """
        Analyze reputation for a single package.
        
        **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
        
        Args:
            package_name: Name of the package
            ecosystem: Package ecosystem (npm, pypi, etc.)
            context: Shared context
        
        Returns:
            Dictionary with reputation analysis for the package
        """
        # Normalize ecosystem name
        normalized_ecosystem = self.ecosystem_mapping.get(ecosystem.lower(), ecosystem.lower())
        
        # Check cache first
        cache_key = self._generate_cache_key(package_name, normalized_ecosystem)
        cached_result = self.cache_manager.get_reputation(cache_key)
        
        if cached_result:
            self._log(f"Using cached reputation data for {package_name}")
            return cached_result
        
        # Fetch metadata and calculate reputation
        try:
            if normalized_ecosystem == "npm":
                metadata = self.fetch_npm_metadata(package_name)
            elif normalized_ecosystem == "pypi":
                metadata = self.fetch_pypi_metadata(package_name)
            else:
                raise ValueError(f"Unsupported ecosystem: {ecosystem}")
            
            # Calculate reputation score
            reputation_data = self.calculate_reputation_score(metadata, normalized_ecosystem)
            
            # Identify risk factors
            risk_factors = self._identify_risk_factors(reputation_data, metadata, normalized_ecosystem)
            
            # Analyze author history
            author_analysis = self._analyze_author_history(metadata, normalized_ecosystem)
            
            # Determine risk level
            risk_level = self._determine_risk_level(reputation_data["score"], risk_factors)
            
            # Calculate confidence
            confidence = self._calculate_confidence(reputation_data, metadata)
            
            # Generate reasoning
            reasoning = self._generate_reasoning(
                reputation_data,
                risk_factors,
                author_analysis,
                risk_level
            )
            
            result = {
                "package_name": package_name,
                "ecosystem": normalized_ecosystem,
                "reputation_score": reputation_data["score"],
                "risk_level": risk_level,
                "factors": reputation_data["factors"],
                "risk_factors": risk_factors,
                "author_analysis": author_analysis,
                "confidence": confidence,
                "reasoning": reasoning,
                "metadata_summary": self._extract_metadata_summary(metadata, normalized_ecosystem)
            }
            
            # Cache the result
            self.cache_manager.store_reputation(cache_key, result, ttl_hours=24)
            
            return result
            
        except Exception as e:
            self._log(f"Error analyzing reputation for {package_name}: {str(e)}", "ERROR")
            return {
                "package_name": package_name,
                "ecosystem": normalized_ecosystem,
                "reputation_score": 0.5,
                "risk_level": "unknown",
                "error": str(e),
                "confidence": 0.0,
                "reasoning": f"Failed to analyze reputation: {str(e)}"
            }
    
    def fetch_npm_metadata(self, package_name: str) -> Dict[str, Any]:
        """
        Fetch package metadata from npm registry.
        
        **Tool function for agent**
        **Validates: Requirement 5.1**
        
        Args:
            package_name: Name of the npm package
        
        Returns:
            Package metadata dictionary
        """
        registry_url = f"https://registry.npmjs.org/{package_name}"
        
        try:
            metadata = self.reputation_scorer._fetch_metadata(registry_url)
            return metadata
        except Exception as e:
            self._log(f"Error fetching npm metadata for {package_name}: {str(e)}", "ERROR")
            raise
    
    def fetch_pypi_metadata(self, package_name: str) -> Dict[str, Any]:
        """
        Fetch package metadata from PyPI registry.
        
        **Tool function for agent**
        **Validates: Requirement 5.1**
        
        Args:
            package_name: Name of the PyPI package
        
        Returns:
            Package metadata dictionary
        """
        registry_url = f"https://pypi.org/pypi/{package_name}/json"
        
        try:
            metadata = self.reputation_scorer._fetch_metadata(registry_url)
            return metadata
        except Exception as e:
            self._log(f"Error fetching PyPI metadata for {package_name}: {str(e)}", "ERROR")
            raise
    
    def calculate_reputation_score(
        self,
        metadata: Dict[str, Any],
        ecosystem: str
    ) -> Dict[str, Any]:
        """
        Calculate reputation score from package metadata.
        
        **Tool function for agent**
        **Validates: Requirement 5.2**
        
        Args:
            metadata: Package metadata from registry
            ecosystem: Package ecosystem
        
        Returns:
            Dictionary with reputation score and factor scores
        """
        try:
            # Use reputation scorer to calculate scores
            reputation_data = self.reputation_scorer._calculate_scores(metadata)
            return reputation_data
        except Exception as e:
            self._log(f"Error calculating reputation score: {str(e)}", "ERROR")
            # Return default scores on error
            return {
                "score": 0.5,
                "factors": {
                    "age_score": 0.5,
                    "downloads_score": 0.5,
                    "author_score": 0.5,
                    "maintenance_score": 0.5
                },
                "flags": ["error_calculating_score"],
                "metadata": metadata
            }
    
    def _identify_risk_factors(
        self,
        reputation_data: Dict[str, Any],
        metadata: Dict[str, Any],
        ecosystem: str
    ) -> List[Dict[str, Any]]:
        """
        Identify specific risk factors for the package.
        
        **Validates: Requirement 5.3**
        
        Args:
            reputation_data: Reputation score data
            metadata: Package metadata
            ecosystem: Package ecosystem
        
        Returns:
            List of risk factor dictionaries
        """
        risk_factors = []
        factors = reputation_data.get("factors", {})
        flags = reputation_data.get("flags", [])
        
        # Check age-related risks
        age_score = factors.get("age_score", 0.5)
        if age_score < 0.3:
            risk_factors.append({
                "type": "new_package",
                "severity": "high",
                "description": "Package is very new (< 30 days old)",
                "score": age_score
            })
        elif age_score < 0.6:
            risk_factors.append({
                "type": "recent_package",
                "severity": "medium",
                "description": "Package is relatively new (< 90 days old)",
                "score": age_score
            })
        
        # Check download-related risks
        downloads_score = factors.get("downloads_score", 0.5)
        if downloads_score < 0.3:
            risk_factors.append({
                "type": "low_downloads",
                "severity": "high",
                "description": "Package has very low download counts",
                "score": downloads_score
            })
        elif downloads_score < 0.6:
            risk_factors.append({
                "type": "moderate_downloads",
                "severity": "medium",
                "description": "Package has moderate download counts",
                "score": downloads_score
            })
        
        # Check author-related risks
        author_score = factors.get("author_score", 0.5)
        if author_score < 0.4:
            risk_factors.append({
                "type": "unknown_author",
                "severity": "high",
                "description": "Package author is unknown or unverified",
                "score": author_score
            })
        elif author_score < 0.7:
            risk_factors.append({
                "type": "new_author",
                "severity": "medium",
                "description": "Package author has limited history",
                "score": author_score
            })
        
        # Check maintenance-related risks
        maintenance_score = factors.get("maintenance_score", 0.5)
        if maintenance_score < 0.3:
            risk_factors.append({
                "type": "abandoned",
                "severity": "high",
                "description": "Package appears to be abandoned (no updates in 2+ years)",
                "score": maintenance_score
            })
        elif maintenance_score < 0.6:
            risk_factors.append({
                "type": "stale",
                "severity": "medium",
                "description": "Package has not been updated recently (1+ year)",
                "score": maintenance_score
            })
        
        # Check for suspicious patterns
        if self._has_suspicious_patterns(metadata, ecosystem):
            risk_factors.append({
                "type": "suspicious_patterns",
                "severity": "high",
                "description": "Package exhibits suspicious patterns in metadata",
                "score": 0.0
            })
        
        return risk_factors
    
    def _analyze_author_history(
        self,
        metadata: Dict[str, Any],
        ecosystem: str
    ) -> Dict[str, Any]:
        """
        Analyze author history for suspicious patterns.
        
        **Validates: Requirement 5.4**
        
        Args:
            metadata: Package metadata
            ecosystem: Package ecosystem
        
        Returns:
            Dictionary with author analysis
        """
        author_info = {
            "author_name": None,
            "is_verified": False,
            "maintainer_count": 0,
            "is_organization": False,
            "suspicious_patterns": []
        }
        
        try:
            if ecosystem == "npm":
                # Extract npm author information
                if "author" in metadata:
                    if isinstance(metadata["author"], dict):
                        author_info["author_name"] = metadata["author"].get("name")
                    elif isinstance(metadata["author"], str):
                        author_info["author_name"] = metadata["author"]
                
                # Check for maintainers
                if "maintainers" in metadata:
                    author_info["maintainer_count"] = len(metadata["maintainers"])
                    if author_info["maintainer_count"] > 1:
                        author_info["is_organization"] = True
                
                # Check for verification
                if "publisher" in metadata:
                    if metadata["publisher"].get("type") == "organization":
                        author_info["is_verified"] = True
                        author_info["is_organization"] = True
                
            elif ecosystem == "pypi":
                # Extract PyPI author information
                if "info" in metadata:
                    info = metadata["info"]
                    author_info["author_name"] = info.get("author")
                    
                    # Check for maintainers
                    if "maintainer" in info and info["maintainer"]:
                        author_info["maintainer_count"] = 1
                    
                    # Check for organization indicators
                    author_email = info.get("author_email", "")
                    if any(domain in author_email for domain in ["@google.com", "@microsoft.com", "@facebook.com"]):
                        author_info["is_organization"] = True
                        author_info["is_verified"] = True
            
            # Detect suspicious patterns
            if not author_info["author_name"]:
                author_info["suspicious_patterns"].append("no_author_information")
            
            if author_info["maintainer_count"] == 0:
                author_info["suspicious_patterns"].append("no_maintainers")
            
            # Check for single-character or very short author names
            if author_info["author_name"] and len(author_info["author_name"]) <= 2:
                author_info["suspicious_patterns"].append("suspicious_author_name")
            
        except Exception as e:
            self._log(f"Error analyzing author history: {str(e)}", "ERROR")
            author_info["suspicious_patterns"].append("error_analyzing_author")
        
        return author_info
    
    def _has_suspicious_patterns(self, metadata: Dict[str, Any], ecosystem: str) -> bool:
        """
        Check for suspicious patterns in package metadata.
        
        Args:
            metadata: Package metadata
            ecosystem: Package ecosystem
        
        Returns:
            True if suspicious patterns detected
        """
        suspicious = False
        
        try:
            # Check for missing critical fields
            if ecosystem == "npm":
                if "name" not in metadata or "version" not in metadata:
                    suspicious = True
                
                # Check for suspicious version patterns (e.g., 99.0.0)
                if "dist-tags" in metadata:
                    latest_version = metadata["dist-tags"].get("latest", "")
                    if latest_version.startswith("99."):
                        suspicious = True
            
            elif ecosystem == "pypi":
                if "info" not in metadata:
                    suspicious = True
                else:
                    info = metadata["info"]
                    if not info.get("name") or not info.get("version"):
                        suspicious = True
            
        except Exception:
            pass
        
        return suspicious
    
    def _determine_risk_level(
        self,
        reputation_score: float,
        risk_factors: List[Dict[str, Any]]
    ) -> str:
        """
        Determine overall risk level based on reputation score and risk factors.
        
        **Validates: Requirement 5.5**
        
        Args:
            reputation_score: Overall reputation score (0.0-1.0)
            risk_factors: List of identified risk factors
        
        Returns:
            Risk level string: "low", "medium", "high", or "critical"
        """
        # Count severity levels
        high_severity_count = sum(
            1 for rf in risk_factors if rf.get("severity") == "high"
        )
        medium_severity_count = sum(
            1 for rf in risk_factors if rf.get("severity") == "medium"
        )
        
        # Determine risk level
        if high_severity_count >= 2 or reputation_score < 0.3:
            return "high"
        elif high_severity_count >= 1 or reputation_score < 0.5:
            return "medium"
        elif medium_severity_count >= 1 or reputation_score < 0.7:
            return "medium"
        else:
            return "low"
    
    def _calculate_confidence(
        self,
        reputation_data: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> float:
        """
        Calculate confidence score for reputation analysis.
        
        **Validates: Requirement 5.5**
        
        Args:
            reputation_data: Reputation score data
            metadata: Package metadata
        
        Returns:
            Confidence score (0.0-1.0)
        """
        # Start with high confidence
        confidence = 0.95
        
        # Reduce confidence if metadata is incomplete
        factors = reputation_data.get("factors", {})
        
        # Check if all factors have non-default scores
        if all(score == 0.5 for score in factors.values()):
            confidence -= 0.2
        
        # Reduce confidence for missing metadata fields
        if "error" in reputation_data.get("flags", []):
            confidence -= 0.3
        
        # Increase confidence if we have detailed metadata
        if metadata and len(metadata) > 5:
            confidence = min(1.0, confidence + 0.05)
        
        return max(0.0, min(1.0, confidence))
    
    def _generate_reasoning(
        self,
        reputation_data: Dict[str, Any],
        risk_factors: List[Dict[str, Any]],
        author_analysis: Dict[str, Any],
        risk_level: str
    ) -> str:
        """
        Generate reasoning for the reputation assessment.
        
        **Validates: Requirement 5.5**
        
        Args:
            reputation_data: Reputation score data
            risk_factors: List of risk factors
            author_analysis: Author history analysis
            risk_level: Determined risk level
        
        Returns:
            Reasoning string
        """
        reasoning_parts = []
        
        # Overall assessment
        score = reputation_data.get("score", 0.5)
        reasoning_parts.append(f"Package reputation score: {score:.2f} (risk level: {risk_level}).")
        
        # Factor breakdown
        factors = reputation_data.get("factors", {})
        if factors:
            low_factors = [
                name.replace("_score", "")
                for name, value in factors.items()
                if value < 0.5
            ]
            if low_factors:
                reasoning_parts.append(f"Low scores in: {', '.join(low_factors)}.")
        
        # Risk factors
        if risk_factors:
            high_risk = [rf for rf in risk_factors if rf.get("severity") == "high"]
            if high_risk:
                risk_descriptions = [rf.get("description", "") for rf in high_risk]
                reasoning_parts.append(f"High-risk factors: {'; '.join(risk_descriptions)}.")
        
        # Author analysis
        if author_analysis.get("suspicious_patterns"):
            reasoning_parts.append(
                f"Author concerns: {', '.join(author_analysis['suspicious_patterns'])}."
            )
        elif author_analysis.get("is_verified"):
            reasoning_parts.append("Package from verified/organization author.")
        
        return " ".join(reasoning_parts)
    
    def _extract_metadata_summary(
        self,
        metadata: Dict[str, Any],
        ecosystem: str
    ) -> Dict[str, Any]:
        """
        Extract key metadata fields for summary.
        
        Args:
            metadata: Full package metadata
            ecosystem: Package ecosystem
        
        Returns:
            Dictionary with summary metadata
        """
        summary = {}
        
        try:
            if ecosystem == "npm":
                summary["name"] = metadata.get("name")
                summary["version"] = metadata.get("dist-tags", {}).get("latest")
                summary["description"] = metadata.get("description")
                summary["license"] = metadata.get("license")
                
                if "time" in metadata:
                    summary["created"] = metadata["time"].get("created")
                    summary["modified"] = metadata["time"].get("modified")
                
            elif ecosystem == "pypi":
                if "info" in metadata:
                    info = metadata["info"]
                    summary["name"] = info.get("name")
                    summary["version"] = info.get("version")
                    summary["description"] = info.get("summary")
                    summary["license"] = info.get("license")
                    summary["author"] = info.get("author")
        
        except Exception:
            pass
        
        return summary
    
    def _calculate_overall_confidence(self, package_results: List[Dict[str, Any]]) -> float:
        """
        Calculate overall confidence across all packages.
        
        Args:
            package_results: List of package analysis results
        
        Returns:
            Overall confidence score (0.0-1.0)
        """
        if not package_results:
            return 0.0
        
        # Average confidence across all packages
        total_confidence = sum(p.get("confidence", 0.0) for p in package_results)
        avg_confidence = total_confidence / len(package_results)
        
        return avg_confidence
    
    def _generate_cache_key(self, package: str, ecosystem: str) -> str:
        """
        Generate cache key for reputation data.
        
        Args:
            package: Package name
            ecosystem: Package ecosystem
        
        Returns:
            Cache key string
        """
        return f"reputation:{ecosystem}:{package}"
