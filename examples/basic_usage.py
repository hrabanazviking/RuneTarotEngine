# RuneTarot — Basic Usage Example

"""
Example: How to use RuneTarot as a Python library.
This demonstrates programmatic access to the engine
without the TUI or CLI.
"""

import sys
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.engine import RuneTarotEngine


def main():
    # Initialize the engine
    engine = RuneTarotEngine()
    
    if not engine.initialize_subsystems():
        print("Engine initialization failed!")
        sys.exit(1)
    
    # List available spreads
    print("Available spreads:")
    for info in engine.spread_manager.list_spreads():
        print(f"  • {info['name']} ({info['card_count']} cards) — {info['tradition']}")
    print()
    
    # Generate a Celtic Cross reading
    result = engine.generate_reading(
        spread_name="celtic_cross",
        question="What is the path forward?",
    )
    
    # Print the reading
    print(result["reading_text"])
    
    # Check if AI is available
    if engine.is_ai_available():
        print("\n✦ AI interpretation available!")
        print(result["ai_interpretation"])
    else:
        print("\n⚠ AI not available — set API key in config")


if __name__ == "__main__":
    main()
