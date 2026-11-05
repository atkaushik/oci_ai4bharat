import oci
import os
import time
import argparse
import math
from pathlib import Path

from utils import getSpeechClient, getObjectStorageClient, getEndpoints
from model_entry import translate_srt

import json

from load_env_data import load_env




terminal_states = ["SUCCEEDED", "FAILED", "CANCELED", "PARTIALLY_SUCCEEDED"]


output_srt_file_directory = "./output_srts"
output_translated_srt_file_directory = "./translated_srts"

def createTranscriptionJob(ai_client, object_storage_info, language_code):
    
    load_env()

    print ("createTranscriptionJob - object_storage_info", object_storage_info)
    print ("createTranscriptionJob - language_code", language_code)
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

    

    model_type = os.getenv('model_type')
    print ("model type in env file: ", model_type)

    if model_type == "ORACLE":
        
        lang_code = str(language_code)+"-"+"IN"
    else:
        lang_code = language_code

    print ("lang_code: ", lang_code)
    print ("lamodel_typeng_code: ", model_type)
    print ("sample_transcription_settings: ", sample_transcription_settings)

    sample_model_details = oci.ai_speech.models.TranscriptionModelDetails(language_code=lang_code, model_type=model_type, transcription_settings=sample_transcription_settings)

    
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
        
        print ("%%%%%%%%%%%%%")
        print ("File name in bucket: ", file_name)
        file_prefix = os_prefix + file_name
        print ("file prefix for object: ", file_prefix)
        output_file_name = None
        
        response = object_storage_client.list_objects(namespace_name=object_storage_info["object_output_namespace"], bucket_name=object_storage_info["object_output_bucket"], prefix=file_prefix)

        
        for output_object in response.data.objects:
            object_name = output_object.name
            print ("$$$$$$$$$$$$$$$$$$$")
            print ("Object names in bucket - "+str({object_storage_info["object_output_bucket"]})+" : ", object_name)
            file_stream = None
            
            if object_name != file_prefix+".srt":
                continue
            
            print(f"Output name for the SRT file: {object_name}")
            
            object_response = object_storage_client.get_object(
                namespace_name=object_storage_info["object_output_namespace"],
                bucket_name=object_storage_info["object_output_bucket"],
                object_name=object_name
            )
            file_stream = object_response.data.raw.data
            print (file_stream)
            if file_stream is None:
                print(f"The output SRT file for the job {job_id} is not found, or some error occurred while downloading the output file for the file {file_name}.")
                exit(1)
            else:
                
                output_file_name = createOutputSrtFile(job_id=job_id, file_name=file_name, file_stream=file_stream)
                updateEnv("output_file_name", output_file_name)
                print ("output_file_name: ", output_file_name)
                output_file_names.append(output_file_name)
                output_file_names.append(file_prefix)
    print (output_file_name, file_prefix)
    
    return output_file_names

def createOutputSrtFile(job_id, file_name, file_stream):
    load_env()
    output_srt_file_directory = os.getenv('output_srt_file_directory')
    output_file_name = output_srt_file_directory + "/" + job_id + "/" + file_name + ".srt"
    print ("output_file_name: ", output_file_name)
    
    output_dir_to_create = output_file_name[0 : output_file_name.rfind("/")]
    Path(output_dir_to_create).mkdir(parents=True, exist_ok=True)
    
    
    with open(output_file_name, "wb+") as f:
        f.write(file_stream)
    updateEnv("output_file_name", output_file_name)
    print(f"FILE IS STORED AT: {output_file_name}\n")
    return output_file_name

def updateEnv(key_name, key_value):
    new_key = key_name
    new_value = json.dumps(key_value)

    
    
    env_path = str(Path(__file__).resolve().parent / ".env")
    key_exists = False

    with open(env_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            if line.startswith(f"{new_key}="):
                key_exists = True
                break
                
    
    if key_exists:
        
        with open(env_path, 'w') as file:
            for line in lines:
                if line.startswith(f"{new_key}="):
                    file.write(f"{new_key}={new_value}\n")
                else:
                    file.write(line)
    else:
        
        with open(env_path, 'a') as file:
            file.write(f"{new_key}={new_value}\n")

    print(f"{new_key} set to {new_value} in .env file.")

def file_to_translate():
    load_env()
  
    
    
    
    print ("source_srt: ", os.getenv('output_file_name'))

    x= os.getenv('output_file_name')
    
    

    
    
    

    
    files_input = []
    
    
    
    
    
    
    files_input.append(x)
    print (files_input)
    
    return files_input

def define_variables_env():
    
    load_env()
    object_input_job_list = []
    os_region = os.getenv('os_region')
    speech_region = os.getenv('speech_region')
    genai_region = os.getenv('genai_region')
    os_region= os.getenv('os_region')
    speech_region=os.getenv('speech_region')
    genai_region=os.getenv('genai_region')
    object_input_namespace=os.getenv("object_input_namespace")
    object_input_bucket=os.getenv('object_input_bucket')
    object_output_namespace=os.getenv('object_output_namespace')
    object_output_bucket=os.getenv('object_output_bucket')
    object_input_job_list.append(os.getenv('input_video'))
    compartment_id=os.getenv('compartment_id')
    output_srt_file_directory=os.getenv('output_srt_file_directory')
    output_translated_srt_file_directory=os.getenv('output_translated_srt_file_directory')
    oci_profile=os.getenv('oci_profile')
    

    
    
    updateEnv('source_srt', "")
    updateEnv('output_file_name', "")


    print ("os_region: ",os_region)
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


    endpoints = getEndpoints(os_region, speech_region, genai_region)
    print ("endpoints: ", endpoints)

    args = parser.parse_args()
    model = args.model
    source_language = args.source_language
    target_language_str = args.target_languages
    target_languages = target_language_str.split(",")
    enable_closed_captions = bool(args.enable_closed_captions)
    cc_model = args.cc_model
    min_silence_duration = args.min_silence_duration


    

    object_storage_info = {
        "object_input_namespace": object_input_namespace,
        "object_input_bucket": object_input_bucket,
        "object_output_namespace": object_output_namespace,
        "object_output_bucket": object_output_bucket,
        "object_input_job_list": object_input_job_list,
        "compartment_id": compartment_id
    }

    ai_client = getSpeechClient(endpoints["SPEECH"])
    
    
    return ai_client, object_storage_info, source_language, endpoints, enable_closed_captions, target_languages, model

def run_stt_job_on_oci(ai_client, object_storage_info, source_language):
    load_env()

    
    updateEnv('job_id', "")
    time_taken, response = createTranscriptionJob(ai_client, object_storage_info, source_language)
    print(f"Job submitted. API Response: {response}")
    job_id = response.id
    print ("job id created: ", job_id)
    updateEnv("job_id", job_id)

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
    job_id_env = os.getenv('job_id')
    print ("job_id_env: ", job_id_env)

def translate_input_srt(files_input):
    load_env()
    for i, pre_translated_srt_file in enumerate(files_input):
    

        print("index: ", i)
        print ("pre_translated_srt_file: ", pre_translated_srt_file)
        print ("pre_translated_srt_files: ", pre_translated_srt_files)
        srt_file = pre_translated_srt_files[0]
        file_prefix = pre_translated_srt_files[1]
        print ("srt_file: ", srt_file, 
               "file_prefix: ", file_prefix)
        updated_srt = srt_file
        
        print ("updated_srt: ", updated_srt)
        print(f"Is closed captions enabled? {enable_closed_captions}")


        if enable_closed_captions:
            
            video_details_for_closed_captions = {
                "BUCKET": os.getenv('object_input_bucket'),
                "NAMESPACE": os.getenv('object_input_namespace'),
                "OBJECT": os.getenv('object_input_job_list'[i]),
                "SERVICE_ENDPOINT": endpoints['OS'],
            }
            print(f"Adding closed captions for {srt_file}.")
            updated_srt = addClosedCaptions(video_details_for_closed_captions, srt_file, endpoints['GENAI'], source_language, cc_model, min_silence_duration)
            print(f"Finished adding closed captions into {updated_srt}.")

        for target_language in target_languages:
            print(f"Translating the files to {target_language}.")
            translated_srt_file = output_translated_srt_file_directory + updated_srt[len(output_srt_file_directory):]
            translated_srt_file = translated_srt_file[0 : translated_srt_file.rfind(".")] + f"_{target_language}_{model}.srt"

            
            output_dir_to_create = translated_srt_file[0 : translated_srt_file.rfind("/")]
            Path(output_dir_to_create).mkdir(parents=True, exist_ok=True)
            print ("output_dir_to_create: ", output_dir_to_create)
            print ("translated_srt_file: ", translated_srt_file)
            updated_blocks = translate_srt(updated_srt, translated_srt_file, source_language, target_language, model, endpoints)
            
            output_file_prefix = f"{file_prefix}_{source_language}_to_{target_language}_{model}.srt"
            uploadTranslatedSRT(object_storage_client, updated_blocks, object_storage_info, output_file_prefix)

if __name__ == "__main__":

    load_env()
    
    ai_client, object_storage_info, source_language, endpoints, enable_closed_captions, target_languages, model = define_variables_env()

    

    
    run_stt_job_on_oci(ai_client, object_storage_info, source_language)

    
    
    print ("####################")
    

    object_storage_client = getObjectStorageClient(service_endpoint=endpoints['OS'])
    job_id_env = os.getenv('job_id')
    print ("job_id_env: ", job_id_env)
    
    
    pre_translated_srt_files = fetchAndDownloadSRT(object_storage_client, job_id_env, object_storage_info)
    
    print ("pre_translated_srt_files: ", pre_translated_srt_files[0])
    updateEnv("source_srt", pre_translated_srt_files[0])

    
    
    

    

    files_input = file_to_translate()

    print ("files_input: ", files_input)

    
    

    
