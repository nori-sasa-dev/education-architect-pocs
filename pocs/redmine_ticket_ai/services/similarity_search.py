import anthropic
from database.db import CHROMA_PATH, get_tickets_by_ids
from services.embedder import encode

_chroma_client = None
_collection = None


def _get_collection():
    global _chroma_client, _collection
    if _chroma_client is None:
        import chromadb
        _chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        _collection = _chroma_client.get_or_create_collection(
            name="tickets",
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


class SimilaritySearchService:
    def search(
        self,
        query: str,
        top_k: int = 5,
        ticket_type: str | None = None,
        feature: str | None = None,
    ) -> list[dict]:
        """クエリに類似するチケットをスコア付きで返す"""
        collection = _get_collection()
        query_vec = encode(query)

        where = {}
        if ticket_type and ticket_type != "すべて":
            where["ticket_type"] = {"$eq": ticket_type}
        if feature and feature != "すべて":
            where["feature"] = {"$eq": feature}

        query_kwargs = dict(
            query_embeddings=[query_vec],
            n_results=min(top_k, collection.count()),
            include=["metadatas", "distances"],
        )
        if where:
            query_kwargs["where"] = where

        results = collection.query(**query_kwargs)

        ids = [int(i) for i in results["ids"][0]]
        distances = results["distances"][0]

        tickets = get_tickets_by_ids(ids)

        # コサイン距離 → 類似スコア（0〜100%）に変換
        dist_map = {int(i): d for i, d in zip(results["ids"][0], distances)}
        for t in tickets:
            dist = dist_map.get(t["id"], 1.0)
            t["similarity"] = round((1 - dist) * 100, 1)

        tickets.sort(key=lambda t: t["similarity"], reverse=True)
        return tickets

    def suggest_solution(
        self,
        query: str,
        similar_tickets: list[dict],
        api_key: str,
    ) -> str:
        """類似チケットをもとにClaude APIで解決策を提案する"""
        context_lines = []
        for t in similar_tickets[:3]:
            context_lines.append(
                f"【{t['ticket_type']}】{t['title']}\n"
                f"  真の原因: {t.get('root_cause', 'なし')}\n"
                f"  解決策: {t.get('resolution', 'なし')}"
            )
        context = "\n\n".join(context_lines)

        prompt = (
            f"以下は過去の類似チケットの情報です。\n\n{context}\n\n"
            f"---\n"
            f"新しい事象: {query}\n\n"
            "上記の過去事例を参考に、新しい事象の考えられる原因と解決策を簡潔に提案してください。"
            "箇条書きで3点以内にまとめてください。"
        )

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
