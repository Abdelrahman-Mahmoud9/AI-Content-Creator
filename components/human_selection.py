"""
Human Selection Component
-----------------------
This component implements the human-in-the-loop mechanism for topic selection.
"""

from typing import Dict, List, Any
import os
import json
from datetime import datetime

def log_selection(state: Dict[str, Any], selected_topic: str):
    """Log the topic selection."""
    run_id = state.get("run_id", datetime.now().strftime("%Y%m%d_%H%M%S"))
    component_dir = os.path.join("logs", run_id, "human_selection")
    os.makedirs(component_dir, exist_ok=True)
    
    # Log the selected topic
    log_file = os.path.join(component_dir, "output.txt")
    with open(log_file, "w") as f:
        f.write(f"===== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =====\n")
        f.write("Input topics:\n")
        for i, topic in enumerate(state.get("trending_topics", []), 1):
            f.write(f"{i}. {topic}\n")
        f.write("\n")
        f.write(f"Selected topic: {selected_topic}\n\n")
        
        # Add state summary
        f.write("State summary:\n")
        summary = {
            "trending_topics": state.get("trending_topics", []),
            "selected_topic": selected_topic,
            "run_id": run_id
        }
        f.write(json.dumps(summary, indent=2))
        f.write("\n\n")

def get_human_selection(state: Dict[str, Any]) -> Dict[str, Any]:
    """Get human selection of a topic and update the agent state."""
    trending_topics = state["trending_topics"]
    
    if not trending_topics:
        # If no topics were found, use a default topic
        selected_topic = "Recent Advances in Large Language Models"
        print(f"No trending topics found. Using default topic: {selected_topic}")
        
        # Log the selection
        log_selection(state, selected_topic)
        
        return {**state, "selected_topic": selected_topic}
    
    # Display the trending topics to the user
    print("\nTrending AI Topics:")
    for i, topic in enumerate(trending_topics, 1):
        print(f"{i}. {topic}")
    
    # Get user selection
    while True:
        try:
            selection = input("\nSelect a topic number (1-{}): ".format(len(trending_topics)))
            
            # Handle empty input (default to first topic)
            if not selection.strip():
                selected_index = 0
                break
                
            selected_index = int(selection) - 1
            
            if 0 <= selected_index < len(trending_topics):
                break
            else:
                print(f"Please enter a number between 1 and {len(trending_topics)}")
                
        except ValueError:
            print("Please enter a valid number")
    
    selected_topic = trending_topics[selected_index]
    print(f"\nSelected topic: {selected_topic}")
    
    # Log the selection
    log_selection(state, selected_topic)
    
    # Update the state with the selected topic
    return {**state, "selected_topic": selected_topic}