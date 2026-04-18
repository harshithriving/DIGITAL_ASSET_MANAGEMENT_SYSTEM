import os
from dotenv import load_dotenv
from imagekitio import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions

load_dotenv()

private_key = os.getenv('IMAGEKIT_PRIVATE_KEY')
public_key = os.getenv('IMAGEKIT_PUBLIC_KEY')
url_endpoint = os.getenv('IMAGEKIT_URL_ENDPOINT')

print("Private key exists:", bool(private_key))
print("Public key exists:", bool(public_key))
print("URL endpoint:", url_endpoint)

if not all([private_key, public_key, url_endpoint]):
    print("Missing credentials!")
    exit(1)

imagekit = ImageKit(
    private_key=private_key,
    public_key=public_key,
    url_endpoint=url_endpoint
)

# Create a small test file
with open("test.txt", "w") as f:
    f.write("Hello ImageKit")

try:
    with open("test.txt", "rb") as f:
        options = UploadFileRequestOptions(
            use_unique_file_name=True,
            folder="dam_system_test"
        )
        response = imagekit.upload_file(
            file=f,
            file_name="test.txt",
            options=options
        )
        print("Upload successful!")
        print("File ID:", response.file_id)
        print("URL:", response.url)
except Exception as e:
    print("Upload failed:", str(e))