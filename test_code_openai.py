import re
from indic_trans_test import model_translate


def read_srt_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def parse_srt_blocks(srt_content):
    entries = srt_content.strip().split('\n\n')
    blocks = []
    for entry in entries:
        lines = entry.strip().split('\n')
        if len(lines) >= 3:
            index = lines[0]
            timestamp = lines[1]
            text = ' '.join(lines[2:])
            blocks.append((index, timestamp, text))
    return blocks


def group_blocks_into_sentences(blocks):
    grouped = []
    current_text = ''
    temp_blocks = []
    time_pattern = r'(\d{2}:\d{2}:\d{2},\d{3})\s-->\s(\d{2}:\d{2}:\d{2},\d{3})'

    for _, timestamp, text in blocks:
        current_text += ' ' + text
        temp_blocks.append(timestamp)
        if re.search(r'[।!?]$', text.strip()):
            start_time = re.match(time_pattern, temp_blocks[0]).group(1)
            end_time = re.match(time_pattern, temp_blocks[-1]).group(2)
            grouped.append((start_time, end_time, current_text.strip()))
            current_text = ''
            temp_blocks = []

    if current_text.strip() and temp_blocks:
        start_time = re.match(time_pattern, temp_blocks[0]).group(1)
        end_time = re.match(time_pattern, temp_blocks[-1]).group(2)
        grouped.append((start_time, end_time, current_text.strip()))

    return grouped



def translate_sentences(grouped_sentences):
    translated = []
    
    for start, end, text in grouped_sentences:
        english = model_translate([text],'hi','en','input_file')
        translated.append((start, end, english))

    return translated


def list_to_sentence(lst):
    """Converts a list containing a single string to a sentence."""
    if len(lst) == 1 and isinstance(lst[0], str):
        return lst[0]
    else:
        raise ValueError("Input list must contain a single string element.")
    


def create_srt_content(translated_entries):
    entry = translated_entries
    
    
    
    srt_lines = []
    for i, (start, end, text) in enumerate(entry, start=1):
        srt_lines.append(str(i))
        srt_lines.append(f"{start} --> {end}")
        t = list_to_sentence(text)
        srt_lines.append(t)
        srt_lines.append("")  
    return '\n'.join(srt_lines)


def translate_srt_file(input_srt, output_srt):
    srt_content = read_srt_file(input_srt)
    
    blocks = parse_srt_blocks(srt_content)
    print ("##################")
    
    grouped = group_blocks_into_sentences(blocks)
    print ("##################")
    
    translated = translate_sentences(grouped)
   
    srt_result = create_srt_content(translated)
    with open(output_srt, 'w', encoding='utf-8') as f:
        f.write(srt_result)
    print(f"✅ Translated SRT saved to {output_srt}")


translate_srt_file('hind_srt.srt', 'translated_output.srt')
