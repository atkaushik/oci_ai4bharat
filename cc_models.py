import re
from typing import List, Tuple
from transformers import pipeline
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image




def getBlipClosedCaptionsForFrame(frame_path):
    
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large")

    
    image = Image.open(frame_path).convert("RGB")

    
    inputs = processor(image, return_tensors="pt")
    caption_ids = model.generate(**inputs)
    caption = processor.batch_decode(caption_ids, skip_special_tokens=True)[0]

    print("Caption:", caption)
    return caption





























