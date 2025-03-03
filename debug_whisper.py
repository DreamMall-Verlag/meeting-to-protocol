import sys
import importlib
import importlib.util

def check_module(name):
    """Check if a module can be imported and print its location."""
    print(f"Checking module: {name}")
    try:
        # Try to import the module
        module = importlib.import_module(name)
        print(f"  Successfully imported {name}")
        print(f"  Module location: {module.__file__}")
        print(f"  Module version: {getattr(module, '__version__', 'Unknown')}")
        print(f"  Module functions: {dir(module)[:10]}...")
        return module
    except ImportError as e:
        print(f"  Failed to import {name}: {e}")
        return None
    except Exception as e:
        print(f"  Error importing {name}: {e}")
        return None

def main():
    print("Python version:", sys.version)
    
    # Check for any module named whisper
    check_module("whisper")
    
    # Check for openai.whisper (part of the OpenAI API)
    try:
        import openai
        print("OpenAI version:", openai.__version__)
        if hasattr(openai, "whisper"):
            print("OpenAI has whisper attribute")
    except ImportError:
        print("OpenAI not installed")
    
    # List all installed packages
    print("\nListing all installed packages with 'whisper' in the name:")
    import pkg_resources
    for pkg in pkg_resources.working_set:
        if "whisper" in pkg.key.lower():
            print(f"  {pkg.key} ({pkg.version}) at {pkg.location}")

if __name__ == "__main__":
    main()
