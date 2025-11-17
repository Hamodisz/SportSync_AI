"""
SportSync AI V2 - Main Interface Entry Point for Streamlit Cloud

This entry point configures the Python path and runs the full V2 interface with:
- 10 Deep Questions system
- Multi-page UI (welcome, questions, analysis, results)
- Modern design with custom CSS
- Full personality analysis with Layer-Z Enhanced
- 15 psychological frameworks integration
- Video generation and sport recommendations

Deploy to Streamlit Cloud using this file as the main entry point:
- Repository: Hamodisz/SportSync_AI
- Branch: main
- Main file path: streamlit_app.py
"""

import sys
from pathlib import Path

# Add project root to Python path
# This allows all imports to work correctly on Streamlit Cloud
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now import and run the main V2 interface
# This loads the full-featured interface with all pages
from apps.main import main

# Run the application
if __name__ == "__main__":
    main()
