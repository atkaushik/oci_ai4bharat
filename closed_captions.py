import os
import cv2
import pysrt
import time
from datetime import datetime, timedelta

from utils import downloadVideo, deleteTempVideoFileAndFrames
from genai_client import getClosedCaptionsForFrame
from cc_models import getBlipClosedCaptionsForFrame



def timestamp_to_milliseconds(timestamp):
    """Convert SRT timestamp to milliseconds."""
    return (
        timestamp.hours * 3600000 +
        timestamp.minutes * 60000 +
        timestamp.seconds * 1000 +
        timestamp.milliseconds
    )

def get_silent_periods(subs, min_silence_duration):
    """Find silent periods between subtitles."""
    print(f"MIN SILENCE DURATION: {min_silence_duration}")
    silent_periods = []
    for i in range(len(subs) - 1):
        end_time = timestamp_to_milliseconds(subs[i].end)
        start_time = timestamp_to_milliseconds(subs[i + 1].start)
        if start_time > end_time and (start_time - end_time) > min_silence_duration:
            silent_periods.append((end_time, start_time))
    return silent_periods

def extract_frames(video_path, silent_periods):
    """Extract frames from silent periods."""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames, frames_filenames = [], []
    temp_dir = "./temp_frames"
    os.makedirs(temp_dir, exist_ok=True)
    
    for start, end in silent_periods:
        timestamp = (start + end) // 2  
        frame_number = int((timestamp / 1000) * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        success, frame = cap.read()
        if success:
            frames.append((timestamp, frame))
            timestamp = frame_number / fps
            frame_filename = os.path.join(temp_dir, f"frame_{frame_number:05d}.png")
            frames_filenames.append(frame_filename)
            cv2.imwrite(frame_filename, frame)  

    cap.release()
    return frames, frames_filenames

def insert_silence_captions(srt_path, silent_periods, analyses):
    """Insert analysis text into SRT file during silent periods."""
    subs = pysrt.open(srt_path)
    new_subs = list(subs)  

    
    for (start, end), text in zip(silent_periods, analyses):
        new_sub = pysrt.SubRipItem()
        new_sub.start = pysrt.SubRipTime(milliseconds=start)
        new_sub.end = pysrt.SubRipTime(milliseconds=end)
        new_sub.text = text
        new_subs.append(new_sub)

    
    new_subs.sort(key=lambda x: timestamp_to_milliseconds(x.start))

    
    for i, sub in enumerate(new_subs, start=1):
        sub.index = i

    
    pysrt.SubRipFile(new_subs).save(srt_path, encoding="utf-8")

    return srt_path

def addClosedCaptions(video_details, srt_path, genai_endpoint, source_language, cc_model, min_silence_duration):
    video_path = downloadVideo(video_details)
    subs = pysrt.open(srt_path)
    silent_periods = get_silent_periods(subs, min_silence_duration)

    frames, frame_filenames = extract_frames(video_path, silent_periods)

    analyses = []
    if frames == None or len(frames) == 0:
        print(f"No silent periods observed in the file {srt_path}. No need for closed captioning!")
        return

    print(f"Number of frames to analyze: {len(frames)}")
    i, incorrect_format_count = 0, 0
    while i < len(frames):
        analysis_text = None
        (timestamp, frame) = frames[i]
        if cc_model == "genai":
            print(f"Using OCI Gen AI model for closed captioning for Frame {i}")
            analysis_text, is_incorrect_format = getClosedCaptionsForFrame(frame, frame_filenames[i], genai_endpoint, source_language)
            if is_incorrect_format:
                incorrect_format_count += 1
        elif cc_model == "blip":
            print("Using BLIP model for closed captioning")
            analysis_text = getBlipClosedCaptionsForFrame(frame_filenames[i])

        analyses.append(analysis_text)
        
        time.sleep(3)
        i += 1

    print(f"Number of incorrectly formatted responses: {incorrect_format_count}")
    print(f"All frames captions: {analyses}")
    updated_srt = insert_silence_captions(srt_path, silent_periods, analyses)
    print(f"Updated SRT file saved as: {updated_srt}")

    
    deleteTempVideoFileAndFrames(video_path, frame_filenames)

    return updated_srt












