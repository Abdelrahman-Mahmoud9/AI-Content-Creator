"""
Image Generation Component
-----------------------
This component generates an appropriate image for the blog post using Lepton's SDXL API.
"""

import os
import uuid
from typing import Dict, Any
import openai
from leptonai.client import Client
import json
from datetime import datetime
import shutil

def log_image_generation(state: Dict[str, Any], image_prompt: str, image_path: str):
    """Log the image generation process."""
    run_id = state.get("run_id", datetime.now().strftime("%Y%m%d_%H%M%S"))
    component_dir = os.path.join("logs", run_id, "image_generation")
    os.makedirs(component_dir, exist_ok=True)
    
    # Log the image prompt and path
    log_file = os.path.join(component_dir, "output.txt")
    with open(log_file, "w") as f:
        f.write(f"===== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =====\n")
        f.write(f"Topic: {state.get('selected_topic', '')}\n\n")
        
        # Log the prompt
        f.write("Image generation prompt:\n")
        f.write(f"\"{image_prompt}\"\n\n")
        
        # Log the image path
        f.write(f"Generated image saved to: {image_path}\n\n")
        
        # Add state summary
        f.write("State summary:\n")
        summary = {
            "selected_topic": state.get("selected_topic", ""),
            "image_path": image_path,
            "prompt_length": len(image_prompt),
            "run_id": run_id
        }
        f.write(json.dumps(summary, indent=2))
        f.write("\n\n")
    
    # Save the prompt to a separate file
    prompt_file = os.path.join(component_dir, "image_prompt.txt")
    with open(prompt_file, "w") as f:
        f.write(image_prompt)
    
    # If image exists, copy it to the logs directory
    if os.path.exists(image_path):
        try:
            image_filename = os.path.basename(image_path)
            log_image_path = os.path.join(component_dir, image_filename)
            shutil.copy2(image_path, log_image_path)
        except Exception as e:
            print(f"Could not copy image to logs: {e}")

def generate_image_prompt(content: str, topic: str) -> str:
    """Generate a prompt for image generation based on the content."""
    client = openai.OpenAI(
        base_url="https://llama3-3-70b.lepton.run/api/v1/",
        api_key=os.getenv("LEPTON_API_KEY")
    )
    
    system_message = """
    You are an expert in creating prompts for AI image generation systems like Stable Diffusion.
    
    Based on the blog post I'll share, create a detailed prompt that will generate an engaging 
    and relevant featured image for the post.
    
    The prompt should:
    - Be detailed and specific
    - Include visual elements related to the topic
    - Specify a style that matches the tone of the article
    - Be optimized for AI image generation
    
    Return ONLY the image generation prompt, without any additional text or explanations.
    The prompt should be 1-3 sentences.
    """
    
    user_message = f"""
    Blog post topic: {topic}
    
    Blog post content (excerpt):
    ```
    {content[:2000]}  
    ```
    
    Create an image generation prompt for this article.
    """
    
    try:
        response = client.chat.completions.create(
            model="llama3.3-70b",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            max_tokens=200,
            temperature=0.7
        )
        
        # Clean up the prompt
        image_prompt = response.choices[0].message.content.strip().strip('"').strip()
        
    except Exception as e:
        print(f"Error generating image prompt: {e}")
        # Fallback prompt
        image_prompt = f"Highly detailed digital illustration of {topic}, futuristic, technology concept, blue background, high quality"
    
    # Add some style keywords if needed
    if "digital art" not in image_prompt.lower() and "illustration" not in image_prompt.lower():
        image_prompt += ", digital art, high quality, detailed illustration"
    
    return image_prompt

def generate_image_lepton_sdxl(prompt: str) -> str:
    """Generate an image using Lepton's SDXL API and return the path to the saved image."""
    try:
        # Initialize Lepton client
        api_token = os.getenv("LEPTON_API_KEY")
        client = Client("https://sdxl.lepton.run", token=api_token)
        
        # Generate image with SDXL
        image_data = client.run(
            prompt=prompt,
            height=1024,
            width=1024,
            guidance_scale=7.5,  # Increased for better prompt adherence
            high_noise_frac=0.8,
            seed=uuid.uuid4().int % (2**32),  # Random seed
            steps=30,
            use_refiner=True  # Enable refiner for better quality
        )
        
        # Create output directory if it doesn't exist
        os.makedirs("output/images", exist_ok=True)
        
        # Save the image
        image_path = f"output/images/blog_image_{hash(prompt) % 10000}.png"
        with open(image_path, 'wb') as f:
            f.write(image_data)
        
        print(f"Image saved to {image_path}")
        return image_path
        
    except Exception as e:
        print(f"Error generating image with Lepton SDXL: {e}")
        return ""

def generate_image(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate an image for the blog post and update the agent state."""
    content = state["current_content"]
    topic = state["selected_topic"]
    
    print("Generating image for the blog post...")
    
    # Generate a prompt for the image
    image_prompt = generate_image_prompt(content, topic)
    print(f"Image generation prompt: {image_prompt}")
    
    # Generate image with Lepton SDXL
    image_path = generate_image_lepton_sdxl(image_prompt)
    
    if not image_path:
        print("Failed to generate image. Using placeholder.")
        # Return placeholder image path
        image_path = "placeholder.png"
    
    # Log the image generation
    log_image_generation(state, image_prompt, image_path)
    
    # Update the state with the image path
    return {**state, "image_url": image_path}