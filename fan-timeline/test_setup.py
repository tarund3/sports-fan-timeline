#!/usr/bin/env python3
"""
Test script to verify the Sports Fan Timeline project setup.
Run this after setup to ensure everything is working correctly.
"""

import sys
import json
from pathlib import Path

def test_imports():
    """Test that all modules can be imported."""
    print("🔄 Testing imports...")
    
    try:
        from src.timeline import utils, ingest_reddit, parse_pbp, teacher, make_sft
        print("✅ All core modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_schema():
    """Test that the JSON schema is valid."""
    print("🔄 Testing JSON schema...")
    
    try:
        schema_path = Path("schema/timeline.schema.json")
        with open(schema_path, "r") as f:
            schema = json.load(f)
        
        # Test with sample data
        sample_data = {
            "game_id": "test-game",
            "timeline": [
                {
                    "ts": "Q1 10:00",
                    "event": "Test event",
                    "fan_sentiment": "pos"
                }
            ]
        }
        
        import jsonschema
        jsonschema.validate(sample_data, schema)
        print("✅ JSON schema is valid")
        return True
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        return False

def test_sample_data():
    """Test that sample data was generated."""
    print("🔄 Testing sample data...")
    
    sample_files = [
        "data/sample/reddit/2019-12-01-LAL-DAL.jsonl",
        "data/sample/pbp/2019-12-01-LAL-DAL.json",
        "data/sample/teacher/windows.jsonl",
        "data/sft/sft_data.jsonl"
    ]
    
    all_exist = True
    for file_path in sample_files:
        if Path(file_path).exists():
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False
    
    return all_exist

def test_teacher_pipeline():
    """Test that the teacher pipeline can run."""
    print("🔄 Testing teacher pipeline...")
    
    try:
        from src.timeline.teacher import windows_from_sources
        
        # Test with sample data
        reddit_path = "data/sample/reddit/2019-12-01-LAL-DAL.jsonl"
        pbp_path = "data/sample/pbp/2019-12-01-LAL-DAL.json"
        
        if not Path(reddit_path).exists() or not Path(pbp_path).exists():
            print("❌ Sample data not found for testing")
            return False
        
        windows, pbp = windows_from_sources(reddit_path, pbp_path)
        
        if len(windows) > 0:
            print(f"✅ Teacher pipeline generated {len(windows)} windows")
            return True
        else:
            print("❌ Teacher pipeline generated no windows")
            return False
            
    except Exception as e:
        print(f"❌ Teacher pipeline test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Sports Fan Timeline project setup...")
    print("=" * 50)
    
    tests = [
        ("Module imports", test_imports),
        ("JSON schema", test_schema),
        ("Sample data", test_sample_data),
        ("Teacher pipeline", test_teacher_pipeline)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The project is set up correctly.")
        print("\n📋 You can now:")
        print("1. Run the Streamlit demo: streamlit run app/streamlit_app.py")
        print("2. Start the API server: uvicorn src.timeline.serve:app --reload")
        print("3. Train the model: python src/timeline/train_sft.py --config configs/nba.yaml")
    else:
        print("❌ Some tests failed. Please check the errors above and fix any issues.")
        sys.exit(1)

if __name__ == "__main__":
    main()
