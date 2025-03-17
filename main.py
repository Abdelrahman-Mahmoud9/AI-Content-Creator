"""
AI Content Creation Agent - Main Application
-------------------------------------------
This script orchestrates the entire workflow for the AI content creation agent,
including topic discovery, content generation, refinement, image generation,
and HTML page creation using LangGraph.
"""

import os
from dotenv import load_dotenv
import argparse
from datetime import datetime
import json
import shutil

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence, List, Dict, Any

# Import our custom components
from components.topic_discovery import get_trending_topics
from components.human_selection import get_human_selection
from components.content_generation import generate_initial_content
from components.content_refinement import refine_content
from components.image_generation import generate_image
from components.html_formatter import create_html_page, log_html_creation

load_dotenv()

# Define the state for our agent
class AgentState(TypedDict):
    trending_topics: List[str]
    selected_topic: str
    current_content: str
    refinement_count: int
    refinement_feedback: List[List[str]]
    image_url: str
    html_content: str
    run_id: str
    
def initialize_state() -> AgentState:
    """Initialize the agent state with default values."""
    # Generate a unique run ID
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    return {
        "trending_topics": [],
        "selected_topic": "",
        "current_content": "",
        "refinement_count": 0,
        "refinement_feedback": [],
        "image_url": "",
        "html_content": "",
        "run_id": run_id
    }

# Define the workflow graph
def build_workflow_graph() -> StateGraph:
    """Build the langgraph workflow for the content creation agent."""
    
    # Create a new graph
    graph = StateGraph(AgentState)
    
    # Add nodes to the graph
    graph.add_node("discover_topics", get_trending_topics)
    graph.add_node("human_selection", get_human_selection)
    graph.add_node("generate_content", generate_initial_content)
    graph.add_node("refine_content", refine_content)
    graph.add_node("generate_image", generate_image)
    graph.add_node("create_html", create_html_page)
    
    # Define the edges (workflow)
    graph.add_edge("discover_topics", "human_selection")
    graph.add_edge("human_selection", "generate_content")
    graph.add_edge("generate_content", "refine_content")
    
    # Conditional edge: Either continue refinement or move to image generation
    def should_continue_refinement(state: AgentState) -> str:
        if state["refinement_count"] < 4:  # Maximum 4 iterations
            return "refine_content"
        else:
            return "generate_image"
    
    graph.add_conditional_edges(
        "refine_content",
        should_continue_refinement,
        {
            "refine_content": "refine_content",
            "generate_image": "generate_image"
        }
    )
    
    graph.add_edge("generate_image", "create_html")
    graph.add_edge("create_html", END)
    
    # Set the entry point
    graph.set_entry_point("discover_topics")
    
    return graph

def log_final_output(state: Dict[str, Any], output_path: str):
    """Log the final output details."""
    run_id = state.get("run_id", "unknown")
    logs_dir = os.path.join("logs", run_id)
    
    # Create a summary file with all the important information
    summary_file = os.path.join(logs_dir, "run_summary.json")
    summary = {
        "run_id": run_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "selected_topic": state.get("selected_topic", ""),
        "refinement_iterations": state.get("refinement_count", 0),
        "final_output_path": output_path,
        "image_path": state.get("image_url", ""),
        "content_length": len(state.get("current_content", "")),
        "html_length": len(state.get("html_content", "")),
    }
    
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    
    # Copy the final HTML output to the logs directory
    if os.path.exists(output_path):
        try:
            html_filename = os.path.basename(output_path)
            log_html_path = os.path.join(logs_dir, html_filename)
            shutil.copy2(output_path, log_html_path)
        except Exception as e:
            print(f"Could not copy final HTML to logs: {e}")

def main():
    """Main function to run the agent workflow."""
    parser = argparse.ArgumentParser(description="AI Content Creation Agent")
    parser.add_argument("--output", type=str, default="output", help="Output directory for HTML files")
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(args.output, exist_ok=True)
    
    # Initialize the state and workflow
    initial_state = initialize_state()
    
    # Create logs directory for this run
    run_id = initial_state["run_id"]
    logs_dir = os.path.join("logs", run_id)
    os.makedirs(logs_dir, exist_ok=True)
    
    workflow = build_workflow_graph().compile()
    
    # Run the workflow
    print("Starting AI Content Creation Agent workflow...")
    
    try:
        # Get the final state from the workflow
        final_state = workflow.invoke(initial_state)
        
        # Save the HTML content
        if final_state.get("html_content") and final_state.get("selected_topic"):
            # Clean the filename
            output_file = final_state["selected_topic"].replace(' ', '_').lower()
            output_file = ''.join(c for c in output_file if c.isalnum() or c in '._- ')
            output_path = os.path.join(args.output, f"{output_file}.html")
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(final_state["html_content"])
            print(f"HTML content created and saved to {output_path}")
            
            # Update HTML logger with final output path
            log_html_creation(final_state, final_state.get("selected_topic", ""), 
                            final_state.get("html_content", ""), output_path)
                            
            # Log final output details
            log_final_output(final_state, output_path)
            
            print("Workflow completed successfully!")
        else:
            print("Workflow completed but no HTML content was generated.")
            
    except Exception as e:
        print(f"Error during workflow execution: {e}")
        import traceback
        traceback.print_exc()
        
        # Log the error
        with open(f"logs/{run_id}/error.txt", "w") as f:
            f.write(f"Error during workflow execution: {e}\n")
            traceback.print_exc(file=f)

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()
    main()