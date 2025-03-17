"""
Content Refinement Component
--------------------------
This component implements the self-critique and refinement mechanism using direct API calls.
"""

import os
from typing import Dict, Any, List
import openai
import re
import json
from datetime import datetime

def log_refinement(state: Dict[str, Any], feedback: List[str], refined_content: str):
    """Log the refinement process."""
    run_id = state.get("run_id", datetime.now().strftime("%Y%m%d_%H%M%S"))
    refinement_count = state.get("refinement_count", 0)
    component_dir = os.path.join("logs", run_id, "content_refinement")
    os.makedirs(component_dir, exist_ok=True)
    
    # Create iteration-specific log directory
    iteration_dir = os.path.join(component_dir, f"iteration_{refinement_count}")
    os.makedirs(iteration_dir, exist_ok=True)
    
    # Log the feedback and refinement
    log_file = os.path.join(iteration_dir, "output.txt")
    with open(log_file, "w") as f:
        f.write(f"===== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =====\n")
        f.write(f"Refinement iteration: {refinement_count}\n\n")
        
        # Log the feedback
        f.write("Feedback received:\n")
        for i, point in enumerate(feedback, 1):
            f.write(f"{i}. {point}\n")
        f.write("\n")
        
        # Add a preview of the refined content
        f.write("Refined content preview:\n")
        f.write("---\n")
        preview = refined_content[:1000] + "..." if len(refined_content) > 1000 else refined_content
        f.write(preview)
        f.write("\n---\n\n")
        
        # Add state summary
        f.write("State summary:\n")
        summary = {
            "refinement_count": refinement_count,
            "feedback_points": len(feedback),
            "content_length": len(refined_content),
            "run_id": run_id
        }
        f.write(json.dumps(summary, indent=2))
        f.write("\n\n")
    
    # Save the full content to a separate file
    content_file = os.path.join(iteration_dir, "refined_content.md")
    with open(content_file, "w") as f:
        f.write(refined_content)
    
    # Save the feedback to a separate file
    feedback_file = os.path.join(iteration_dir, "feedback.json")
    with open(feedback_file, "w") as f:
        json.dump(feedback, f, indent=2)

def critique_content(content: str, topic: str) -> List[str]:
    """Use LLM to critique the content and provide feedback."""
    client = openai.OpenAI(
        base_url="https://llama3-3-70b.lepton.run/api/v1/",
        api_key=os.getenv("LEPTON_API_KEY")
    )
    
    system_message = """
    You are an expert editor specializing in AI and technology content.
    
    Analyze the following blog post and provide constructive criticism.
    
    Focus on these aspects:
    1. Clarity and coherence
    2. Technical accuracy and depth
    3. Engagement and reader interest
    4. Structure and flow
    5. Language and style
    
    For each aspect, provide specific feedback with examples from the text.
    Highlight both strengths and areas for improvement.
    
    Return a list of 3-5 specific improvement points, ordered by priority.
    Each point should clearly identify an issue and suggest how to address it.
    Be specific and actionable in your feedback.
    
    IMPORTANT: Format your response as a clean numbered list, with one improvement point per line, like this:
    1. First improvement point
    2. Second improvement point
    3. Third improvement point
    """
    
    user_message = f"""
    Review this blog post about "{topic}":
    
    ```
    {content}
    ```
    
    Provide 3-5 specific improvement points, ordered by priority.
    """
    
    try:
        # Get critique from LLM
        response = client.chat.completions.create(
            model="llama3.3-70b",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            max_tokens=2000,
            temperature=0.2
        )
        
        critique = response.choices[0].message.content.strip()
        
        # Process the critique to extract clean feedback points
        feedback = process_feedback(critique)
        
    except Exception as e:
        print(f"Error generating critique: {e}")
        feedback = ["Improve the technical depth of the content.", 
                   "Add more specific examples to illustrate key points.",
                   "Enhance the conclusion with more forward-looking insights."]
    
    # Ensure we have at least some feedback points
    if not feedback:
        feedback = ["Improve the technical depth of the content.", 
                   "Add more specific examples to illustrate key points.",
                   "Enhance the conclusion with more forward-looking insights."]
    
    # Print feedback in a clean format
    print("Feedback received:")
    for i, point in enumerate(feedback[:5], 1):
        point_preview = point[:100] + "..." if len(point) > 100 else point
        print(f"{i}. {point_preview}")
    
    return feedback[:5]  # Return at most 5 feedback points

def process_feedback(critique: str) -> List[str]:
    """Process the critique text to extract clean feedback points."""
    # First, split by newlines
    lines = [line.strip() for line in critique.splitlines() if line.strip()]
    
    # Filter out headings and other non-feedback lines
    feedback_lines = []
    
    for line in lines:
        # Skip lines that don't look like feedback points
        if line.startswith("#") or len(line) < 10:
            continue
        
        # Check if the line starts with a number (likely a feedback point)
        if re.match(r'^\d+[\.\)]', line):
            # Split by the first period or parenthesis
            parts = re.split(r'[\.\)]', line, 1)
            if len(parts) > 1:
                feedback_lines.append(parts[1].strip())
            else:
                feedback_lines.append(line)
        # Some points may not have numbers
        elif ":" in line and len(line) > 20:
            feedback_lines.append(line)
    
    # If we couldn't extract structured feedback, return the original lines
    if not feedback_lines and lines:
        feedback_lines = [line for line in lines if len(line) > 10]
    
    return feedback_lines

def refine_content(state: Dict[str, Any]) -> Dict[str, Any]:
    """Refine content based on critique and update the agent state."""
    current_content = state["current_content"]
    topic = state["selected_topic"]
    refinement_count = state["refinement_count"]
    previous_feedback = state["refinement_feedback"]
    
    print(f"Starting refinement iteration {refinement_count + 1}...")
    
    # Get critique of the current content
    feedback = critique_content(current_content, topic)
    
    # Set up the OpenAI client with Lepton's API
    client = openai.OpenAI(
        base_url="https://llama3-3-70b.lepton.run/api/v1/",
        api_key=os.getenv("LEPTON_API_KEY")
    )
    
    system_message = """
    You are an expert AI content writer. Your task is to improve a blog post based on editorial feedback.
    
    Please rewrite the blog post, addressing all the feedback points while maintaining the original structure and key information.
    Make the improvements seamlessly integrated into the text.
    
    Return the complete improved version of the blog post in Markdown format.
    """
    
    # Format the feedback for inclusion in the prompt
    formatted_feedback = "\n".join([f"- {point}" for point in feedback])
    
    # Format previous feedback history
    formatted_previous = ""
    if previous_feedback:
        formatted_previous = "Previous rounds of feedback:\n"
        for i, round_feedback in enumerate(previous_feedback):
            formatted_previous += f"Round {i+1}:\n"
            for item in round_feedback[:3]:  # Limit to first 3 items per round
                shortened = item[:100] + "..." if len(item) > 100 else item
                formatted_previous += f"- {shortened}\n"
    
    user_message = f"""
    Original blog post about "{topic}":
    ```
    {current_content}
    ```
    
    Editorial feedback:
    {formatted_feedback}
    
    {formatted_previous}
    
    Please improve the blog post based on this feedback. Provide the complete revised version.
    """
    
    try:
        # Get refined content from LLM
        response = client.chat.completions.create(
            model="llama3.3-70b",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            max_tokens=4000,
            temperature=0.4
        )
        
        refined_content = response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"Error refining content: {e}")
        # If there's an error, keep the original content
        refined_content = current_content
    
    # Log the refinement process
    log_refinement(state, feedback, refined_content)
    
    # Update the state with the refined content and increment refinement count
    updated_feedback = previous_feedback + [feedback]
    
    return {
        **state,
        "current_content": refined_content,
        "refinement_count": refinement_count + 1,
        "refinement_feedback": updated_feedback
    }