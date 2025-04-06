#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess

def main():
    parser = argparse.ArgumentParser(description='Run the University Course Assistant')
    parser.add_argument('--mode', choices=['cli', 'web'], default='cli',
                        help='Run mode: cli (command line interface) or web (Streamlit web interface)')
    args = parser.parse_args()

    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Change to the script directory
    os.chdir(script_dir)
    
    if args.mode == 'cli':
        # Run the CLI version
        print("Starting CLI mode...")
        subprocess.run([sys.executable, "app/main.py"])
    else:
        # Run the Streamlit web app
        print("Starting web interface...")
        # Use the virtual environment's streamlit executable
        venv_dir = os.path.join(script_dir, "venv")
        streamlit_path = os.path.join(venv_dir, "bin", "streamlit")
        if os.path.exists(streamlit_path):
            subprocess.run([streamlit_path, "run", "app/streamlit_app.py"])
        else:
            # Fallback to using the Python module directly
            subprocess.run([sys.executable, "-m", "streamlit", "run", "app/streamlit_app.py"])

if __name__ == "__main__":
    main() 