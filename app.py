from transformers import AutoProcessor, AutoModelForCausalLM  
from PIL import Image
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import os
import json

# Initialize the FastAPI app
app = FastAPI()

# Define the model and processor
model_id = 'microsoft/Florence-2-large-ft'
model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True).eval().to("cuda")
processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)

def extract_text(image_path, task_prompt='<OCR_WITH_REGION>', text_input=None):
    try:
        image = Image.open(image_path).convert('RGB')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error opening image: {e}")
    
    prompt = task_prompt if text_input is None else task_prompt + text_input
    inputs = processor(text=prompt, images=image, return_tensors="pt")
    generated_ids = model.generate(
        input_ids=inputs["input_ids"].to("cuda"),
        pixel_values=inputs["pixel_values"].to("cuda"),
        max_new_tokens=1024,
        early_stopping=False,
        do_sample=False,
        num_beams=3,
    )
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
    parsed_answer = processor.post_process_generation(
        generated_text, 
        task=task_prompt, 
        image_size=(image.width, image.height)
    )
    return parsed_answer

@app.post("/predict")
async def predict(request: dict):
    try:
        result = extract_text(request['image_paths'])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
