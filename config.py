"""
Configuration management for Multi-Agent Security Analysis System.
Handles loading configuration from environment variables and .env files.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for the Multi-Agent Security Analysis System."""
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    OPENAI_VISION_MODEL: str = os.getenv("OPENAI_VISION_MODEL", "gpt-4-vision-preview")
    
    # GitHub Configuration
    GITHUB_TOKEN: Optional[str] = os.getenv("GITHUB_TOKEN")
    
    # Web Search API Configuration (for supply chain attack detection)
    SERPER_API_KEY: Optional[str] = os.getenv("SERPER_API_KEY")  # https://serper.dev
    BRAVE_SEARCH_API_KEY: Optional[str] = os.getenv("BRAVE_SEARCH_API_KEY")  # https://brave.com/search/api/
    TAVILY_API_KEY: Optional[str] = os.getenv("TAVILY_API_KEY")  # https://tavily.com
    
    # Snyk API Configuration (for vulnerability checking)
    SNYK_TOKEN: Optional[str] = os.getenv("SNYK_TOKEN")
    
    # System Configuration
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_DURATION_HOURS: int = int(os.getenv("CACHE_DURATION_HOURS", "24"))
    OUTPUT_DIRECTORY: str = os.getenv("OUTPUT_DIRECTORY", "outputs")
    
    # Agent Configuration
    AGENT_TEMPERATURE: float = float(os.getenv("AGENT_TEMPERATURE", "0.1"))
    AGENT_MAX_TOKENS: int = int(os.getenv("AGENT_MAX_TOKENS", "4096"))
    AGENT_TIMEOUT_SECONDS: int = int(os.getenv("AGENT_TIMEOUT_SECONDS", "120"))
    AGENT_MAX_ROUNDS: int = int(os.getenv("AGENT_MAX_ROUNDS", "12"))
    
    # OSV API Configuration
    OSV_API_BASE_URL: str = os.getenv("OSV_API_BASE_URL", "https://api.osv.dev")
    OSV_API_TIMEOUT: int = int(os.getenv("OSV_API_TIMEOUT", "30"))
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "multi_agent_security.log")
    
    # Analysis Configuration
    SKIP_MALICIOUS_DB_UPDATE: bool = os.getenv("SKIP_MALICIOUS_DB_UPDATE", "false").lower() == "true"
    ENABLE_OSV_QUERIES: bool = os.getenv("ENABLE_OSV_QUERIES", "true").lower() == "true"
    FORCE_UPDATE_DB: bool = os.getenv("FORCE_UPDATE_DB", "false").lower() == "true"
    
    # Visual Analysis Configuration
    ENABLE_VISUAL_ANALYSIS: bool = os.getenv("ENABLE_VISUAL_ANALYSIS", "true").lower() == "true"
    MAX_IMAGE_SIZE_MB: int = int(os.getenv("MAX_IMAGE_SIZE_MB", "10"))
    SUPPORTED_IMAGE_FORMATS: list = os.getenv("SUPPORTED_IMAGE_FORMATS", "png,jpg,jpeg,gif,bmp").split(",")
    
    # Security Configuration
    MAX_PACKAGE_NAME_LENGTH: int = int(os.getenv("MAX_PACKAGE_NAME_LENGTH", "100"))
    MAX_SBOM_SIZE_MB: int = int(os.getenv("MAX_SBOM_SIZE_MB", "50"))
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration values."""
        if not cls.OPENAI_API_KEY:
            print("Warning: OPENAI_API_KEY not set. OpenAI features will not work.")
            return False
        
        # Create output directory if it doesn't exist
        output_path = Path(cls.OUTPUT_DIRECTORY)
        output_path.mkdir(exist_ok=True)
        
        return True
    
    @classmethod
    def get_llm_config(cls) -> dict:
        """Get LLM configuration for AutoGen agents."""
        return {
            "config_list": [
                {
                    "model": cls.OPENAI_MODEL,
                    "api_key": cls.OPENAI_API_KEY,
                    "temperature": cls.AGENT_TEMPERATURE,
                    "max_tokens": cls.AGENT_MAX_TOKENS,
                    "timeout": cls.AGENT_TIMEOUT_SECONDS,
                }
            ]
        }
    
    @classmethod
    def get_vision_llm_config(cls) -> dict:
        """Get Vision LLM configuration for visual analysis."""
        return {
            "config_list": [
                {
                    "model": cls.OPENAI_VISION_MODEL,
                    "api_key": cls.OPENAI_API_KEY,
                    "temperature": cls.AGENT_TEMPERATURE,
                    "max_tokens": cls.AGENT_MAX_TOKENS,
                    "timeout": cls.AGENT_TIMEOUT_SECONDS,
                }
            ]
        }

# Global configuration instance
config = Config()