import re
from typing import List, Tuple
from tabulate import tabulate
import os


def parse_srt(srt_text: str) -> List[Tuple[str, str, str]]:
    entries = []
    blocks = re.split(r'\n{2,}', srt_text.strip())

    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) >= 2:
            
            if re.match(r'^\d+$', lines[0]):
                lines = lines[1:]
            if not lines:
                continue
            if re.match(r'\d{2}:\d{2}:\d{2},\d{3}\s-->\s\d{2}:\d{2}:\d{2},\d{3}', lines[0]):
                start, end = lines[0].split(' --> ')
                text = ' '.join(lines[1:]).strip()
                entries.append((start, end, text))
    return entries


def merge_subtitles(subs: List[Tuple[str, str, str]], max_chars=120) -> List[Tuple[str, str, str]]:
    merged = []
    buffer_text = ""
    buffer_start = None
    buffer_end = None

    for start, end, text in subs:
        if not text.strip():
            continue
        if not buffer_text:
            buffer_text = text
            buffer_start = start
            buffer_end = end
        elif len(buffer_text + " " + text) <= max_chars and not buffer_text.endswith(('.', '!', '?')):
            buffer_text += " " + text
            buffer_end = end
        else:
            merged.append((buffer_start, buffer_end, buffer_text.strip()))
            buffer_text = text
            buffer_start = start
            buffer_end = end
    if buffer_text:
        merged.append((buffer_start, buffer_end, buffer_text.strip()))
    return merged


def write_srt(subs: List[Tuple[str, str, str]], path: str):
    with open(path, 'w', encoding='utf-8') as f:
        for i, (start, end, text) in enumerate(subs, 1):
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

def write_srt_object(subs: List[Tuple[str, str, str]]):
        new_srt = []
        for i, (start, end, text) in enumerate(subs, 1):
            new_srt.append(f"{i}\n{start} --> {end}\n{text}\n\n")
        return new_srt


def show_table(subs: List[Tuple[str, str, str]]):
    print(tabulate(
        [(i+1, s, e, t) for i, (s, e, t) in enumerate(subs)],
        headers=["#", "Start", "End", "Text"],
        tablefmt="fancy_grid"
    ))


def run(input_file='input.srt', output_file='merged_output.srt', max_chars=120):
    with open(input_file, 'r', encoding='utf-8') as f:
        srt_content = f.read()

    parsed = parse_srt(srt_content)
    if not parsed:
        print("❌ No subtitles parsed.")
        return

    merged = merge_subtitles(parsed, max_chars=max_chars)
    write_srt(merged, output_file)
    print(f"✅ Successfully wrote {len(merged)} merged subtitles to '{output_file}'")
    show_table(merged)

def run_object(input_file, max_chars=120):
    
    

    parsed = parse_srt(input_file)
    if not parsed:
        print("❌ No subtitles parsed.")
        return

    merged = merge_subtitles(parsed, max_chars=max_chars)
    new_srt = write_srt_object(merged)
    
    
    return new_srt




def file_list(directory_path):
    return [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]












