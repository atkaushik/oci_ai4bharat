import oci
import logging

import os
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
           

logger = logging.getLogger()

logger.setLevel(logging.DEBUG)

config = oci.config.from_file()
compartment_id = "YOUR_OCI_RESOURCE_OCID"
object_storage = oci.object_storage.ObjectStorageClient(config)


namespace = object_storage.get_namespace().data

def bucket_list_mumbai():
    bucket_list_mumbai = []
    bucket_list = object_storage.list_buckets(namespace,compartment_id)
    for b in bucket_list.data:
        bucket_list_mumbai.append(b.name)
    return bucket_list_mumbai

def create_bucket_mumbai(name):
    create_bucket_mumbai_resp = object_storage.create_bucket(
        namespace,
        create_bucket_details=oci.object_storage.models.CreateBucketDetails(
            name=name,
            compartment_id=compartment_id,
            storage_tier="Standard",
            public_access_type="NoPublicAccess"
        )

    )
    return create_bucket_mumbai_resp.data.name + " bucket created"



def delete_bucket_mumbai(name):
    delete_bucket_mumbai_resp = object_storage.delete_bucket (
        namespace_name=namespace,
        bucket_name=name
    )
    return delete_bucket_mumbai_resp.headers


def create_object_mumbai(bucketname, objectname, os_path):
    with open(os_path, "rb") as in_file:
        obj = object_storage.put_object(
            namespace_name=namespace,
            bucket_name=bucketname,
            object_name=objectname, 
            put_object_body=in_file
            )
        return obj.headers

def delete_object_mumbai(bucketname, objectname):
    delete_object_mumbai_resp = object_storage.delete_object(
        namespace_name=namespace,
        bucket_name=bucketname,
        object_name=objectname
    )
    return delete_object_mumbai_resp.headers

def create_object_hyd(bucketname, objectname, os_path):
    with open(os_path, "rb") as in_file:
        obj = object_storage.put_object(
            namespace_name=namespace,
            bucket_name=bucketname,
            object_name=objectname, 
            put_object_body=in_file
            )
        return obj.headers

if __name__ == "__main__":







    print (bucket_list_mumbai())








