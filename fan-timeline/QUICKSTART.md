# 🚀 Quick Start Guide

Get the Sports Fan Timeline project running in under 5 minutes!

## Prerequisites

- Python 3.8+
- pip (Python package installer)

## Option 1: Automated Setup (Recommended)

```bash
# 1. Navigate to the project directory
cd fan-timeline

# 2. Run the automated setup
python setup.py

# 3. Activate the virtual environment
source .venv/bin/activate  # On macOS/Linux
# OR
.venv\Scripts\activate     # On Windows

# 4. Test the setup
python test_setup.py

# 5. Run the demo!
streamlit run app/streamlit_app.py
```

## Option 2: Manual Setup

```bash
# 1. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# OR
.venv\Scripts\activate     # On Windows

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Set Python path
export PYTHONPATH=$(pwd)  # On macOS/Linux
# OR
set PYTHONPATH=%cd%       # On Windows

# 4. Generate sample data
python src/timeline/make_synth.py --out data/sample

# 5. Run teacher pipeline
python src/timeline/teacher.py --reddit data/sample/reddit/2019-12-01-LAL-DAL.jsonl --pbp data/sample/pbp/2019-12-01-LAL-DAL.json --out data/sample/teacher

# 6. Create SFT data
python src/timeline/make_sft.py --windows data/sample/teacher/windows.jsonl --out data/sft/sft_data.jsonl

# 7. Run the demo
streamlit run app/streamlit_app.py
```

## What You'll Get

✅ **Working demo** with synthetic NBA game data  
✅ **Teacher pipeline** generating training data  
✅ **SFT data** ready for model training  
✅ **Streamlit app** showing timeline + sentiment  
✅ **FastAPI server** for programmatic access

## Next Steps

1. **Explore the demo** - Generate sample games and see the timeline
2. **Upload your data** - Use real Reddit threads and PBP data
3. **Train a model** - Run QLoRA fine-tuning (requires GPU)
4. **Customize** - Modify thresholds, add new sports, etc.

## Troubleshooting

**Import errors?** Make sure you're in the virtual environment and PYTHONPATH is set.

**Missing dependencies?** Run `pip install -r requirements.txt` again.

**Schema validation errors?** Check that your data matches the expected format.

## Need Help?

- Check the main README.md for detailed documentation
- Look at the example data in `data/sample/` for format reference
- Review the PRD.txt for project requirements and goals

---

🎯 **Goal**: Get you from zero to working demo as quickly as possible!
