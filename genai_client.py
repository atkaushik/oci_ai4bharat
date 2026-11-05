import oci
import time
import os
import base64
import json
import random

from utils import getGenAIClient
from constants import LANGUAGE_CODE_TO_LANGUAGE
from load_env_data import load_env

load_env()

MAX_RETRIES = 3

def translate_using_genai(texts, source_language, target_language, input_path, endpoint):
    source_language_full = "-1" if source_language not in LANGUAGE_CODE_TO_LANGUAGE else LANGUAGE_CODE_TO_LANGUAGE[source_language]
    target_language_full = "-1" if target_language not in LANGUAGE_CODE_TO_LANGUAGE else LANGUAGE_CODE_TO_LANGUAGE[target_language]
    
    translated_results = []
    overall_time = time.time()
    for text in texts:
        output_text = hit_genai_endpoint(text, source_language_full, target_language_full, endpoint)
        translated_results.append(output_text)

    print(f"Total time taken for the entire text {input_path} is {time.time() - overall_time}")
    return translated_results

def hit_genai_endpoint(message, source_language, target_language, endpoint):
    load_env()
    generative_ai_client = getGenAIClient(endpoint)
    print(f"Input: {message}")
    compartment_id = os.getenv('compartment_id')
    

    text_content = oci.generative_ai_inference.models.TextContent()
    
    
    text_content.text = f"""
        You are a language translator
        Translate the following {source_language} text into{target_language}.
        If a direct translation is not possible for a word:
        First, use a loanword if one exists.
        If not, then transliterate the word to preserve its pronunciation using {target_language} script.
        If transliteration is not possible, then use phonetic transcription.
        Ensure the overall sentence remains natural in the target language.
        There should not be any text in {source_language} language in output
        Do not provide any explanation or justifications. provide simple output.
        
        Message: f"{message}"
        """
    
    message = oci.generative_ai_inference.models.UserMessage()
    message.content = [text_content]

    chat_request = oci.generative_ai_inference.models.GenericChatRequest()
    chat_request.messages = [message]
    chat_request.api_format = oci.generative_ai_inference.models.BaseChatRequest.API_FORMAT_GENERIC
    chat_request.num_generations = 1
    chat_request.max_tokens = 20
    chat_request.is_stream = False
    chat_request.temperature = 0.75
    chat_request.top_p = 0.7
    chat_request.top_k = -1
    chat_request.frequency_penalty = 1.0
    chat_request.max_tokens = 500

    chat_detail = oci.generative_ai_inference.models.ChatDetails()
    
    chat_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(model_id="meta.llama-3.2-90b-vision-instruct")
    chat_detail.compartment_id = compartment_id
    chat_detail.chat_request = chat_request

    chat_response = generative_ai_client.chat(chat_detail)
    output_message = None
    if chat_response.data.chat_response is not None and len(chat_response.data.chat_response.choices) > 0:
        output_message = chat_response.data.chat_response.choices[0].message

    output_text = None
    if output_message is not None and len(output_message.content) > 0:
        output_text = output_message.content[0].text

    print(f"Output: {output_text}")

    
    return output_text
    
def convertLocalImageFileToDataUrl(frame_path: str):
    """
    Convert a local image file to a data URL.
    """
    with open(frame_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

    _, extension = os.path.splitext(frame_path)
    mime_type = f"image/{extension[1:].lower()}"

    return f"data:{mime_type};base64,{encoded_string}"

def getClosedCaptionsForFrame(frame, frame_filename, genai_endpoint, source_language):
    generative_ai_client = getGenAIClient(genai_endpoint)
    compartment_id = "YOUR_OCI_RESOURCE_OCID"

    image_content = oci.generative_ai_inference.models.ImageContent()

    text_content = oci.generative_ai_inference.models.TextContent()
    language = LANGUAGE_CODE_TO_LANGUAGE[source_language]

    prompt_text = """
        You are a picture annotator. Given an image, generate a caption for a transcription in %s. The transcription should be enclosed in angular brackets (< >).

        ### INSTRUCTIONS:
        1. The caption must be a short phrase with ONLY A VERB (action) and An OBJECT (what the action is applied to). NO SUBJECT should be present.
        2. The caption MUST NOT EXCEED 8 tokens.
        3. DO NOT provide TRANSLATIONS of the captions.

        ### OUTPUT STRUCTURE:
        The structure of the response should ALWAYS be in the following format: <INSERT CAPTION TEXT HERE>

        If the image has only text, perform Optical Character recognition and RETURN the detected text as the caption.
        Only return the output caption. NO other description should be present.
        """ % (language)
    
    text_content.text = prompt_text
    message = oci.generative_ai_inference.models.UserMessage()

    image_url_str = convertLocalImageFileToDataUrl(frame_filename)
    image_url = oci.generative_ai_inference.models.ImageUrl(url=image_url_str)
    image_content = oci.generative_ai_inference.models.ImageContent(image_url=image_url)

    message.content = [text_content, image_content]
    message.role = "USER"
    chat_request = oci.generative_ai_inference.models.GenericChatRequest()
    chat_request.messages = [message]
    chat_request.api_format = oci.generative_ai_inference.models.BaseChatRequest.API_FORMAT_GENERIC
    chat_request.num_generations = 1
    chat_request.is_stream = False
    chat_request.temperature = 0.25
    chat_request.top_p = 0.7
    chat_request.top_k = -1
    chat_request.frequency_penalty = 1.0
    chat_request.max_tokens = 350

    chat_detail = oci.generative_ai_inference.models.ChatDetails()
    
    chat_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(model_id="meta.llama-3.2-90b-vision-instruct")
    chat_detail.compartment_id = compartment_id
    chat_detail.chat_request = chat_request

    retries = 0
    success = False
    chat_response = None
    while not success:
        try:
            if retries > MAX_RETRIES:
                break
            chat_response = generative_ai_client.chat(chat_detail)
            success = True
        except Exception as e:
            
            retries += 1
            time.sleep(3)

    if chat_response is None:
        print("Retries exhausted. No response received from GenAI!")
        return "<>"

    output_message = None
    if chat_response.data.chat_response is not None and len(chat_response.data.chat_response.choices) > 0:
        output_message = chat_response.data.chat_response.choices[0].message

    output_caption = None
    if output_message is not None and len(output_message.content) > 0:
        output_text = output_message.content[0].text
        output_caption, is_incorrect_format = parseOutputCaptions(output_text)
        print(f"Choosing \"{output_caption}\" as caption to be returned for this frame.")

    
    return f"[{output_caption}]", is_incorrect_format

def parseOutputCaptions(genai_output):
    try:
        list_start = genai_output.index("<")
        list_end = genai_output.index(">")
        caption = genai_output[list_start + 1 : list_end]
        return caption, False
    
    except ValueError as e:
        
        return genai_output, True
    

