from importlib.metadata import files
import json
import os
import oci
import re
from Transform_SRT import run_object


config = oci.config.from_file(profile_name=os.getenv("oci_profile", "DEFAULT"))
compartment_id = "YOUR_OCI_RESOURCE_OCID"
object_storage = oci.object_storage.ObjectStorageClient(config)


namespace = object_storage.get_namespace().data

def bucket_list_oci():
    bucket_list_oci = []
    bucket_list = object_storage.list_buckets(namespace,compartment_id)
    for b in bucket_list.data:
        bucket_list_oci.append(b.name)
    print (bucket_list_oci)
    return bucket_list_oci

def list_of_objects(name, pre_fix):
    list_of_objects = object_storage.list_objects(
    namespace_name=namespace,
    bucket_name=name,
    prefix=pre_fix
    )
    return list_of_objects.data.objects


def delete_obj(obj_name, bucketname):
    
    
    
    
    
    try:
        object_storage.delete_object(
            namespace_name=namespace,
            bucket_name=bucketname,
            object_name=obj_name
        )
        print(f"Object {obj_name} deleted successfully")
    except oci.exceptions.ServiceError as e:
        print(f"Error deleting object: {e}")

     
def get_obj(obj_name, bucketname):
     obj = object_storage.get_object(
          namespace_name=namespace,
          bucket_name=bucketname,
          object_name=obj_name
          )
     return obj.data.content.decode('utf-8')

def copy_obj(source_object_name, bucketname):
     object_storage.copy_object(
          namespace_name=namespace,
          bucket_name=bucketname,
          copy_object_details=oci.object_storage.models.CopyObjectDetails(
               destination_region=config['region'],
               destination_namespace=namespace,
               source_object_name=source_object_name,
               destination_bucket=bucketname,
               destination_object_name=source_object_name
            )
          
     )


def create_object_mumbai(bucketname, objectname, os_path):
    with open(os_path, "rb") as in_file:
        obj = object_storage.put_object(
            namespace_name=namespace,
            bucket_name=bucketname,
            object_name=objectname, 
            put_object_body=in_file
            )
        return obj.headers

def create_object_oci(bucketname, objectname, content):
    in_file = content.encode('utf-8')
    obj = object_storage.put_object(
        namespace_name=namespace,
        bucket_name=bucketname,
        object_name=objectname, 
        put_object_body=in_file
        )
    print (obj.headers)
    return obj.headers
    


def replace_text_from_object (srt_lines: list[str]) -> list[str]:

    webvtt_lines = ["WEBVTT", "", "", ""]  

        
    timestamp_pattern = re.compile(
        r'(\d{2}:\d{2}:\d{2}),(\d{3})\s-->\s(\d{2}:\d{2}:\d{2}),(\d{3})'
    )

    for line in srt_lines:
        
        match = timestamp_pattern.search(line)
        if match:
            
            line = timestamp_pattern.sub(
                r'\1.\2 --> \3.\4' + ' line:80%', line 
            )
        webvtt_lines.append(line)


    updated_content = "\n".join(webvtt_lines)
    

    return updated_content





bucketname = "YOUR_BUCKET_NAME"
bucket_list_oci()
obj_names = list_of_objects(bucketname,"")

srt_file = []
for i in obj_names:    
    if i.name.endswith('.srt'):
        srt_file.append(i.name)

for i in obj_names:    
    if i.name.endswith('.vtt_new'):
        
        
        print (i.name)
        delete_obj(bucketname=bucketname, obj_name=i.name)

for i in srt_file:
    
    print (i)
    srt_data = get_obj(i, bucketname)
    new_srt = run_object(srt_data, 120)
    
    new_vtt = replace_text_from_object (new_srt)
    new_obj_name = i + ".vtt_new"
    
    

    create_object_oci(bucketname=bucketname, objectname=new_obj_name, content=new_vtt)
    
    print (new_vtt)
    
print ("###########################")
