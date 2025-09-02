#!/usr/bin/env python3
"""
Teacher pipeline for generating timeline snippets with sentiment analysis and event summaries.
"""

import json
import random
import re
from typing import List, Dict, Tuple, Optional
from nltk.sentiment import SentimentIntensityAnalyzer
import numpy as np

# Initialize VADER sentiment analyzer
sia = SentimentIntensityAnalyzer()

def vader_label(text: str) -> str:
    """Label text as positive, negative, or mixed using VADER sentiment analysis.
    
    Args:
        text: Input text to analyze
        
    Returns:
        Sentiment label: "pos", "neg", or "mixed"
    """
    if not text.strip():
        return "mixed"
    
    score = sia.polarity_scores(text)["compound"]
    if score > 0.25:
        return "pos"
    elif score < -0.25:
        return "neg"
    else:
        return "mixed"

def trimmed_mean_sentiment(comments: List[Dict]) -> str:
    """Compute sentiment using trimmed mean to avoid single loud user skew.
    
    Args:
        comments: List of comment dictionaries with 'body' field
        
    Returns:
        Overall sentiment label
    """
    if not comments:
        return "mixed"
    
    # Get sentiment scores for each comment
    sentiments = []
    for comment in comments:
        body = comment.get("body", "")
        if body.strip():
            score = sia.polarity_scores(body)["compound"]
            sentiments.append(score)
    
    if not sentiments:
        return "mixed"
    
    # Sort by absolute value and trim top/bottom 10%
    sentiments = sorted(sentiments, key=abs)
    trim_count = max(1, int(len(sentiments) * 0.1))
    trimmed = sentiments[trim_count:-trim_count] if len(sentiments) > 2 * trim_count else sentiments
    
    # Compute mean and classify
    mean_score = np.mean(trimmed)
    return vader_label("dummy") if len(trimmed) == 0 else vader_label("positive" if mean_score > 0.25 else "negative" if mean_score < -0.25 else "neutral")

def is_run(pbp_events: List[Dict]) -> Optional[Tuple[str, int, str]]:
    """Detect if PBP events represent a scoring run.
    
    Args:
        pbp_events: List of PBP event dictionaries
        
    Returns:
        Tuple of (team, run_length, star_player) or None if no run detected
    """
    if len(pbp_events) < 2:
        return None
    
    # Group events by team and calculate consecutive scoring
    team_scores = {}
    for event in pbp_events:
        team = event.get("team", "")
        points = event.get("points", 0)
        if team and points > 0:
            if team not in team_scores:
                team_scores[team] = []
            team_scores[team].append(points)
    
    # Check for runs (8+ points in sequence)
    for team, scores in team_scores.items():
        if sum(scores) >= 8:
            # Find the player with most points (simplified)
            star_player = "star"  # Placeholder - would need player info in real data
            return team, sum(scores), star_player
    
    return None

def is_lead_change(pbp_events: List[Dict]) -> Optional[Tuple[str, str, str]]:
    """Detect if PBP events represent a lead change.
    
    Args:
        pbp_events: List of PBP event dictionaries
        
    Returns:
        Tuple of (team, player, shot_type) or None if no lead change
    """
    if len(pbp_events) < 1:
        return None
    
    # Simplified lead change detection
    # In real implementation, would track score changes
    for event in pbp_events:
        if event.get("points", 0) > 0:
            team = event.get("team", "")
            desc = event.get("desc", "")
            
            # Extract shot type from description
            shot_type = "shot"
            if "3PT" in desc:
                shot_type = "three-pointer"
            elif "Free Throw" in desc:
                shot_type = "free throw"
            elif "Dunk" in desc:
                shot_type = "dunk"
            elif "Layup" in desc:
                shot_type = "layup"
            
            return team, "player", shot_type
    
    return None

def is_highlight_play(pbp_events: List[Dict]) -> Optional[Tuple[str, str]]:
    """Detect if PBP events contain highlight plays.
    
    Args:
        pbp_events: List of PBP event dictionaries
        
    Returns:
        Tuple of (player, play_type) or None if no highlight
    """
    highlight_keywords = ["block", "dunk", "steal", "alley-oop", "behind-the-back", "no-look"]
    
    for event in pbp_events:
        desc = event.get("desc", "").lower()
        for keyword in highlight_keywords:
            if keyword in desc:
                # Extract player name (simplified)
                player = "player"  # Placeholder
                return player, keyword
    
    return None

def summarize_window(pbp_events: List[Dict], comments: List[Dict]) -> str:
    """Generate event summary for a window using PBP events and fan quotes.
    
    Args:
        pbp_events: List of PBP event dictionaries
        comments: List of comment dictionaries
        
    Returns:
        Event summary string (≤ 28 tokens)
    """
    # Check for runs first
    run_info = is_run(pbp_events)
    if run_info:
        team, run_len, star = run_info
        summary = f"{team} {run_len}-0 run as {star} scores {run_len} straight."
        return summary
    
    # Check for lead changes
    lead_info = is_lead_change(pbp_events)
    if lead_info:
        team, player, shot_type = lead_info
        summary = f"{team} retake the lead on {player} {shot_type}."
        return summary
    
    # Check for highlight plays
    highlight_info = is_highlight_play(pbp_events)
    if highlight_info:
        player, play_type = highlight_info
        summary = f"{player} emphatic {play_type} fires up fans."
        return summary
    
    # Fallback: use last PBP event description
    if pbp_events:
        last_event = pbp_events[-1]
        desc = last_event.get("desc", "")
        if desc:
            # Capitalize and clean up
            summary = desc.capitalize()
            # Truncate if too long
            if len(summary.split()) > 20:
                summary = " ".join(summary.split()[:20]) + "..."
            return summary
    
    # Default fallback
    return "Game action continues."

def add_fan_quotes(summary: str, comments: List[Dict], max_quotes: int = 2) -> str:
    """Add fan quotes to the summary if available.
    
    Args:
        summary: Base event summary
        comments: List of comment dictionaries
        max_quotes: Maximum number of quotes to add
        
    Returns:
        Summary with fan quotes
    """
    if not comments:
        return summary
    
    # Get top comments by score
    scored_comments = [(c.get("score", 0), c.get("body", "")) for c in comments]
    scored_comments.sort(key=lambda x: x[0], reverse=True)
    
    quotes_added = 0
    for score, body in scored_comments:
        if quotes_added >= max_quotes:
            break
        
        if body and len(body) <= 40:  # ≤ 8 tokens roughly
            # Clean up the quote
            clean_quote = re.sub(r'[^\w\s\-\']', '', body)
            if clean_quote and len(clean_quote.split()) <= 8:
                summary += f' "{clean_quote}"'
                quotes_added += 1
    
    return summary

def write_event(pbp_events: List[Dict], comments: List[Dict]) -> str:
    """Write a complete event summary with fan quotes.
    
    Args:
        pbp_events: List of PBP event dictionaries
        comments: List of comment dictionaries
        
    Returns:
        Complete event summary string
    """
    summary = summarize_window(pbp_events, comments)
    summary_with_quotes = add_fan_quotes(summary, comments)
    
    # Ensure we don't exceed token limit
    words = summary_with_quotes.split()
    if len(words) > 28:
        summary_with_quotes = " ".join(words[:28]) + "..."
    
    return summary_with_quotes

def label_window(win: Dict) -> Dict:
    """Label a single window with sentiment and event summary.
    
    Args:
        win: Window dictionary with comments and PBP events
        
    Returns:
        Dictionary with timeline information
    """
    # Extract comments and PBP events
    comments = win.get("comments", [])
    pbp_events = win.get("pbp", [])
    
    # Get sentiment using trimmed mean
    fan_sentiment = trimmed_mean_sentiment(comments)
    
    # Generate event summary
    event = write_event(pbp_events, comments)
    
    # Create timestamp
    period = win.get("period", 1)
    clock_start = win.get("clock_start", "00:00")
    
    if period > 4:
        period_label = f"OT{period - 4}"
    else:
        period_label = f"Q{period}"
    
    timestamp = f"{period_label} {clock_start}"
    
    return {
        "timeline": [{
            "ts": timestamp,
            "event": event,
            "fan_sentiment": fan_sentiment
        }]
    }

def extract_top_themes(all_comments: List[str], min_df: int = 3, max_features: int = 50) -> List[str]:
    """Extract top themes using TF-IDF on n-grams.
    
    Args:
        all_comments: List of all comment texts
        min_df: Minimum document frequency
        max_features: Maximum number of features to return
        
    Returns:
        List of top theme n-grams
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        # Combine all comments
        combined_text = " ".join(all_comments)
        
        # Create TF-IDF vectorizer
        vec = TfidfVectorizer(
            analyzer='word',
            ngram_range=(2, 3),
            min_df=min_df,
            max_features=max_features,
            stop_words='english'
        )
        
        # Fit and transform
        ngrams = vec.fit_transform([combined_text])
        
        # Get feature names and scores
        feature_names = vec.get_feature_names_out()
        scores = ngrams.sum(0).A1
        
        # Sort by score and return top features
        sorted_features = sorted(
            zip(feature_names, scores),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Filter out team names and numbers
        team_names = {"lakers", "mavericks", "celtics", "bucks", "warriors", "grizzlies", "heat", "nuggets"}
        filtered_features = []
        
        for feature, score in sorted_features[:10]:  # Top 10
            # Skip if contains team names or is mostly numbers
            if not any(team in feature.lower() for team in team_names):
                if not re.match(r'^\d+$', feature):
                    filtered_features.append(feature)
        
        return filtered_features[:5]  # Return top 5
        
    except ImportError:
        # Fallback if sklearn not available
        return ["basketball", "game", "play", "shot", "fans"]
