"""
HTML Formatter Component
----------------------
This component formats the final content into an HTML page.
"""

import os
import markdown
from typing import Dict, Any
import re
from datetime import datetime
import json

def log_html_creation(state: Dict[str, Any], title: str, html_content: str, output_path: str = None):
    """Log the HTML creation process."""
    run_id = state.get("run_id", datetime.now().strftime("%Y%m%d_%H%M%S"))
    component_dir = os.path.join("logs", run_id, "html_formatter")
    os.makedirs(component_dir, exist_ok=True)
    
    # Log the HTML creation
    log_file = os.path.join(component_dir, "output.txt")
    with open(log_file, "w") as f:
        f.write(f"===== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =====\n")
        f.write(f"Generated HTML for: {title}\n\n")
        
        # Log the image path used
        f.write(f"Image path: {state.get('image_url', '')}\n")
        
        if output_path:
            f.write(f"Output path: {output_path}\n")
        
        # Add a preview of the HTML
        f.write("\nHTML preview:\n")
        f.write("---\n")
        html_preview = html_content[:500] + "..." if len(html_content) > 500 else html_content
        f.write(html_preview)
        f.write("\n---\n\n")
        
        # Add state summary
        f.write("State summary:\n")
        summary = {
            "title": title,
            "html_length": len(html_content),
            "image_path": state.get("image_url", ""),
            "run_id": run_id
        }
        f.write(json.dumps(summary, indent=2))
        f.write("\n\n")
    
    # Save a copy of the HTML file
    html_file = os.path.join(component_dir, "output.html")
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)

def create_html_page(state: Dict[str, Any]) -> Dict[str, Any]:
    """Format the content into an HTML page and update the agent state."""
    content = state["current_content"]
    image_path = state["image_url"]
    
    print("Creating HTML page...")
    
    # Extract title from the content (assuming it's the first line)
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if title_match:
        title = title_match.group(1)
    else:
        title = state["selected_topic"]
    
    # Convert Markdown to HTML
    html_body = markdown.markdown(content, extensions=['extra', 'toc'])
    
    # Determine relative path for image
    if os.path.exists(image_path):
        # If the image path is relative to the current directory,
        # adjust it to be relative to the output HTML file
        rel_image_path = os.path.relpath(image_path, "output")
    else:
        # If the image doesn't exist (placeholder), use a placeholder URL
        rel_image_path = "https://placehold.co/600x400?text=AI+Blog+Image"
    
    # Get current date
    current_date = datetime.now().strftime("%B %d, %Y")
    
    # Create HTML template
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        :root {{
            --primary-color: #3498db;
            --secondary-color: #2c3e50;
            --text-color: #333;
            --background-color: #f5f5f5;
            --content-background: #ffffff;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background-color: var(--background-color);
            margin: 0;
            padding: 0;
        }}
        
        .container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: var(--content-background);
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }}
        
        header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 20px 0;
            border-bottom: 1px solid #eee;
        }}
        
        h1 {{
            color: var(--secondary-color);
            margin-bottom: 10px;
            font-size: 2.2em;
        }}
        
        .date {{
            color: #666;
            font-style: italic;
            margin-bottom: 20px;
        }}
        
        .featured-image {{
            width: 100%;
            height: auto;
            max-height: 400px;
            object-fit: cover;
            margin-bottom: 30px;
            border-radius: 5px;
        }}
        
        h2 {{
            color: var(--primary-color);
            margin-top: 30px;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
            font-size: 1.8em;
        }}
        
        h3 {{
            color: var(--secondary-color);
            margin-top: 25px;
            font-size: 1.4em;
        }}
        
        p {{
            margin-bottom: 20px;
        }}
        
        blockquote {{
            border-left: 4px solid var(--primary-color);
            padding-left: 15px;
            margin-left: 0;
            color: #555;
        }}
        
        code {{
            background-color: #f0f0f0;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: 'Courier New', Courier, monospace;
        }}
        
        pre {{
            background-color: #f0f0f0;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        
        footer {{
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #777;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <div class="date">Published on {current_date}</div>
        </header>
        
        <img src="{rel_image_path}" alt="Featured Image for {title}" class="featured-image">
        
        <article>
            {html_body}
        </article>
        
        <footer>
            <p>Generated by AI Content Creation Agent</p>
        </footer>
    </div>
</body>
</html>
"""
    
    # Log the HTML creation
    log_html_creation(state, title, html_template)
    
    # Update the state with the HTML content
    return {**state, "html_content": html_template}