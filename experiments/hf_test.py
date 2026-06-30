from huggingface_hub import batch_bucket_files
import time

BUCKET = "hinabarun/testproject"


print("Uploading...")
start_time=time.perf_counter()

batch_bucket_files(
    BUCKET,
    add=[
        (
            "hello-secondbrain.txt",
            "secondbrain-folder/hello-secondbrain.txt"
        )
    ]
)

time_taken=time.perf_counter()-start_time
print(f"Upload successful in {time_taken:.4f} sec")