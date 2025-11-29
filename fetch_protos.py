import os
import json
import urllib.request

BASE_API_URL = "https://api.github.com/repos/ClassIsland/ClassIsland/contents/ClassIsland.Shared/Protobuf"
TARGET_DIR = "cims/Protobuf"
SUBDIRS = ["Enum", "Service", "Server", "Client", "Command", "AuditEvent"]


def get_files_in_dir(subdir):
    url = f"{BASE_API_URL}/{subdir}"
    print(f"Fetching file list from {url}...")
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            return [item for item in data if item["name"].endswith(".proto")]
    except Exception as e:
        print(f"Error fetching {subdir}: {e}")
        return []


def download_file(file_info, subdir):
    download_url = file_info["download_url"]
    filename = file_info["name"]
    target_path = os.path.join(TARGET_DIR, subdir, filename)

    print(f"Downloading {filename} to {target_path}...")
    try:
        with urllib.request.urlopen(download_url) as response:
            content = response.read()
            with open(target_path, "wb") as f:
                f.write(content)
    except Exception as e:
        print(f"Error downloading {filename}: {e}")


def main():
    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR)

    for subdir in SUBDIRS:
        subdir_path = os.path.join(TARGET_DIR, subdir)
        if not os.path.exists(subdir_path):
            os.makedirs(subdir_path)

        files = get_files_in_dir(subdir)
        for file_info in files:
            download_file(file_info, subdir)


if __name__ == "__main__":
    main()
