"""
Logger Component
---------------
This component handles logging of inputs, prompts, and outputs for each step
of the content creation workflow.
"""

import os
import json
from typing import Dict, Any, Callable, List
from datetime import datetime

def setup_logging(run_id: str):
    """Set up logging directories for a specific run."""
    # Create main logs directory
    os.makedirs("logs", exist_ok=True)
    
    # Create run-specific directory
    run_dir = os.path.join("logs", run_id)
    os.makedirs(run_dir, exist_ok=True)
    
    # Create component-specific directories
    components = [
        "topic_discovery",
        "human_selection",
        "content_generation",
        "content_refinement",
        "image_generation",
        "html_formatter"
    ]
    
    for component in components:
        os.makedirs(os.path.join(run_dir, component), exist_ok=True)
    
    return run_dir

def log_state(state_dict: Dict[str, Any], *, state_type: str, node_name: str = None, **kwargs):
    """Callback function to log state transitions in the workflow."""
    if state_type not in ["start", "input", "output"] or not state_dict:
        return
    
    run_id = state_dict.get("run_id", "unknown")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Skip logging if node_name is None (happens at the very start and end)
    if node_name is None:
        return
    
    # Determine the component directory based on node name
    component_dir = os.path.join("logs", run_id, node_name)
    os.makedirs(component_dir, exist_ok=True)
    
    # Clean up state data for logging (remove large content if needed)
    log_state = {k: v for k, v in state_dict.items()}
    
    # Create appropriate log file based on state type
    if state_type == "input":
        log_file = os.path.join(component_dir, "input.txt")
        with open(log_file, "a") as f:
            f.write(f"===== {timestamp} =====\n")
            f.write(f"Input to {node_name}:\n")
            
            # Handle specific components
            if node_name == "topic_discovery":
                f.write("Starting topic discovery process...\n\n")
            
            elif node_name == "human_selection":
                f.write("Trending topics:\n")
                for i, topic in enumerate(log_state.get("trending_topics", []), 1):
                    f.write(f"{i}. {topic}\n")
                f.write("\n")
            
            elif node_name == "generate_content":
                f.write(f"Selected topic: {log_state.get('selected_topic', '')}\n\n")
            
            elif node_name == "refine_content":
                f.write(f"Refinement iteration: {log_state.get('refinement_count', 0) + 1}\n")
                f.write(f"Current content length: {len(log_state.get('current_content', ''))}\n")
                
                # Write summary of previous feedback if available
                previous_feedback = log_state.get("refinement_feedback", [])
                if previous_feedback:
                    f.write("\nPrevious feedback summary:\n")
                    for i, round_feedback in enumerate(previous_feedback):
                        f.write(f"Round {i+1}:\n")
                        for j, item in enumerate(round_feedback[:5]):
                            f.write(f"- {item}\n")
                        f.write("\n")
                f.write("\n")
            
            elif node_name == "generate_image":
                f.write("Starting image generation for the blog post...\n")
                f.write(f"Content length: {len(log_state.get('current_content', ''))}\n")
                f.write(f"Topic: {log_state.get('selected_topic', '')}\n\n")
            
            elif node_name == "create_html":
                f.write("Starting HTML formatting...\n")
                f.write(f"Content length: {len(log_state.get('current_content', ''))}\n")
                f.write(f"Image path: {log_state.get('image_url', '')}\n\n")
            
            # Add general state info as JSON
            f.write("State summary:\n")
            summary = {
                k: v if not isinstance(v, str) or len(v) < 200 
                else f"<{len(v)} characters>" 
                for k, v in log_state.items()
            }
            f.write(json.dumps(summary, indent=2))
            f.write("\n\n")
    
    elif state_type == "output":
        log_file = os.path.join(component_dir, "output.txt")
        with open(log_file, "a") as f:
            f.write(f"===== {timestamp} =====\n")
            f.write(f"Output from {node_name}:\n")
            
            # Handle specific components
            if node_name == "topic_discovery":
                f.write("Discovered trending topics:\n")
                for i, topic in enumerate(log_state.get("trending_topics", []), 1):
                    f.write(f"{i}. {topic}\n")
                f.write("\n")
            
            elif node_name == "human_selection":
                f.write(f"Selected topic: {log_state.get('selected_topic', '')}\n\n")
            
            elif node_name == "generate_content":
                f.write("Generated initial content:\n")
                f.write("---\n")
                f.write(log_state.get("current_content", "")[:1000] + "...\n")
                f.write("---\n\n")
                
                # Save full content to separate file
                content_file = os.path.join(component_dir, "initial_content.md")
                with open(content_file, "w") as cf:
                    cf.write(log_state.get("current_content", ""))
            
            elif node_name == "refine_content":
                # Get the latest feedback
                all_feedback = log_state.get("refinement_feedback", [])
                iteration = log_state.get("refinement_count", 0)
                
                f.write(f"Refinement iteration {iteration} completed\n")
                
                if all_feedback and len(all_feedback) > 0:
                    latest_feedback = all_feedback[-1]
                    f.write("\nFeedback received:\n")
                    for i, point in enumerate(latest_feedback, 1):
                        f.write(f"{i}. {point}\n")
                
                f.write("\nRefined content summary:\n")
                content_preview = log_state.get("current_content", "")[:500] + "..."
                f.write(content_preview + "\n\n")
                
                # Save full content to separate file
                content_file = os.path.join(component_dir, f"refined_content_{iteration}.md")
                with open(content_file, "w") as cf:
                    cf.write(log_state.get("current_content", ""))
            
            elif node_name == "generate_image":
                f.write(f"Generated image path: {log_state.get('image_url', '')}\n\n")
            
            elif node_name == "create_html":
                f.write("HTML formatting completed\n")
                f.write(f"HTML content length: {len(log_state.get('html_content', ''))}\n\n")
                
                # Save HTML preview
                html_preview = log_state.get("html_content", "")[:500] + "..."
                f.write("HTML preview:\n")
                f.write(html_preview + "\n\n")
            
            # Add general state info as JSON
            f.write("State summary:\n")
            summary = {
                k: v if not isinstance(v, str) or len(v) < 200 
                else f"<{len(v)} characters>" 
                for k, v in log_state.items()
            }
            f.write(json.dumps(summary, indent=2))
            f.write("\n\n")

def format_feedback(feedback_list: List[str]) -> str:
    """Format feedback points in a clean, readable format."""
    if not feedback_list:
        return "No feedback available"
    
    result = ""
    for i, point in enumerate(feedback_list, 1):
        # Clean up the point (remove numbering if present)
        if point.strip().startswith(str(i) + ".") or point.strip().startswith(str(i) + ")"):
            # Point already has numbering, extract the content
            content = point.split(".", 1)[1].strip() if "." in point else point.split(")", 1)[1].strip()
        else:
            content = point.strip()
        
        result += f"{i}. {content}\n"
    
    return result