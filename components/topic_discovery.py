"""
Topic Discovery Component
------------------------
This component is responsible for discovering trending AI topics by scraping
relevant websites and using Llama 3.3 70B to identify the most interesting trends.
"""

import requests
from bs4 import BeautifulSoup
import os
import re
from typing import Dict, List, Any
import openai
import json
from datetime import datetime

# Import custom LLM from content_generation
# We'll use a simple function instead to avoid circular imports
def call_llama(prompt):
    """Call Llama 3.3 70B via Lepton API."""
    client = openai.OpenAI(
        base_url="https://llama3-3-70b.lepton.run/api/v1/",
        api_key=os.getenv("LEPTON_API_KEY")
    )
    
    completion = client.chat.completions.create(
        model="llama3.3-70b",
        messages=[
            {"role": "system", "content": "You are a trend analyst specializing in artificial intelligence and technology."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2048
    )
    
    return completion.choices[0].message.content

# Sources for trending AI topics
SOURCES = [
    "https://news.ycombinator.com",
    "https://www.reddit.com/r/artificial/",
    "https://www.reddit.com/r/MachineLearning/",
    "https://venturebeat.com/category/ai/",
    "https://techcrunch.com/category/artificial-intelligence/",
]

def scrape_content(url: str) -> str:
    """Scrape content from a given URL."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract relevant content (this will vary based on the website structure)
        # For demonstration purposes, we'll extract all text
        text_content = soup.get_text()
        
        # Clean up the text (remove extra whitespace, etc.)
        text_content = " ".join(text_content.split())
        
        return text_content[:10000]  # Limit content size
    
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return ""

def extract_trending_topics(contents: List[str]) -> List[str]:
    """Use Llama 3.3 70B to extract trending AI topics from scraped content."""
    
    # Create a prompt for the LLM
    prompt = """
    Based on the following content scraped from tech news sites, identify the top 10 
    trending topics in AI right now. Focus on specific advancements, technologies, 
    research papers, or applications that are gaining significant attention.
    
    For each topic, provide a short, catchy title (5-7 words) that would make a good 
    blog post headline.
    
    Scraped content:
    {}
    
    Return ONLY a list of 10 trending AI topics, one per line, without any additional text.
    DO NOT number your list - just return the topic titles.
    """.format("\n\n".join(contents))
    
    # Call Llama 3.3 70B
    response = call_llama(prompt)
    
    # Parse the response into a list of topics and clean any numbering
    topics = []
    for line in response.strip().split("\n"):
        if not line.strip():
            continue
        
        # Remove numbering patterns (e.g. "1.", "1)", "[1]", etc.)
        cleaned_line = re.sub(r'^\s*\d+[\.\)\]]*\s*', '', line.strip())
        
        # Remove any asterisks, dashes or other list markers
        cleaned_line = re.sub(r'^\s*[\*\-\+]\s*', '', cleaned_line)
        
        topics.append(cleaned_line)
    
    return topics[:10]  # Ensure we have at most 10 topics

def log_discovery(state: Dict[str, Any], topics: List[str]):
    """Log the topic discovery process."""
    run_id = state.get("run_id", datetime.now().strftime("%Y%m%d_%H%M%S"))
    component_dir = os.path.join("logs", run_id, "topic_discovery")
    os.makedirs(component_dir, exist_ok=True)
    
    # Log the discovered topics
    log_file = os.path.join(component_dir, "output.txt")
    with open(log_file, "w") as f:
        f.write(f"===== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =====\n")
        f.write("Discovered trending topics:\n")
        for i, topic in enumerate(topics, 1):
            f.write(f"{i}. {topic}\n")
        f.write("\n")
        
        # Add state summary
        f.write("State summary:\n")
        summary = {
            "trending_topics": topics,
            "run_id": run_id
        }
        f.write(json.dumps(summary, indent=2))
        f.write("\n\n")

def get_trending_topics(state: Dict[str, Any]) -> Dict[str, Any]:
    """Get trending AI topics and update the agent state."""
    print("Discovering trending AI topics...")
    
    # Scrape content from sources
    contents = []
    for source in SOURCES:
        print(f"Scraping {source}...")
        content = scrape_content(source)
        if content:
            contents.append(content)
    
    # If we couldn't scrape any content, use a fallback list of topics
    if not contents:
        print("Using fallback trending topics...")
        trending_topics = [
            "GPT-5 Rumors and Expected Capabilities",
            "Open-Source LLMs Challenging Commercial Models",
            "AI Coding Assistants Revolution",
            "Multimodal AI Systems Breaking Barriers",
            "AI Ethics and Regulation Developments",
            "Edge AI and On-Device Intelligence",
            "AI in Healthcare Diagnostic Breakthroughs",
            "Generative AI for Creative Industries",
            "AI Agents and Autonomous Systems",
            "Foundation Models in Scientific Discovery"
        ]
    else:
        # Extract trending topics using LLM
        trending_topics = extract_trending_topics(contents)
    
    # Log the discovery process
    log_discovery(state, trending_topics)
    
    # Update the state with trending topics
    return {**state, "trending_topics": trending_topics}