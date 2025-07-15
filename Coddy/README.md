import os

repository_url = "<repository_url>"  # Replace with the actual repository URL

try:
    os.system(f"git clone {repository_url}")
    os.chdir("funny_clock")
    print("Successfully cloned and changed directory.")
except Exception as e:
    print(f"An error occurred: {e}")