"""
Generate a visual representation of the workflow graph using Mermaid
"""

import os
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from main import AgentState, build_workflow_graph
from langchain_core.runnables.graph import MermaidDrawMethod
import base64

# Define a function to save the graph visualization
def generate_workflow_graph():
    """Generate and save a visualization of the workflow graph"""
    
    # Build the workflow graph
    graph = build_workflow_graph()
    
    # Get the compiled graph
    runnable = graph.compile()
    
    # Generate the Mermaid PNG
    try:
        png_data = runnable.get_graph().draw_mermaid_png(
            draw_method=MermaidDrawMethod.API,
        )
        
        # Create docs directory if it doesn't exist
        os.makedirs("docs", exist_ok=True)
        
        # Save the PNG to a file
        with open('docs/workflow_graph.png', 'wb') as f:
            f.write(png_data)
        
        print("Workflow graph visualization saved to docs/workflow_graph.png")
        
        # Generate Mermaid markdown for reference
        mermaid_code = runnable.get_graph().draw_mermaid()
        with open('docs/workflow_graph.md', 'w') as f:
            f.write("```mermaid\n")
            f.write(mermaid_code)
            f.write("\n```")
        
        print("Mermaid code saved to docs/workflow_graph.md")
        
    except Exception as e:
        print(f"Error generating graph visualization: {e}")
        
        # Fallback to simple text representation
        workflow_text = """
        Workflow Graph:
        
        [discover_topics] --> [human_selection] --> [generate_content] --> [refine_content]
                                                                           |
                                                                           | (count < 4)
                                                                           v
                                                                      [refine_content]
                                                                           |
                                                                           | (count >= 4)
                                                                           v
                                                                      [generate_image] --> [create_html] --> [END]
        """
        
        # Save the text visualization
        with open('docs/workflow_graph.txt', 'w') as f:
            f.write(workflow_text)
        
        print("Simple workflow graph saved to docs/workflow_graph.txt")
        print(workflow_text)

if __name__ == "__main__":
    generate_workflow_graph()