import re
from typing import List, Tuple

from indic_trans import model_translate
from genai_client import translate_using_genai

def load_srt(file_path: str) -> List[Tuple[str, str, str]]:
    """Load an SRT file and extract index, timestamp, and text."""
    with open(file_path, 'r', encoding='utf-8') as file:
        srt_content = file.read()

    matches = re.findall(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\Z)', srt_content, re.DOTALL)
    return [(index, timestamp, text.replace('\n', ' ')) for index, timestamp, text in matches]

def group_sentences(subtitles: List[Tuple[str, str, str]]) -> List[Tuple[List[Tuple[str, str, str]], str]]:
    """Group subtitle segments into full sentences."""
    sentence_groups = []
    temp_group = []
    temp_text = ""

    for segment in subtitles:
        index, timestamp, text = segment
        temp_group.append(segment)
        temp_text += " " + text.strip()

        if re.search(r'[.!?\]]$', text.strip()):  
            sentence_groups.append((temp_group, temp_text.strip()))
            temp_group = []
            temp_text = ""

    
    if temp_group:
        sentence_groups.append((temp_group, temp_text.strip()))

    return sentence_groups

def translate_texts(sentences: List[str], target_language: str) -> List[str]:
    """Translate a list of full sentences using Hugging Face models."""
    translator = pipeline("translation", model=f"Helsinki-NLP/opus-mt-en-{target_language}")
    return [translator(sentence, max_length=512)[0]['translation_text'] for sentence in sentences]

def redistribute_translations(groups: List[Tuple[List[Tuple[str, str, str]], str]], translations: List[str]) -> List[Tuple[str, str, str]]:
    """Break translated sentences back into subtitle segments."""
    updated_subtitles = []
    
    for (segments, original_text), translated_text in zip(groups, translations):
        
        words = translated_text.split()
        print (words)
        word_index = 0
        for index, timestamp, _ in segments:
            segment_word_count = len(_.split())  
            print (segment_word_count)
            translated_segment = " ".join(words[word_index: word_index + segment_word_count])
            updated_subtitles.append((index, timestamp, translated_segment))
            word_index += segment_word_count
            print (segment_word_count, translated_segment, index, timestamp, _, word_index)
    return updated_subtitles

def save_srt(file_path: str, subtitles: List[Tuple[str, str, str]]):
    """Save updated subtitles back into an SRT file."""
    with open(file_path, 'w', encoding='utf-8') as file:
        for index, timestamp, text in subtitles:
            file.write(f"{index}\n{timestamp}\n{text}\n\n")

def translate_texts_helsinki(texts: List[str], source_language: str, target_language: str) -> List[str]:
    """Translate a list of strings to the target language using a HuggingFace translation pipeline."""
    translator = pipeline("translation", model=f"Helsinki-NLP/opus-mt-{source_language}-{target_language}")
    translated = [translator(text, max_length=512)[0]['translation_text'] for text in texts]
    return translated

def fix_bracket_alignment(updated_srt):
    for i in range(0, len(updated_srt)):
        (index, timestamp, translated_segment) = updated_srt[i]
        if translated_segment is not None and translated_segment != "" and translated_segment[0] == '[' and translated_segment[-1] != ']':
            updated_srt[i] = (index, timestamp, translated_segment + "]")
        elif translated_segment is not None and translated_segment != "" and translated_segment[0] != '[' and translated_segment[-1] == ']':
            updated_srt[i] = (index, timestamp, "[" + translated_segment)
    
    return updated_srt

def translate_srt(input_path: str, output_path: str, source_language: str, target_language: str, model: str, endpoints: dict):
    print (input_path, output_path, source_language, target_language, model, endpoints)
    subtitles = load_srt(input_path)
    sentence_groups = group_sentences(subtitles)
    print ("sentence_groups: ", sentence_groups)
    full_sentences = [text for _, text in sentence_groups]
    
    if model == "helsinki":
        print("Using Helsinki NLP model")
        translations = translate_texts_helsinki(full_sentences, source_language, target_language)
    elif model == "genai":
        print("Using GenAI Llama model")
        translations = translate_using_genai(full_sentences, source_language, target_language, input_path, endpoints["GENAI"])
    elif model == "ai4bharat":
        print("Using Ai4Bharat model")
        translations = model_translate(full_sentences, source_language, target_language, input_path)
    else:
        print("Incorrect model option!")
        return
    
    print("Completed translation of texts")

    
    
    print("Replaced translated texts into blocks")
    updated_subtitles = redistribute_translations(sentence_groups, translations)
    
    
    updated_subtitles = fix_bracket_alignment(updated_subtitles)
    
    
    save_srt(output_path, updated_subtitles)

    print(f"Output translated SRT is stored in {output_path}")
    return updated_subtitles