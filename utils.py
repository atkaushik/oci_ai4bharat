import oci
import os
import time
from load_env_data import load_env

load_env()
service_endpoint = os.getenv('service_endpoint')
profile_name = os.getenv('oci_profile')
service_endpoint = os.getenv('service_endpoint')
speech_region = os.getenv('speech_region')
os_region = os.getenv('os_region')
genai_region = os.getenv('genai_region')


def getSigner(profile_name):
    config = oci.config.from_file(profile_name=profile_name)
    
    
    
    
    
    
    signer = oci.signer.Signer(
                    tenancy=config['tenancy'],
                    user=config['user'],
                    fingerprint=config['fingerprint'],
                    private_key_file_location=config['key_file'],
                    pass_phrase=config['pass_phrase']
        )
    
    return config, signer

def getSpeechClient(service_endpoint=service_endpoint):
    load_env()
    profile_name = os.getenv('oci_profile')
    config, signer = getSigner(profile_name)
    ai_client = oci.ai_speech.AIServiceSpeechClient(config, service_endpoint=service_endpoint, signer=signer)
    return ai_client

def getGenAIClient(service_endpoint):
    load_env()
    profile_name = os.getenv('oci_profile')
    config, signer = getSigner(profile_name)
    generative_ai_client = oci.generative_ai_inference.GenerativeAiInferenceClient(config=config, signer=signer, service_endpoint=service_endpoint,
                                                                retry_strategy=oci.retry.NoneRetryStrategy())
    return generative_ai_client

def getObjectStorageClient(service_endpoint):
    load_env()
    profile_name = os.getenv('oci_profile')
    config, signer = getSigner(profile_name)
    os_client = oci.object_storage.ObjectStorageClient(config, signer=signer, service_endpoint=service_endpoint)
    return os_client

def downloadVideo(video_details):
    bucket = video_details["BUCKET"]
    namespace = video_details["NAMESPACE"]
    object_name = video_details["OBJECT"]

    print(f"Downloading video {object_name}")
    dir_name = "./temp_videos"
    os.makedirs(dir_name, exist_ok=True)
    temp_storage_location = os.path.join(dir_name, object_name)
    output_dir_to_create = temp_storage_location[0 : temp_storage_location.rfind("/")]

    if os.path.exists(temp_storage_location):
        print(f"Video file already exists at: {temp_storage_location}\n")
        return temp_storage_location

    os_client = getObjectStorageClient(video_details["SERVICE_ENDPOINT"])

    object_response = os_client.get_object(
        namespace_name=namespace,
        bucket_name=bucket,
        object_name=object_name
    )
    file_stream = object_response.data.raw.data
    os.makedirs(output_dir_to_create, exist_ok=True)

    with open(temp_storage_location, "wb+") as f:
        f.write(file_stream)

    print(f"Video file temporarily stored at: {temp_storage_location}\n")
    return temp_storage_location

def deleteTempVideoFileAndFrames(video_file_path, frame_filenames):
    try:
        if os.path.exists(video_file_path):
            os.remove(video_file_path)
        else:
            print(f"The file {video_file_path} does not exist")

        for filename in frame_filenames:
            if os.path.exists(filename):
                os.remove(filename)
            else:
                print(f"The file {filename} does not exist")

    except Exception as e:
        print(f"Some error occurred during file cleanup: {e}")
        return False
    finally:
        return True

def getEndpoints(os_region, speech_region, genai_region):
    endpoints = {
        "SPEECH": f"https://speech.aiservice.{speech_region}.oci.oraclecloud.com",
        "OS": f"https://objectstorage.{os_region}.oraclecloud.com",
        "GENAI": f"https://inference.generativeai.{genai_region}.oci.oraclecloud.com"
    }

    return endpoints