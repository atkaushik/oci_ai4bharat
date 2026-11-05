import oci
import time
import os
import base64
import json
import random

import re
from load_env_data import load_env

from indic_trans import model_translate

load_env()




os_region = os.getenv('os_region')
speech_region = os.getenv('speech_region')
genai_region = os.getenv('genai_region')


input_srt_file = './examples/input.srt'


endpoint = 'https://inference.generativeai.us-chicago-1.oci.oraclecloud.com'

def translate_srt_with_gpt(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    blocks = []
    block = ""
    for line in lines:
        if line.strip() == "":
            if block:
                blocks.append(block.strip())
                block = ""
        else:
            block += line

    translated_blocks = []
    for b in blocks:
        lines_in_block = b.splitlines()
        if len(lines_in_block) >= 3:
            index = lines_in_block[0]
            timestamp = lines_in_block[1]
            text_lines = "\n".join(lines_in_block[2:])
            translated_text = genai_endpoint(text_lines, 'hi', 'en')
            translated_block = f"{index}\n{timestamp}\n{translated_text}\n\n"
            translated_blocks.append(translated_block)
        else:
            translated_blocks.append(b + "\n\n")  

    with open(output_file, 'w', encoding='utf-8') as file:
        file.writelines(translated_blocks)

    print(f"Done! Translated file saved to {output_file}")

def getSigner(profile_name):
    config = oci.config.from_file(profile_name=profile_name)
    # Avoid logging authentication configuration.
    
    
    
    
    
    signer = oci.signer.Signer(
                    tenancy=config['tenancy'],
                    user=config['user'],
                    fingerprint=config['fingerprint'],
                    private_key_file_location=config['key_file'],
                    pass_phrase=config['pass_phrase']
        )
    
    return config, signer

def getGenAIClient(endpoint):
    load_env()
    profile_name = os.getenv('oci_profile')
    config, signer = getSigner(profile_name)
    generative_ai_client = oci.generative_ai_inference.GenerativeAiInferenceClient(config=config, signer=signer, service_endpoint=endpoint,
                                                                retry_strategy=oci.retry.NoneRetryStrategy())
    return generative_ai_client

def genai_endpoint(message, source_language, target_language):
    load_env()
    generative_ai_client = getGenAIClient(endpoint)
    print(f"Input: {message}")
    compartment_id = os.getenv('compartment_id')
    

    text_content = oci.generative_ai_inference.models.TextContent()
    text_content.text = f"I have a piece of text in {source_language} language. Convert this text into {target_language} for me. I want only the translation. I don't want any text in {source_language}. Message: {message}"
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
    
    chat_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(model_id="meta.llama-3.3-70b-instruct")
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

def genai_endpoint_prompt(prompt, message, source_language, target_language):
    load_env()
    generative_ai_client = getGenAIClient(endpoint)
    
    compartment_id = os.getenv('compartment_id')
    

    text_content = oci.generative_ai_inference.models.TextContent()
    
    text_content.text = prompt
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
    
    chat_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(model_id="meta.llama-3.1-405b-instruct")
    chat_detail.compartment_id = compartment_id
    chat_detail.chat_request = chat_request

    chat_response = generative_ai_client.chat(chat_detail)
    output_message = None
    if chat_response.data.chat_response is not None and len(chat_response.data.chat_response.choices) > 0:
        output_message = chat_response.data.chat_response.choices[0].message

    output_text = None
    if output_message is not None and len(output_message.content) > 0:
        output_text = output_message.content[0].text

    

    
    return output_text



def read_srt(path):
    pattern = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3})\n(.+?)(?=\n\d+\n|\Z)', re.DOTALL)
    with open(path, "r", encoding="utf-8") as f:
        srt_content = f.read()
    return pattern.findall(srt_content)

def write_srt(entries, path):
    with open(path, "w", encoding="utf-8") as f:
        for index, timecode, text in entries:
            f.write(f"{index}\n{timecode}\n{text.strip()}\n\n")
        
        
        

def batch(entries, batch_size):
    for i in range(0, len(entries), batch_size):
        yield entries[i:i+batch_size]

def translate_text(text, source_language, target_language):
    prompt = (
        f"""
        Could you please translate the following subtitle text in {source_language} language to {target_language} language for me?

        1. First, analyze the key elements:
            - Identify main subject, verb, and objects
            - Note any idiomatic expressions
            - Mark technical terms or proper nouns
        2.   While creating Hindi terms for technical vocabulary, you should consider following in descending order of priority:
            -How they are translated in Indian Textbooks.
            -How they are used in hindi/sanskrit dictionaries like Prof Raghu Vira's dictionary.
            -How Indian Govt documents use them
            -The etymology of English term.
            -How such terms are created in mandarine, Korean, German etc
        3.   Consider cultural context:
            -Adjust formal/informal tone
            -Adapt metaphors if needed
            -Handle culture-specific references
        4. Create initial Hindi translation
        5. Refine for naturalness:
            -Mention English technical terms in brackets
            -Adjust word order for Hindi's SOV structure
            -Ensure gender agreement

        f"{text}"
        """
    )

    response = genai_endpoint_prompt(prompt, text, source_language, target_language)
    
    return response

def translate_srt_using_llm():
    input_srt = input_srt_file
    target_language = "hi"
    source_language = "en"
    output_srt = "output_2_"+target_language+".srt"
    batch_size = 5  

    entries = read_srt(input_srt)
    translated_entries = []

    for chunk in batch(entries, batch_size):
        
        
        
        combined = "\n".join([t[2].replace('\n', ' ') for t in chunk])
        print (combined)
        translated_text = translate_text(combined, source_language, target_language)
        
        print (translated_text)
        
        translated_lines = translated_text.split('\n')
        print (translated_lines)
        for (idx, timecode, _), translation in zip(chunk, translated_lines):
            translated_entries.append((idx, timecode, translation.strip()))
        
        
        

    
    print ("##########")
    print (translated_entries)
    
    

def translate_srt_using_ai4bharat():
    input_srt = input_srt_file
    target_language = "hi"
    source_language = "en"
    output_srt = "output_2_"+target_language+".srt"
    batch_size = 1  

    entries = read_srt(input_srt)
    translated_entries = []

    for chunk in batch(entries, batch_size):
        
        
       
        combined = "\n".join([t[2].replace('\n', ' ') for t in chunk])
        input_text = ['"' + combined + '"']
        
        
        
        
        input_path = 'indic_code/output_srts/YOUR_OCI_RESOURCE_OCID'
        translated_text = model_translate(input_text, source_language, target_language, input_path)
        

        
        

        translated_lines = translated_text
        print (translated_lines)
        for (idx, timecode, _), translation in zip(chunk, translated_lines):
            translated_entries.append((idx, timecode, translation.strip()))
            print (idx, timecode, _, translation)


        
        

    
    print ("##########")
    print (translated_entries)
    write_srt(translated_entries, output_srt)
    print(f"Translated SRT saved to {output_srt}")

if __name__ == "__main__":
    

    translate_srt_using_ai4bharat()