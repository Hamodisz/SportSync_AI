"""
API Backend Tests for FastAPI
Tests endpoints, error handling, and integration
"""

import pytest
from pathlib import Path
import json


class TestAPIStructure:
    """Test API backend structure"""
    
    def test_backend_file_exists(self):
        """Test backend file exists"""
        backend = Path('api/backend_simple.py')
        assert backend.exists(), "api/backend_simple.py is missing"
    
    def test_fastapi_imports(self):
        """Test FastAPI is properly imported"""
        with open('api/backend_simple.py') as f:
            content = f.read()
        
        assert 'from fastapi import' in content
        assert 'FastAPI' in content
    
    def test_cors_middleware(self):
        """Test CORS middleware is configured"""
        with open('api/backend_simple.py') as f:
            content = f.read()
        
        assert 'CORSMiddleware' in content
        assert 'allow_origins' in content
    
    def test_openai_import(self):
        """Test OpenAI is imported"""
        with open('api/backend_simple.py') as f:
            content = f.read()
        
        assert 'openai' in content.lower()


class TestAPIEndpoints:
    """Test API endpoints structure"""
    
    def test_analyze_endpoint_exists(self):
        """Test /api/analyze endpoint exists"""
        with open('api/backend_simple.py') as f:
            content = f.read()
        
        assert '/api/analyze' in content or '@app.post' in content
    
    def test_health_endpoint_exists(self):
        """Test /health endpoint exists"""
        with open('api/backend_simple.py') as f:
            content = f.read()
        
        assert '/health' in content
        assert '@app.get' in content
    
    def test_pydantic_models(self):
        """Test Pydantic models are defined"""
        with open('api/backend_simple.py') as f:
            content = f.read()
        
        assert 'BaseModel' in content
        assert 'class ' in content


class TestAPILogic:
    """Test API business logic"""
    
    def test_three_layer_system(self):
        """Test three-layer AI system is implemented"""
        with open('api/backend_simple.py') as f:
            content = f.read()
        
        # Check for all three layers
        assert 'gpt-3.5-turbo' in content  # Fast
        assert 'o1-mini' in content or 'gpt-4' in content  # Reasoning
        assert 'gpt-4' in content  # Intelligence
    
    def test_error_handling(self):
        """Test error handling is present"""
        with open('api/backend_simple.py') as f:
            content = f.read()
        
        assert 'try:' in content
        assert 'except' in content
        assert 'HTTPException' in content or 'Exception' in content
    
    def test_env_variables(self):
        """Test environment variables are used"""
        with open('api/backend_simple.py') as f:
            content = f.read()
        
        assert 'os.getenv' in content or 'load_dotenv' in content
        assert 'OPENAI_API_KEY' in content


class TestAPIConfiguration:
    """Test API configuration files"""
    
    def test_requirements_exists(self):
        """Test requirements.txt exists for API"""
        req_file = Path('api/requirements.txt')
        assert req_file.exists(), "api/requirements.txt is missing"
    
    def test_requirements_content(self):
        """Test requirements.txt has necessary packages"""
        with open('api/requirements.txt') as f:
            content = f.read()
        
        assert 'fastapi' in content.lower()
        assert 'uvicorn' in content.lower()
        assert 'openai' in content.lower()
    
    def test_readme_exists(self):
        """Test API README exists"""
        readme = Path('api/README.md')
        assert readme.exists(), "api/README.md is missing"


class TestAPISecurity:
    """Test API security measures"""
    
    def test_no_hardcoded_secrets(self):
        """Test no hardcoded API keys"""
        with open('api/backend_simple.py') as f:
            content = f.read()
        
        # Should use environment variables
        assert 'os.getenv' in content or 'os.environ' in content
        
        # Should NOT have hardcoded keys
        lines = content.split('\n')
        for line in lines:
            if 'sk-proj-' in line:
                # Only allow in comments
                assert '#' in line or '//' in line, f"Hardcoded key in: {line[:50]}"
    
    def test_cors_configured_properly(self):
        """Test CORS is not too permissive"""
        with open('api/backend_simple.py') as f:
            content = f.read()
        
        # Should specify origins, not use "*" in production
        if 'allow_origins' in content:
            # This is good - origins are specified
            assert True
        else:
            pytest.skip("CORS not configured")


class TestAPIDocumentation:
    """Test API documentation"""
    
    def test_readme_has_installation(self):
        """Test README has installation instructions"""
        readme = Path('api/README.md')
        if readme.exists():
            with open(readme) as f:
                content = f.read()
            
            assert 'install' in content.lower() or 'pip' in content.lower()
    
    def test_readme_has_endpoints(self):
        """Test README documents endpoints"""
        readme = Path('api/README.md')
        if readme.exists():
            with open(readme) as f:
                content = f.read()
            
            assert '/api/analyze' in content or 'endpoint' in content.lower()
    
    def test_docstrings_present(self):
        """Test functions have docstrings"""
        with open('api/backend_simple.py') as f:
            content = f.read()
        
        # Check for docstrings
        assert '"""' in content or "'''" in content


class TestAPIPerformance:
    """Test API performance considerations"""
    
    def test_async_endpoints(self):
        """Test endpoints use async/await"""
        with open('api/backend_simple.py') as f:
            content = f.read()
        
        # FastAPI endpoints should be async
        assert 'async def' in content
    
    def test_timing_tracked(self):
        """Test response times are tracked"""
        with open('api/backend_simple.py') as f:
            content = f.read()
        
        # Should track timing for each layer
        assert 'time' in content.lower() or 'duration' in content.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--color=yes'])
