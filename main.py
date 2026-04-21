import os
import random
import sys
from dotenv import load_dotenv
from generate_article import generate_article, TOPICS
from post_to_wp import post_article

load_dotenv()


def run(topic: str = None, status: str = "draft"):
    if not topic:
        topic = random.choice(TOPICS)

    print(f"記事生成中: {topic}")
    article = generate_article(topic)
    print(f"タイトル: {article['title']}")

    result = post_article(article, status=status)
    print(f"投稿完了: {result['link']}")
    return result


if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else None
    status = sys.argv[2] if len(sys.argv) > 2 else "publish"
    run(topic=topic, status=status)
