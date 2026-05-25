import plistlib
from pathlib import Path

path = Path.home() / "Library/Safari/Bookmarks.plist"

with open(path, "rb") as f:
    data = plistlib.load(f)

def walk(node, depth=0):
    if not isinstance(node, dict):
        return
    btype = node.get("WebBookmarkType", "")
    if btype == "WebBookmarkTypeList":
        title = node.get("Title", "（タイトルなし）")
        count = len([c for c in node.get("Children", []) if isinstance(c, dict) and c.get("WebBookmarkType") == "WebBookmarkTypeLeaf"])
        print("  " * depth + f"📁 {title}  ({count}件)")
        for child in node.get("Children", []):
            walk(child, depth + 1)

walk(data)
