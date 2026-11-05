import json
import os
import oci
import re


config = oci.config.from_file(profile_name=os.getenv("oci_profile", "DEFAULT"))
compartment_id = "YOUR_OCI_RESOURCE_OCID"
object_storage = oci.object_storage.ObjectStorageClient(config)


namespace = object_storage.get_namespace().data

def bucket_list_mumbai():
    bucket_list_mumbai = []
    bucket_list = object_storage.list_buckets(namespace,compartment_id)
    for b in bucket_list.data:
        bucket_list_mumbai.append(b.name)
    return bucket_list_mumbai

list_of_objects = object_storage.list_objects(
    namespace_name=namespace,
    bucket_name="YOUR_BUCKET_NAME",
    prefix="job-"
)

def delete_obj(obj_name):
     object_storage.delete_object(
     namespace_name=namespace,
     bucket_name="YOUR_BUCKET_NAME",
     object_name=obj_name
     )

     
def get_obj(obj_name):
     obj = object_storage.get_object(
          namespace_name=namespace,
          bucket_name="YOUR_BUCKET_NAME",
          object_name=obj_name
          )
     return obj

def copy_obj(source_object_name):
     object_storage.copy_object(
          namespace_name=namespace,
          bucket_name="YOUR_BUCKET_NAME",
          copy_object_details=oci.object_storage.models.CopyObjectDetails(
               destination_region=config['region'],
               destination_namespace=namespace,
               source_object_name=source_object_name,
               destination_bucket="YOUR_BUCKET_NAME",
               destination_object_name=source_object_name
            )
          
     )


def create_object_mumbai(objectname, os_path):
    with open(os_path, "rb") as in_file:
        obj = object_storage.put_object(
            namespace_name=namespace,
            bucket_name="YOUR_BUCKET_NAME",
            object_name=objectname, 
            put_object_body=in_file
            )
        return obj.headers
    


def replace_text_from_file (file_name):
    search_text = ","
    replace_text = "."
    new_line = "WEBVTT"
    with open(file_name, "r") as file:
        data = file.read()

        data = data.replace(search_text, replace_text)

        new_lines = [new_line + "\n", "\n", "\n"]
        
        
        updated_content = '\n'.join(new_lines) + '\n' + data

    return updated_content



for i in list_of_objects.data.objects:
     
     if "srt" in i.name:
          
          obj = get_obj(i.name)
          
          filename = i.name
          os_path="./srt_temp"
          os_vtt="./vtt_temp"
          open(os_path, 'w').close()
          open(os_vtt, 'w').close()

          with open (os_path, "wb") as f:
               for chunck in get_obj(i.name).data.raw.stream(1024 * 1024, decode_content=False):
                    f.write(chunck)

          new_vtt_file_name = i.name + ".vtt"
          print (new_vtt_file_name)
          data = replace_text_from_file(os_path)

          with open (os_vtt, "w") as f:
              f.write(data)     
        
          create_object_mumbai(new_vtt_file_name, os_vtt)
    




