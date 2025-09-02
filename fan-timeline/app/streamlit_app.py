import streamlit as st
import json
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

# from timeline.teacher import windows_from_sources, aggregate_sentiment, label_sentiment, write_event
# from timeline.make_synth import generate_synthetic_reddit, generate_synthetic_pbp

st.set_page_config(
    page_title="Sports Fan Timeline",
    page_icon="🏀",
    layout="wide"
)

st.title("🏀 Sports Fan Thread → Timeline + Sentiment")
st.markdown("Turn chaotic live Reddit game threads into a **clean, minute-by-minute fan timeline** with sentiment and top themes.")

# Sidebar
st.sidebar.header("Game Selection")
demo_mode = st.sidebar.radio("Mode", ["Synthetic Demo", "Upload Data"])

if demo_mode == "Synthetic Demo":
    st.sidebar.markdown("**Synthetic Demo Mode**")
    st.sidebar.markdown("Generates sample data for demonstration.")
    
    if st.sidebar.button("Generate Sample Game"):
        with st.spinner("Generating synthetic data..."):
            # Generate synthetic data
            reddit_data = generate_synthetic_reddit("2019-12-01-LAL-DAL", 100)
            pbp_data = generate_synthetic_pbp()
            
            # Process with teacher pipeline
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as reddit_file:
                for comment in reddit_data:
                    reddit_file.write(json.dumps(comment) + '\n')
                reddit_path = reddit_file.name
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as pbp_file:
                json.dump(pbp_data, pbp_file)
                pbp_path = pbp_file.name
            
            try:
                windows, pbp = windows_from_sources(reddit_path, pbp_path)
                
                # Build timeline
                timeline = []
                for w in windows:
                    sent_val = aggregate_sentiment(w.get("comments", []))
                    sent_lbl = label_sentiment(sent_val, 0.15, -0.15)
                    event = write_event(w, max_len=120)
                    
                    timeline.append({
                        "ts": w["window_label"],
                        "event": event,
                        "fan_sentiment": sent_lbl,
                        "comments_text": w.get("comments_text", "")
                    })
                
                # Extract themes
                from collections import Counter
                all_text = " ".join(w.get("comments_text", "") for w in windows)
                words = [w.lower() for w in all_text.split() if len(w) > 3]
                themes = [word for word, count in Counter(words).most_common(20) if count >= 3][:5]
                
                st.session_state.timeline = timeline
                st.session_state.themes = themes
                st.session_state.reddit_data = reddit_data
                st.session_state.pbp_data = pbp_data
                
                st.success("Sample game generated successfully!")
                
            finally:
                os.unlink(reddit_path)
                os.unlink(pbp_path)

else:
    st.sidebar.markdown("**Upload Mode**")
    st.sidebar.markdown("Upload your own Reddit and PBP data.")
    
    uploaded_reddit = st.sidebar.file_uploader("Reddit Thread (JSONL)", type=['jsonl'])
    uploaded_pbp = st.sidebar.file_uploader("Play-by-Play (JSON)", type=['json'])
    
    if uploaded_reddit and uploaded_pbp and st.sidebar.button("Process Data"):
        with st.spinner("Processing uploaded data..."):
            try:
                # Parse uploaded files
                reddit_data = []
                for line in uploaded_reddit:
                    reddit_data.append(json.loads(line.decode()))
                
                pbp_data = json.loads(uploaded_pbp.read())
                
                # Process with teacher pipeline
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as reddit_file:
                    for comment in reddit_data:
                        reddit_file.write(json.dumps(comment) + '\n')
                    reddit_path = reddit_file.name
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as pbp_file:
                    json.dump(pbp_data, pbp_file)
                    pbp_path = pbp_file.name
                
                try:
                    windows, pbp = windows_from_sources(reddit_path, pbp_path)
                    
                    # Build timeline
                    timeline = []
                    for w in windows:
                        sent_val = aggregate_sentiment(w.get("comments", []))
                        sent_lbl = label_sentiment(sent_val, 0.15, -0.15)
                        event = write_event(w, max_len=120)
                        
                        timeline.append({
                            "ts": w["window_label"],
                            "event": event,
                            "fan_sentiment": sent_lbl,
                            "comments_text": w.get("comments_text", "")
                        })
                    
                    # Extract themes
                    from collections import Counter
                    all_text = " ".join(w.get("comments_text", "") for w in windows)
                    words = [w.lower() for w in all_text.split() if len(w) > 3]
                    themes = [word for word, count in Counter(words).most_common(20) if count >= 3][:5]
                    
                    st.session_state.timeline = timeline
                    st.session_state.themes = themes
                    st.session_state.reddit_data = reddit_data
                    st.session_state.pbp_data = pbp_data
                    
                    st.success("Data processed successfully!")
                    
                finally:
                    os.unlink(reddit_path)
                    os.unlink(pbp_path)
                    
            except Exception as e:
                st.error(f"Error processing data: {str(e)}")

# Main content area
if 'timeline' in st.session_state:
    # Display themes
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.header("📊 Game Timeline")
        
        # Timeline display
        for i, event in enumerate(st.session_state.timeline):
            # Sentiment emoji
            sentiment_emoji = {
                "pos": "😊",
                "neg": "😞", 
                "mixed": "😐"
            }.get(event["fan_sentiment"], "❓")
            
            # Create expandable section for each event
            with st.expander(f"{sentiment_emoji} {event['ts']} - {event['event']}", expanded=True):
                st.markdown(f"**Sentiment:** {event['fan_sentiment']}")
                st.markdown("**Representative Comments:**")
                st.text(event['comments_text'])
    
    with col2:
        st.header("🎯 Top Themes")
        for theme in st.session_state.themes:
            st.markdown(f"- {theme}")
        
        st.header("📋 Export")
        
        # JSON export
        timeline_data = {
            "game_id": "2019-12-01-LAL-DAL",
            "timeline": st.session_state.timeline,
            "top_themes": st.session_state.themes,
            "notes": "Generated using teacher pipeline"
        }
        
        json_str = json.dumps(timeline_data, indent=2)
        st.download_button(
            label="Download JSON",
            data=json_str,
            file_name="timeline.json",
            mime="application/json"
        )
        
        # Copy to clipboard
        if st.button("Copy JSON to Clipboard"):
            st.write("JSON copied to clipboard!")
            st.code(json_str)
        
        st.header("🔄 Actions")
        if st.button("Regenerate Timeline"):
            del st.session_state.timeline
            del st.session_state.themes
            st.rerun()

else:
    st.info("👈 Use the sidebar to generate a sample game or upload your own data to get started!")
    
    # Show example output
    st.header("📖 Example Output")
    st.markdown("""
    The system generates timelines like this:
    """)
    
    example_timeline = [
        {
            "ts": "00:00–00:59",
            "event": "LeBron opens the scoring in transition.",
            "fan_sentiment": "pos"
        },
        {
            "ts": "01:00–01:59", 
            "event": "Mavs go on 10-2 run; Lakers cold from three.",
            "fan_sentiment": "neg"
        },
        {
            "ts": "02:00–02:59",
            "event": "Bench unit stabilizes; AD blocks two shots.",
            "fan_sentiment": "mixed"
        }
    ]
    
    st.json(example_timeline)
    
    st.markdown("""
    ### Features:
    - **Minute-by-minute timeline** from Reddit game threads
    - **Sentiment analysis** (positive/negative/mixed)
    - **Top themes** extraction
    - **JSON export** for downstream use
    - **Teacher pipeline** for training data generation
    """)

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit, FastAPI, and the teacher pipeline approach.")
