"""
Frontend Tests for SportFinderPro React Component
Tests UI logic, state management, and API integration
"""

import pytest
import json
from pathlib import Path


class TestReactComponent:
    """Test React component structure and logic"""
    
    def test_component_file_exists(self):
        """Test that main React component exists"""
        component = Path('web-interface/SportFinderPro.jsx')
        assert component.exists(), "SportFinderPro.jsx is missing"
    
    def test_component_structure(self):
        """Test React component has required structure"""
        with open('web-interface/SportFinderPro.jsx', 'r') as f:
            content = f.read()
        
        # Check for essential React patterns
        assert 'import React' in content
        assert 'useState' in content
        assert 'useEffect' in content
        assert 'export default' in content
    
    def test_ai_models_configuration(self):
        """Test AI models are properly configured"""
        with open('web-interface/SportFinderPro.jsx', 'r') as f:
            content = f.read()
        
        # Check for model definitions
        assert 'AI_MODELS' in content or 'const AI_MODELS' in content
        assert 'gpt-3.5-turbo' in content  # Fast layer
        assert 'o1-mini' in content  # Reasoning layer
        assert 'gpt-4' in content  # Intelligence layer
    
    def test_no_hardcoded_api_keys(self):
        """Test no hardcoded API keys in React component"""
        with open('web-interface/SportFinderPro.jsx', 'r') as f:
            content = f.read()
        
        # Should use process.env
        assert 'process.env' in content
        
        # Should NOT have actual keys
        lines_with_sk = [line for line in content.split('\n') if 'sk-proj-' in line]
        for line in lines_with_sk:
            # Allow in comments or as placeholders only
            assert '//' in line or 'YOUR_API_KEY' in line or '#' in line, \
                f"Potential hardcoded API key: {line[:50]}"
    
    def test_typing_effect_present(self):
        """Test typing effect functionality exists"""
        with open('web-interface/SportFinderPro.jsx', 'r') as f:
            content = f.read()
        
        # Check for typing effect indicators
        assert 'typing' in content.lower() or 'isTyping' in content
    
    def test_ai_logs_panel_present(self):
        """Test AI logs panel exists"""
        with open('web-interface/SportFinderPro.jsx', 'r') as f:
            content = f.read()
        
        assert 'aiLogs' in content or 'logs' in content
        assert 'addLog' in content or 'setLogs' in content
    
    def test_three_layer_analysis(self):
        """Test three-layer analysis is implemented"""
        with open('web-interface/SportFinderPro.jsx', 'r') as f:
            content = f.read()
        
        # Should have references to all three layers
        assert 'fast' in content.lower()
        assert 'reasoning' in content.lower()
        assert 'intelligence' in content.lower()


class TestReactConfig:
    """Test React configuration files"""
    
    def test_env_example_for_react(self):
        """Test .env.example has React variables"""
        env_example = Path('web-interface/.env.example')
        if env_example.exists():
            with open(env_example) as f:
                content = f.read()
            
            assert 'REACT_APP_' in content, "React env vars should start with REACT_APP_"
    
    def test_readme_exists(self):
        """Test README exists in web-interface"""
        readme = Path('web-interface/README.md')
        assert readme.exists(), "web-interface/README.md is missing"


class TestUIComponents:
    """Test UI component structure"""
    
    def test_lucide_icons_imported(self):
        """Test Lucide React icons are imported"""
        with open('web-interface/SportFinderPro.jsx', 'r') as f:
            content = f.read()
        
        assert 'lucide-react' in content
        # Common icons used
        icon_checks = ['Send', 'Brain', 'Loader']
        for icon in icon_checks:
            if icon in content:
                assert True
                return
        pytest.fail("No Lucide icons found in imports")
    
    def test_error_handling_ui(self):
        """Test error handling in UI"""
        with open('web-interface/SportFinderPro.jsx', 'r') as f:
            content = f.read()
        
        # Should have try-catch blocks
        assert 'catch' in content
        assert 'error' in content.lower()
    
    def test_loading_states(self):
        """Test loading states are managed"""
        with open('web-interface/SportFinderPro.jsx', 'r') as f:
            content = f.read()
        
        assert 'loading' in content.lower()
        assert 'setLoading' in content or 'isLoading' in content


class TestAPIIntegration:
    """Test API integration in frontend"""
    
    def test_fetch_api_used(self):
        """Test fetch API is used for requests"""
        with open('web-interface/SportFinderPro.jsx', 'r') as f:
            content = f.read()
        
        assert 'fetch(' in content
        assert 'await' in content
    
    def test_api_error_handling(self):
        """Test API errors are handled"""
        with open('web-interface/SportFinderPro.jsx', 'r') as f:
            content = f.read()
        
        # Should check response.ok
        assert 'response.ok' in content or 'response.status' in content
    
    def test_json_parsing(self):
        """Test JSON response parsing"""
        with open('web-interface/SportFinderPro.jsx', 'r') as f:
            content = f.read()
        
        assert 'JSON.parse' in content or 'response.json()' in content


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--color=yes'])
