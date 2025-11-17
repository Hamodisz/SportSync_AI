"""
SportSync AI - Admin Interface Entry Point for Streamlit Cloud

This entry point configures the Python path so that imports from 'src' work correctly
on Streamlit Cloud. It then imports and runs the full admin interface.

Deploy to Streamlit Cloud using this file as the main entry point:
- Repository: Hamodisz/SportSync_AI
- Branch: main
- Main file path: streamlit_app.py (NOT apps/app_streamlit.py)
"""

import sys
from pathlib import Path

# Add project root to Python path
# This allows 'from src.core...' imports to work correctly
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Verify the path was added
print(f"Added to Python path: {project_root}")
print(f"Python path: {sys.path[:3]}")

# Now import and run the admin app
# All the imports in app_streamlit.py should now work
from apps.app_streamlit import *

# Streamlit will automatically execute the script
print("Streamlit admin interface loaded successfully!")
