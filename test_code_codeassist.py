import re
from indic_trans_test import model_translate




def translate_sentences(grouped_sentences):
    translated = []
    
    for start, end, text in grouped_sentences:
        english = model_translate([text],'hi','en','input_file')
        translated.append((start, end, english))

    return translated

def translate_srt_file(hindi_srt_path, english_srt_path):
    
    
    with open(hindi_srt_path, 'r', encoding='utf-8') as hindi_file:
        lines = hindi_file.readlines()

    
    translated_lines = []
    subtitle_block = []
    
    for line in lines:
        line = line.strip()
        if line:
            subtitle_block.append(line)
        else:
            if subtitle_block:
                
                if len(subtitle_block) > 2:  
                    try:
                        
                        print (subtitle_block[2])
                        translation = model_translate(subtitle_block[2],'hi','en','input_file')
                        
                        print ("%%%%%%%%%%%%")
                        print (translation)
                        
                        translated_subtitle_block = subtitle_block[:2] + translation
                        translated_lines.extend(translated_subtitle_block)
                        translated_lines.append('')  
                    except Exception as e:
                        print(f"Failed to translate: {subtitle_block[2]}. Error: {e}")
                        
                else:
                    translated_lines.extend(subtitle_block)
                    translated_lines.append('')
            subtitle_block = []

    
    if subtitle_block:
        try:
            
            print (subtitle_block[2])
            translation = model_translate(subtitle_block[2],'hi','en','input_file')
            print ("%%%%%%%%%%%%")
            print (translation)
            
            translated_subtitle_block = subtitle_block[:2] + translation
            translated_lines.extend(translated_subtitle_block)
            translated_lines.append('')
        except Exception as e:
            print(f"Failed to translate: {subtitle_block[2]}. Error: {e}")

    with open(english_srt_path, 'w', encoding='utf-8') as english_file:
        english_file.write('\n'.join(translated_lines))



hindi_srt_path = './examples/input.srt'
english_srt_path = './examples/input.srt'
translate_srt_file(hindi_srt_path, english_srt_path)