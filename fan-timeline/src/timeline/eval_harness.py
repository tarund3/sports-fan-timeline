from __future__ import annotations
import json, argparse, os
from typing import List, Dict, Tuple
from collections import Counter
import jsonschema
from sklearn.metrics import f1_score, classification_report

def load_schema(schema_path: str) -> Dict:
    """Load JSON schema for validation."""
    with open(schema_path, "r") as f:
        return json.load(f)

def validate_json_schema(data: Dict, schema: Dict) -> Tuple[bool, str]:
    """Validate data against JSON schema."""
    try:
        jsonschema.validate(data, schema)
        return True, "Valid"
    except jsonschema.ValidationError as e:
        return False, str(e)

def calculate_coverage(predicted_events: List[Dict], reference_events: List[Dict], 
                      time_tolerance: int = 90) -> float:
    """Calculate coverage of reference events by predicted events."""
    if not reference_events:
        return 0.0
    
    covered = 0
    for ref_event in reference_events:
        ref_time = ref_event.get("ts", "")
        # Simple time matching (could be improved with proper parsing)
        for pred_event in predicted_events:
            pred_time = pred_event.get("ts", "")
            if ref_time == pred_time or ref_time in pred_time:
                covered += 1
                break
    
    return covered / len(reference_events)

def calculate_sentiment_f1(predicted: List[Dict], reference: List[Dict]) -> float:
    """Calculate macro F1 score for sentiment classification."""
    if not predicted or not reference:
        return 0.0
    
    # Extract sentiment labels
    pred_sentiments = [e.get("fan_sentiment", "mixed") for e in predicted]
    ref_sentiments = [e.get("fan_sentiment", "mixed") for e in reference]
    
    # Ensure same length (pad if necessary)
    max_len = max(len(pred_sentiments), len(ref_sentiments))
    pred_sentiments.extend(["mixed"] * (max_len - len(pred_sentiments)))
    ref_sentiments.extend(["mixed"] * (max_len - len(ref_sentiments)))
    
    # Calculate F1
    try:
        f1 = f1_score(ref_sentiments, pred_sentiments, average='macro')
        return f1
    except:
        return 0.0

def calculate_redundancy(events: List[Dict], similarity_threshold: float = 0.8) -> float:
    """Calculate redundancy rate (simplified version)."""
    if len(events) <= 1:
        return 0.0
    
    # Simple text similarity check
    duplicate_count = 0
    for i in range(len(events)):
        for j in range(i + 1, len(events)):
            event1 = events[i].get("event", "").lower()
            event2 = events[j].get("event", "").lower()
            
            # Simple word overlap similarity
            words1 = set(event1.split())
            words2 = set(event2.split())
            if words1 and words2:
                similarity = len(words1.intersection(words2)) / len(words1.union(words2))
                if similarity > similarity_threshold:
                    duplicate_count += 1
    
    total_pairs = len(events) * (len(events) - 1) / 2
    return duplicate_count / total_pairs if total_pairs > 0 else 0.0

def evaluate_timeline(predicted: Dict, reference: Dict, schema: Dict) -> Dict:
    """Evaluate a single timeline prediction."""
    results = {}
    
    # JSON schema validation
    is_valid, validation_msg = validate_json_schema(predicted, schema)
    results["json_valid"] = is_valid
    results["validation_error"] = validation_msg
    
    if not is_valid:
        return results
    
    # Extract timeline events
    pred_events = predicted.get("timeline", [])
    ref_events = reference.get("timeline", [])
    
    # Coverage
    results["coverage"] = calculate_coverage(pred_events, ref_events)
    
    # Sentiment F1
    results["sentiment_f1"] = calculate_sentiment_f1(pred_events, ref_events)
    
    # Redundancy
    results["redundancy"] = calculate_redundancy(pred_events)
    
    # Length metrics
    results["pred_length"] = len(pred_events)
    results["ref_length"] = len(ref_events)
    
    return results

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--predictions", required=True, help="Path to predicted timelines JSONL")
    ap.add_argument("--references", required=True, help="Path to reference timelines JSONL")
    ap.add_argument("--schema", default="schema/timeline.schema.json", help="Path to JSON schema")
    ap.add_argument("--output", help="Output file for detailed results")
    args = ap.parse_args()
    
    # Load schema
    try:
        schema = load_schema(args.schema)
        print(f"Loaded schema from {args.schema}")
    except Exception as e:
        print(f"Warning: Could not load schema: {e}")
        schema = {}
    
    # Load predictions and references
    predictions = []
    with open(args.predictions, "r") as f:
        for line in f:
            if line.strip():
                predictions.append(json.loads(line))
    
    references = []
    with open(args.references, "r") as f:
        for line in f:
            if line.strip():
                references.append(json.loads(line))
    
    print(f"Loaded {len(predictions)} predictions and {len(references)} references")
    
    # Evaluate each prediction
    all_results = []
    for i, (pred, ref) in enumerate(zip(predictions, references)):
        result = evaluate_timeline(pred, ref, schema)
        result["sample_id"] = i
        all_results.append(result)
    
    # Aggregate results
    if all_results:
        valid_results = [r for r in all_results if r.get("json_valid", False)]
        
        metrics = {
            "total_samples": len(all_results),
            "valid_json_rate": len(valid_results) / len(all_results),
            "avg_coverage": sum(r.get("coverage", 0) for r in valid_results) / len(valid_results) if valid_results else 0,
            "avg_sentiment_f1": sum(r.get("sentiment_f1", 0) for r in valid_results) / len(valid_results) if valid_results else 0,
            "avg_redundancy": sum(r.get("redundancy", 0) for r in valid_results) / len(valid_results) if valid_results else 0,
        }
        
        print("\n=== EVALUATION RESULTS ===")
        print(f"Total samples: {metrics['total_samples']}")
        print(f"JSON validity rate: {metrics['valid_json_rate']:.3f}")
        print(f"Average coverage: {metrics['avg_coverage']:.3f}")
        print(f"Average sentiment F1: {metrics['avg_sentiment_f1']:.3f}")
        print(f"Average redundancy: {metrics['avg_redundancy']:.3f}")
        
        # Check against PRD targets
        print("\n=== PRD TARGETS ===")
        print(f"JSON validity ≥98%: {'✅' if metrics['valid_json_rate'] >= 0.98 else '❌'}")
        print(f"Coverage ≥70%: {'✅' if metrics['avg_coverage'] >= 0.70 else '❌'}")
        print(f"Sentiment F1 ≥0.60: {'✅' if metrics['avg_sentiment_f1'] >= 0.60 else '❌'}")
        print(f"Redundancy ≤10%: {'✅' if metrics['avg_redundancy'] <= 0.10 else '❌'}")
        
        # Save detailed results
        if args.output:
            output_data = {
                "summary": metrics,
                "detailed_results": all_results
            }
            with open(args.output, "w") as f:
                json.dump(output_data, f, indent=2)
            print(f"\nDetailed results saved to: {args.output}")
    
    else:
        print("No results to evaluate")

if __name__ == "__main__":
    main()
