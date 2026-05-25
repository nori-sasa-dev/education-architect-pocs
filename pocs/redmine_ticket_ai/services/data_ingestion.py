import csv
import io
from pathlib import Path
from database.db import upsert_tickets, log_import, get_ticket_count, DB_PATH, CHROMA_PATH
from database.db import init_db


REQUIRED_COLUMNS = {
    "id", "ticket_type", "feature", "title",
    "description", "root_cause", "resolution",
    "review_comment", "status", "created_at",
}


class DataIngestionService:
    def __init__(self):
        init_db()
        self._chroma_client = None
        self._collection = None

    def _get_chroma(self):
        """ChromaDBクライアントを遅延初期化する"""
        if self._chroma_client is None:
            import chromadb
            self._chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
            self._collection = self._chroma_client.get_or_create_collection(
                name="tickets",
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def _embed_text(self, ticket: dict) -> str:
        """ベクトル化するテキストを組み立てる"""
        parts = [
            ticket.get("title", ""),
            ticket.get("description", ""),
            ticket.get("root_cause", ""),
            ticket.get("resolution", ""),
            ticket.get("review_comment", ""),
        ]
        return " ".join(p for p in parts if p)

    def ingest_csv(self, csv_content: str, filename: str = "upload.csv") -> dict:
        """CSVテキストを受け取り、SQLite + ChromaDBに保存する。結果サマリーを返す。"""
        reader = csv.DictReader(io.StringIO(csv_content))

        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            return {"success": False, "error": f"必須カラムが不足しています: {missing}"}

        rows = []
        for row in reader:
            try:
                row["id"] = int(row["id"])
            except (ValueError, KeyError):
                continue
            rows.append(row)

        if not rows:
            return {"success": False, "error": "有効な行が見つかりませんでした"}

        upsert_tickets(rows)
        log_import(filename, len(rows))

        try:
            from services.embedder import encode_batch
            collection = self._get_chroma()
            texts = [self._embed_text(r) for r in rows]
            embeddings = encode_batch(texts)
            ids = [str(r["id"]) for r in rows]
            metadatas = [
                {
                    "ticket_type": r.get("ticket_type", ""),
                    "feature": r.get("feature", ""),
                    "title": r.get("title", ""),
                    "status": r.get("status", ""),
                }
                for r in rows
            ]
            collection.upsert(documents=texts, embeddings=embeddings, ids=ids, metadatas=metadatas)
            vector_ok = True
        except Exception as e:
            vector_ok = False

        return {
            "success": True,
            "row_count": len(rows),
            "total_count": get_ticket_count(),
            "vector_indexed": vector_ok,
        }

    def ingest_sample(self) -> dict:
        """同梱のサンプルCSVを読み込む"""
        sample_path = Path(__file__).parent.parent / "data" / "sample" / "tickets.csv"
        if not sample_path.exists():
            return {"success": False, "error": "サンプルファイルが見つかりません"}
        content = sample_path.read_text(encoding="utf-8")
        return self.ingest_csv(content, filename="sample/tickets.csv")
