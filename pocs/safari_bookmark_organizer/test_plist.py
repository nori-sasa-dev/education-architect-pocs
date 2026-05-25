import plistlib
from pathlib import Path

path = Path.home() / "Library/Safari/Bookmarks.plist"
print("exists:", path.exists())

try:
    with open(path, "rb") as f:
        data = plistlib.load(f)
    print("readable: OK")
except Exception as e:
    print("ERROR:", e)
