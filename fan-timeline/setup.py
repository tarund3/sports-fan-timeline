#!/usr/bin/env python3
"""
Setup script for Sports Fan Timeline project.
This script helps initialize the project and installs dependencies.
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e}")
        if e.stdout:
            print(f"   Stdout: {e.stdout}")
        if e.stderr:
            print(f"   Stderr: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def create_venv():
    """Create and activate virtual environment."""
    venv_path = Path(".venv")
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return True
    
    print("🔄 Creating virtual environment...")
    if run_command("python3 -m venv .venv", "Creating virtual environment"):
        print("✅ Virtual environment created")
        print("📝 To activate it, run:")
        print("   source .venv/bin/activate  # On macOS/Linux")
        print("   .venv\\Scripts\\activate     # On Windows")
        return True
    return False

def install_dependencies():
    """Install project dependencies."""
    if not run_command("pip install --upgrade pip", "Upgrading pip"):
        return False
    
    if not run_command("pip install -r requirements.txt", "Installing dependencies"):
        return False
    
    return True

def generate_sample_data():
    """Generate sample data for demonstration."""
    print("🔄 Generating sample data...")
    
    # Set PYTHONPATH
    os.environ['PYTHONPATH'] = str(Path.cwd())
    
    if run_command("python src/timeline/make_synth.py --out data/sample", "Generating synthetic data"):
        print("✅ Sample data generated")
        return True
    return False

def run_teacher_pipeline():
    """Run the teacher pipeline on sample data."""
    print("🔄 Running teacher pipeline...")
    
    sample_reddit = "data/sample/reddit/2019-12-01-LAL-DAL.jsonl"
    sample_pbp = "data/sample/pbp/2019-12-01-LAL-DAL.json"
    
    if not Path(sample_reddit).exists() or not Path(sample_pbp).exists():
        print("❌ Sample data not found. Please run generate_sample_data() first.")
        return False
    
    if run_command(f"python src/timeline/teacher.py --reddit {sample_reddit} --pbp {sample_pbp} --out data/sample/teacher", "Running teacher pipeline"):
        print("✅ Teacher pipeline completed")
        return True
    return False

def create_sft_data():
    """Create SFT training data."""
    print("🔄 Creating SFT training data...")
    
    teacher_windows = "data/sample/teacher/windows.jsonl"
    if not Path(teacher_windows).exists():
        print("❌ Teacher windows not found. Please run run_teacher_pipeline() first.")
        return False
    
    if run_command(f"python src/timeline/make_sft.py --windows {teacher_windows} --out data/sft/sft_data.jsonl", "Creating SFT data"):
        print("✅ SFT data created")
        return True
    return False

def main():
    """Main setup function."""
    print("🚀 Setting up Sports Fan Timeline project...")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create virtual environment
    if not create_venv():
        print("❌ Failed to create virtual environment")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        print("💡 Try activating the virtual environment first:")
        print("   source .venv/bin/activate")
        sys.exit(1)
    
    # Generate sample data
    if not generate_sample_data():
        print("❌ Failed to generate sample data")
        sys.exit(1)
    
    # Run teacher pipeline
    if not run_teacher_pipeline():
        print("❌ Failed to run teacher pipeline")
        sys.exit(1)
    
    # Create SFT data
    if not create_sft_data():
        print("❌ Failed to create SFT data")
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("=" * 50)
    print("\n📋 Next steps:")
    print("1. Activate the virtual environment:")
    print("   source .venv/bin/activate  # On macOS/Linux")
    print("   .venv\\Scripts\\activate     # On Windows")
    print("\n2. Run the Streamlit demo:")
    print("   streamlit run app/streamlit_app.py")
    print("\n3. Or run the API server:")
    print("   uvicorn src.timeline.serve:app --reload --port 8000")
    print("\n4. (Optional) Train the model:")
    print("   python src/timeline/train_sft.py --config configs/nba.yaml")
    print("\n📚 For more information, see README.md")

if __name__ == "__main__":
    main()
