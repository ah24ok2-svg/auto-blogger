import anthropic
import json
import os
from pathlib import Path
from dotenv import dotenv_values

_env = {**dotenv_values(Path(__file__).parent / ".env"), **os.environ}

client = anthropic.Anthropic(api_key=_env["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = """あなたはAI副業・バイブコーディング専門のブログライターです。

## 重要：現在は2026年です
- 年号を書く場合は必ず「2026年」を使う
- 「最新」と書く場合は2026年時点の情報を指す
- 2024年・2025年の情報を「最新」と表現しない

## 記事作成の手順
1. まずweb_searchツールでテーマに関する最新情報を2〜3回検索する
2. 検索結果をもとに記事を執筆する
3. 検索で得た具体的な情報・数字・事例を記事に盛り込む

## 記事のスタイル
- 読者は20〜40代の副業に興味があるサラリーマン
- 親しみやすく、でも信頼感のある口調
- 専門用語はわかりやすく噛み砕く
- 実践的なTipsや具体例を必ず入れる
- 冒頭で「この記事を読むとこんなことがわかる」を示す

## リンクの必須ルール
- リサーチで参照したデータ・統計・調査結果には必ず出典リンクを入れる（例：<a href="URL" target="_blank">〇〇調査より</a>）
- 初心者がつまづきそうな専門用語（例：API、LLM、プロンプトエンジニアリング等）には初めて登場する箇所に解説リンクを入れる（わかりやすい解説ページへ）
- リンクは必ずHTMLの<a>タグで記述し、target="_blank"をつけること

## 記事構成
- タイトル（SEOを意識したH1）
- リード文（200字程度）
- 目次相当の見出し（H2を3〜5個）
- 各セクション（H2ごとに300〜500字）
- まとめ
- 全体で1500〜2000字程度

## 最終出力形式
リサーチが終わったら、必ずJSON形式で返してください：
{
  "title": "記事タイトル",
  "content": "HTML形式の本文（h2, h3, p, ul, liタグ使用）",
  "excerpt": "記事の要約（120字以内）",
  "description": "SEOメタディスクリプション（120〜155字、検索結果に表示される文章。読者がクリックしたくなる内容）",
  "image_keyword": "アイキャッチ画像検索用の英語キーワード（1〜3単語。例: AI technology, side business, coding laptop）",
  "tags": ["タグ1", "タグ2", "タグ3"]
}
"""

TOPICS = [
    "バイブコーディングで副業月5万円を稼ぐ具体的な方法",
    "Claude vs ChatGPT、副業で使うならどっち？徹底比較",
    "AIツールを使ったメルカリ転売の効率化テクニック",
    "プログラミング未経験でもできるAI副業5選",
    "Gemini 2.5を使った副業アイデア10選",
    "AIライティングツールで月10万円稼ぐ人の共通点",
    "看護師・教師・経理職がAIで副業を始める方法",
    "無料AIツールだけで副業を始める完全ガイド",
    "バイブコーディングでWebアプリを作って売る方法",
    "AI画像生成で副業する最新トレンド2026年版",
]


def generate_article(topic: str) -> dict:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8096,
        system=SYSTEM_PROMPT,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": f"以下のテーマで記事を書いてください：\n\n{topic}"}],
    )

    # テキストブロックを結合してJSONを抽出
    text = "".join(b.text for b in response.content if hasattr(b, "text"))

    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    else:
        # コードブロックなしの場合、{から始まる部分を抽出
        start = text.find("{")
        end = text.rfind("}") + 1
        text = text[start:end]

    # strict=Falseで制御文字を許容して解析
    return json.loads(text, strict=False)


if __name__ == "__main__":
    import sys
    topic = sys.argv[1] if len(sys.argv) > 1 else TOPICS[0]
    article = generate_article(topic)
    print(json.dumps(article, ensure_ascii=False, indent=2))
