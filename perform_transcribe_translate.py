import oci
import time
import argparse
import math
from pathlib import Path

from utils import getSpeechClient, getObjectStorageClient, getEndpoints
from model_entry import translate_srt
from closed_captions import addClosedCaptions

import os

from dotenv import load_dotenv, dotenv_values 

load_dotenv() 

terminal_states = ["SUCCEEDED", "FAILED", "CANCELED", "PARTIALLY_SUCCEEDED"]


output_srt_file_directory = "./output_srts"
output_translated_srt_file_directory = "./translated_srts"

def createTranscriptionJob(ai_client, object_storage_info, language_code):
    
    sample_display_name = "test_mp4_batch"

    sample_freeform_tags = {}
    sample_description = "This is newly created Job"

    sample_object_location = oci.ai_speech.models.ObjectLocation(namespace_name=object_storage_info["object_input_namespace"], bucket_name=object_storage_info["object_input_bucket"],
    object_names=object_storage_info["object_input_job_list"])
    sample_input_location = oci.ai_speech.models.ObjectListInlineInputLocation(
    location_type="OBJECT_LIST_INLINE_INPUT_LOCATION", object_locations=[sample_object_location])

    sample_output_location = oci.ai_speech.models.OutputLocation(namespace_name=object_storage_info["object_output_namespace"], bucket_name=object_storage_info["object_output_bucket"])
    sample_normalization = oci.ai_speech.models.TranscriptionNormalization(is_punctuation_enabled=True, filters=[])
    sample_diarization = oci.ai_speech.models.Diarization(is_diarization_enabled=False)
    sample_transcription_settings = oci.ai_speech.models.TranscriptionSettings(diarization=sample_diarization)

    
    sample_model_details = oci.ai_speech.models.TranscriptionModelDetails(language_code=language_code, model_type="WHISPER_LARGE_V2", transcription_settings=sample_transcription_settings)

    
    transcription_job_details = oci.ai_speech.models.CreateTranscriptionJobDetails(display_name=sample_display_name,
    compartment_id=object_storage_info["compartment_id"],
    description=sample_description,
    model_details=sample_model_details,
    input_location=sample_input_location,
    additional_transcription_formats=["SRT"], 
    normalization=sample_normalization,
    output_location=sample_output_location,
    freeform_tags=sample_freeform_tags)

    transcription_job = None
    start_time = 0
    try:
        start_time = time.time()
        transcription_job = ai_client.create_transcription_job(create_transcription_job_details=transcription_job_details)
        return (time.time() - start_time), transcription_job.data

    except Exception as e:
        print(e)

    return (time.time() - start_time), None

def pollForJobStatus(job_id, ai_client):
    job_details = ai_client.get_transcription_job(transcription_job_id=job_id)
    return job_details.data.lifecycle_state

def uploadTranslatedSRT(object_storage_client, updated_blocks, object_storage_info, output_file_prefix):
    srt = ""
    for index, timestamp, text in updated_blocks:
        srt += f"{index}\n{timestamp}\n{text}\n\n"
    updated_srt = srt.encode('utf-8')
    object_storage_client.put_object(namespace_name=object_storage_info["object_output_namespace"], bucket_name=object_storage_info["object_output_bucket"], object_name=output_file_prefix, put_object_body=updated_srt)

def fetchAndDownloadSRT(object_storage_client, job_id, object_storage_info):    
    
    os_prefix = "job-" + job_id.split(".")[-1] + "/" + object_storage_info["object_input_namespace"] + "_" + object_storage_info["object_input_bucket"] + "_"
    output_file_names = []
    for file_name in object_storage_info["object_input_job_list"]:
        
        file_prefix = os_prefix + file_name
        
        
        response = object_storage_client.list_objects(namespace_name=object_storage_info["object_output_namespace"], bucket_name=object_storage_info["object_output_bucket"], prefix=file_prefix)

        
        for output_object in response.data.objects:
            object_name = output_object.name
            file_stream = None
            if object_name.split(".")[-1] != "srt":
                continue
            
            print(f"Output name for the SRT file: {object_name}")
            
            object_response = object_storage_client.get_object(
                namespace_name=object_storage_info["object_output_namespace"],
                bucket_name=object_storage_info["object_output_bucket"],
                object_name=object_name
            )
            file_stream = object_response.data.raw.data
            if file_stream is None:
                print(f"The output SRT file for the job {job_id} is not found, or some error occurred while downloading the output file for the file {file_name}.")
                exit(1)
            else:
                
                output_file_name = createOutputSrtFile(job_id=job_id, file_name=file_name, file_stream=file_stream)
                output_file_names.append([output_file_name, file_prefix])

    return output_file_names

def createOutputSrtFile(job_id, file_name, file_stream):
    output_file_name = output_srt_file_directory + "/" + job_id + "/" + file_name + ".srt"

    
    output_dir_to_create = output_file_name[0 : output_file_name.rfind("/")]
    Path(output_dir_to_create).mkdir(parents=True, exist_ok=True)
    
    
    with open(output_file_name, "wb+") as f:
        f.write(file_stream)

    print(f"FILE IS STORED AT: {output_file_name}\n")
    return output_file_name

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
                    prog='Transcribe + Translate',
                    description='Transcribe + Translate',
                    epilog='Transcribe + Translate')
    
    
    parser.add_argument('--model', '-m', required=True, choices=["genai", "helsinki", "ai4bharat"], default="helsinki")
    parser.add_argument('--source_language', '-s', required=False, default="en")
    parser.add_argument('--target_languages', '-t', required=False, default="hi")
    parser.add_argument('--enable_closed_captions', '-e', action="store_true")
    parser.add_argument('--cc_model', '-c', required=False, choices=["blip", "genai"], default="genai")
    parser.add_argument('--min_silence_duration', '-d', required=False, default=3000, type=int)

    
    os_region = "us-ashburn-1"
    speech_region = "us-ashburn-1"
    genai_region = "us-chicago-1"
    endpoints = getEndpoints(os_region, speech_region, genai_region)

    args = parser.parse_args()
    model = args.model
    source_language = args.source_language
    target_language_str = args.target_languages
    target_languages = target_language_str.split(",")
    enable_closed_captions = bool(args.enable_closed_captions)
    cc_model = args.cc_model
    min_silence_duration = args.min_silence_duration

    
    object_input_namespace = "YOUR_OBJECT_STORAGE_NAMESPACE"
    object_input_bucket = "YOUR_BUCKET_NAME"
    object_output_namespace = "YOUR_OBJECT_STORAGE_NAMESPACE"
    object_output_bucket = "YOUR_BUCKET_NAME"
    

    
    object_input_job_list = ["test_mp4/5mins_mp4.mp4"]
    
    
    
    

    compartment_id = "YOUR_OCI_RESOURCE_OCID"

    object_storage_info = {
        "object_input_namespace": object_input_namespace,
        "object_input_bucket": object_input_bucket,
        "object_output_namespace": object_output_namespace,
        "object_output_bucket": object_output_bucket,
        "object_input_job_list": object_input_job_list,
        "compartment_id": compartment_id
    }

    ai_client = getSpeechClient(endpoints["SPEECH"])
    time_taken, response = createTranscriptionJob(ai_client, object_storage_info, source_language)
    print(f"Job submitted. API Response: {response}")
    job_id = response.id

    job_status = None
    while True:
        job_status = pollForJobStatus(job_id=job_id, ai_client=ai_client)
        print(f"Current job status: {job_status}")
        if job_status in terminal_states:
            break
        
        time.sleep(5)

    if job_status is None or job_status != "SUCCEEDED":
        print(f"There was some error in transcription of the job {job_id}. The status is {job_status}")
        exit(1)

    print("\n Job has succeeded!")
    print("\n-------------------------\n")
    print("Pulling output SRT files from Object Storage\n")
    
    object_storage_client = getObjectStorageClient(service_endpoint=endpoints['OS'])

    pre_translated_srt_files = fetchAndDownloadSRT(object_storage_client, job_id, object_storage_info)

    for i, pre_translated_srt_file in enumerate(pre_translated_srt_files):
        srt_file = pre_translated_srt_file[0]
        file_prefix = pre_translated_srt_file[1]
        updated_srt = srt_file
        
        print(f"Is closed captions enabled? {enable_closed_captions}")
        if enable_closed_captions:
            
            video_details_for_closed_captions = {
                "BUCKET": object_input_bucket,
                "NAMESPACE": object_input_namespace,
                "OBJECT": object_input_job_list[i],
                "SERVICE_ENDPOINT": endpoints['OS'],
            }
            print(f"Adding closed captions for {srt_file}.")
            updated_srt = addClosedCaptions(video_details_for_closed_captions, srt_file, endpoints['GENAI'], source_language, cc_model, min_silence_duration)
            print(f"Finished adding closed captions into {updated_srt}.")

        for target_language in target_languages:
            print(f"Translating the files to {target_language}.")
            translated_srt_file = output_translated_srt_file_directory + updated_srt[len(output_srt_file_directory):]
            translated_srt_file = translated_srt_file[0 : translated_srt_file.rfind(".")] + f"_{target_language}.srt"

            
            output_dir_to_create = translated_srt_file[0 : translated_srt_file.rfind("/")]
            Path(output_dir_to_create).mkdir(parents=True, exist_ok=True)
            updated_blocks = translate_srt(updated_srt, translated_srt_file, source_language, target_language, model, endpoints)

            output_file_prefix = f"{file_prefix}_{source_language}_to_{target_language}.srt"
            uploadTranslatedSRT(object_storage_client, updated_blocks, object_storage_info, output_file_prefix)