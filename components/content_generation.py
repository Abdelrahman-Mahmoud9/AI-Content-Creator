"""
Content Generation Component
--------------------------
This component generates the initial content for the selected topic using direct API calls.
"""

import os
from typing import Dict, Any
import openai
import json
from datetime import datetime

def log_content_generation(state: Dict[str, Any], content: str):
    """Log the content generation process."""
    run_id = state.get("run_id", datetime.now().strftime("%Y%m%d_%H%M%S"))
    component_dir = os.path.join("logs", run_id, "content_generation")
    os.makedirs(component_dir, exist_ok=True)
    
    # Log the generated content summary
    log_file = os.path.join(component_dir, "output.txt")
    with open(log_file, "w") as f:
        f.write(f"===== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =====\n")
        f.write(f"Generated content for topic: {state.get('selected_topic', '')}\n\n")
        
        # Add a preview of the content
        f.write("Content preview:\n")
        f.write("---\n")
        preview = content[:1000] + "..." if len(content) > 1000 else content
        f.write(preview)
        f.write("\n---\n\n")
        
        # Add state summary
        f.write("State summary:\n")
        summary = {
            "selected_topic": state.get("selected_topic", ""),
            "content_length": len(content),
            "run_id": run_id
        }
        f.write(json.dumps(summary, indent=2))
        f.write("\n\n")
    
    # Save the full content to a separate file
    content_file = os.path.join(component_dir, "initial_content.md")
    with open(content_file, "w") as f:
        f.write(content)

def generate_initial_content(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate initial content for the selected topic and update the agent state."""
    selected_topic = state["selected_topic"]
    print(f"Generating initial content for topic: {selected_topic}")
    
    # Set up the OpenAI client with Lepton's API
    client = openai.OpenAI(
        base_url="https://llama3-3-70b.lepton.run/api/v1/",
        api_key=os.getenv("LEPTON_API_KEY")
    )
    
    # System message to guide the content generation
    system_message = """
    You are an expert tech blogger specializing in artificial intelligence.
    Write a comprehensive, engaging, and informative blog post about the following trending AI topic.
    
    Your blog post should:
    - Have a catchy title
    - Include an introduction that explains why this topic is important
    - Have clear sections with descriptive headings
    - Provide technical details while remaining accessible to a general audience
    - Include real-world applications or examples
    - Discuss potential future implications
    - End with a conclusion that summarizes key points
    
    The blog post should be approximately 1000-1500 words and written in a professional yet conversational tone.
    Do not include any placeholder text or notes about the structure - write the complete post ready for publication.
    
    Format the post in Markdown with proper headings, paragraphs, and emphasis where appropriate.
    """
    
    # Generate content using direct API call
    try:
        response = client.chat.completions.create(
            model="llama3.3-70b",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Write a blog post about the trending AI topic: {selected_topic}"}
            ],
            max_tokens=4000,
            temperature=0.7
        )
        
        # Extract content from response
        content = response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"Error generating content: {e}")
        # Fallback content
        content = f"""
# {selected_topic}: An Overview

## Introduction
This is a placeholder introduction for the topic '{selected_topic}'. 
The complete content generation encountered an error.

## Key Points
- Point 1
- Point 2
- Point 3

## Conclusion
This is a placeholder conclusion.
"""
    
    # Log the generated content
    log_content_generation(state, content)
    
    # Update the state with the generated content
    return {
        **state, 
        "current_content": content,
        "refinement_count": 0,
        "refinement_feedback": []
    }