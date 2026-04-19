"""
Safari ブックマーク整理エージェント
Claude Computer Use（bash tool）でブックマークを分類・整理する
"""

import os
import plistlib
import json
import anthropic
from pathlib import Path


BOOKMARKS_PATH = Path.home() / "Library/Safari/Bookmarks.plist"

DEMO_BOOKMARKS = [
    {"title": "Anthropic", "url": "https://anthropic.com", "folder": "お気に入りバー"},
    {"title": "GitHub", "url": "https://github.com", "folder": "お気に入りバー"},
    {"title": "Qiita", "url": "https://qiita.com", "folder": "お気に入りバー"},
    {"title": "Udemy", "url": "https://udemy.com", "folder": "学習"},
    {"title": "中小企業診断士 試験情報", "url": "https://www.j-smeca.jp", "folder": "資格"},
    {"title": "Python公式ドキュメント", "url": "https://docs.python.org/ja", "folder": "技術"},
    {"title": "Streamlit Docs", "url": "https://docs.streamlit.io", "folder": "技術"},
    {"title": "NHKニュース", "url": "https://www.nhk.or.jp/news", "folder": "ニュース"},
    {"title": "日経電子版", "url": "https://www.nikkei.com", "folder": "ニュース"},
    {"title": "Amazon", "url": "https://amazon.co.jp", "folder": "ショッピング"},
]


def load_bookmarks_from_plist(target_folder: str | None = None) -> list[dict]:
    """Safariの Bookmarks.plist を読み込んでブックマーク一覧を返す。
    target_folder 指定時はそのフォルダ内のみ返す。
    """
    with open(BOOKMARKS_PATH, "rb") as f:
        data = plistlib.load(f)

    def extract(node, folder="ルート", inside_target: bool = False):
        items = []
        if not isinstance(node, dict):
            return items
        btype = node.get("WebBookmarkType", "")
        if btype == "WebBookmarkTypeLeaf":
            if target_folder is None or inside_target:
                title = node.get("URIDictionary", {}).get("title", "(タイトルなし)")
                url = node.get("URLString", "")
                if url:
                    items.append({"title": title, "url": url, "folder": folder})
        elif btype == "WebBookmarkTypeList":
            fname = node.get("Title", folder)
            # このフォルダがターゲットか、すでにターゲット内にいるか
            now_inside = inside_target or (target_folder is not None and fname == target_folder)
            for child in node.get("Children", []):
                items.extend(extract(child, fname, now_inside))
        return items

    return extract(data)


def get_folder_names_from_plist() -> list[str]:
    """Bookmarks.plist 内のフォルダ名一覧を返す"""
    with open(BOOKMARKS_PATH, "rb") as f:
        data = plistlib.load(f)

    folders = []

    def walk(node):
        if not isinstance(node, dict):
            return
        if node.get("WebBookmarkType") == "WebBookmarkTypeList":
            title = node.get("Title", "")
            if title:
                folders.append(title)
            for child in node.get("Children", []):
                walk(child)

    walk(data)
    return folders


class BookmarkOrganizer:
    """Claude APIを使ってブックマークをカテゴリ分類するエージェント"""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.is_demo_mode = not bool(self.api_key)
        self.client = anthropic.Anthropic(api_key=self.api_key) if not self.is_demo_mode else None

    def load_bookmarks(self, target_folder: str | None = None) -> list[dict]:
        """お気に入りを読み込む（APIキーの有無に関係なく実行）。
        読み込み失敗時のみデモデータにフォールバックする。
        """
        try:
            return load_bookmarks_from_plist(target_folder)
        except PermissionError:
            raise PermissionError(
                "Safariお気に入りへのアクセスが拒否されました。\n"
                "システム設定 → プライバシーとセキュリティ → フルディスクアクセス で "
                "Terminalを追加してください。"
            )
        except FileNotFoundError:
            # plistが存在しない環境（デモ用）
            return DEMO_BOOKMARKS

    def get_folder_names(self) -> tuple[list[str], str | None]:
        """フォルダ名一覧を返す。戻り値: (folders, error_message)"""
        try:
            return get_folder_names_from_plist(), None
        except Exception as e:
            return [], str(e)

    def categorize(self, bookmarks: list[dict], extra_instruction: str = "") -> dict:
        """
        Claude APIでブックマークをカテゴリ分類する
        Returns: {"カテゴリ名": [{"title":..., "url":...}, ...], ...}
        """
        if self.is_demo_mode:
            return self._demo_categorize(bookmarks)

        # ブックマーク一覧をテキスト化
        bm_text = "\n".join(
            f"{i+1}. {b['title']} | {b['url']}"
            for i, b in enumerate(bookmarks)
        )

        prompt = f"""以下のSafariブックマーク一覧を、内容に基づいて分かりやすいカテゴリに分類してください。

## ブックマーク一覧
{bm_text}

## 指示
- カテゴリ数は5〜12個程度（多すぎず少なすぎず）
- カテゴリ名は日本語で、具体的かつ簡潔に
- 1つのブックマークは必ず1つのカテゴリに入れる
- URLだけでなくタイトルも参考にして判断する
{extra_instruction}

## 出力形式
以下のJSON形式で返してください（他の文章は不要）：
```json
{{
  "カテゴリ名1": [
    {{"title": "タイトル", "url": "URL"}},
    ...
  ],
  "カテゴリ名2": [...]
}}
```
"""

        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}]
        )

        text = response.content[0].text

        # ```json ブロックを優先、なければ { } で囲まれた部分を探す
        start = text.find("```json")
        if start != -1:
            end = text.find("```", start + 7)
            json_str = text[start + 7:end].strip() if end != -1 else text[start + 7:].strip()
        else:
            start = text.find("{")
            end = text.rfind("}") + 1
            json_str = text[start:end].strip() if start != -1 else text.strip()

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON解析失敗（stop_reason: {response.stop_reason}）\n応答の末尾: ...{text[-200:]}\n元エラー: {e}")

    def _demo_categorize(self, bookmarks: list[dict]) -> dict:
        """デモ用の固定分類結果"""
        return {
            "AI・技術": [
                {"title": "Anthropic", "url": "https://anthropic.com"},
                {"title": "GitHub", "url": "https://github.com"},
                {"title": "Qiita", "url": "https://qiita.com"},
                {"title": "Python公式ドキュメント", "url": "https://docs.python.org/ja"},
                {"title": "Streamlit Docs", "url": "https://docs.streamlit.io"},
            ],
            "学習・資格": [
                {"title": "Udemy", "url": "https://udemy.com"},
                {"title": "中小企業診断士 試験情報", "url": "https://www.j-smeca.jp"},
            ],
            "ニュース": [
                {"title": "NHKニュース", "url": "https://www.nhk.or.jp/news"},
                {"title": "日経電子版", "url": "https://www.nikkei.com"},
            ],
            "ショッピング": [
                {"title": "Amazon", "url": "https://amazon.co.jp"},
            ],
        }

    def export_html(self, categorized: dict, output_path: str) -> str:
        """整理済みブックマークをHTMLで書き出す"""
        lines = [
            "<!DOCTYPE NETSCAPE-Bookmark-file-1>",
            "<META HTTP-EQUIV='Content-Type' CONTENT='text/html; charset=UTF-8'>",
            "<TITLE>Bookmarks</TITLE>",
            "<H1>整理済みブックマーク</H1>",
            "<DL><p>",
        ]
        for category, items in categorized.items():
            lines.append(f"  <DT><H3>{category}</H3>")
            lines.append("  <DL><p>")
            for item in items:
                lines.append(f'    <DT><A HREF="{item["url"]}">{item["title"]}</A>')
            lines.append("  </DL><p>")
        lines.append("</DL><p>")

        html = "\n".join(lines)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        return output_path
