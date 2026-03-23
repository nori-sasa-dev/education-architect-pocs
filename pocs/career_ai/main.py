import os
import sys
from orchestrator import Orchestrator

DIVIDER = "=" * 52


def check_api_key() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[エラー] 環境変数 ANTHROPIC_API_KEY が設定されていません。")
        print("  export ANTHROPIC_API_KEY='your-api-key'")
        sys.exit(1)


def main() -> None:
    check_api_key()

    print(DIVIDER)
    print("    キャリアチェンジ支援 AI  (プロトタイプ v0.1)")
    print(DIVIDER)
    print("  終了: 'quit' または 'exit'")
    print(DIVIDER + "\n")

    orchestrator = Orchestrator()

    # セッション開始（Interview Agentが最初の質問を生成）
    opening = orchestrator.start()
    print(f"AI: {opening}\n")

    while True:
        try:
            user_input = input("あなた: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nご利用ありがとうございました。")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "終了"):
            print("\nご利用ありがとうございました。")
            break

        response, is_complete = orchestrator.process(user_input)
        print(f"\nAI: {response}\n")

        if is_complete:
            print(DIVIDER)
            print(orchestrator.get_profile_summary())
            print(DIVIDER)
            print("\nインタビュー完了！次のステップ: Analysis Agent でキャリア候補を分析します。")
            break


if __name__ == "__main__":
    main()
