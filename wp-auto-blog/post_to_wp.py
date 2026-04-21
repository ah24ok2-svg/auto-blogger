import requests
import base64
import os
from pathlib import Path
from dotenv import dotenv_values

_env = {**dotenv_values(Path(__file__).parent / ".env"), **os.environ}

WP_URL = _env["WP_URL"]
WP_USERNAME = _env["WP_USERNAME"]
WP_PASSWORD = _env["WP_PASSWORD"]
UNSPLASH_ACCESS_KEY = _env.get("UNSPLASH_ACCESS_KEY", "")


def get_auth_header():
    credentials = f"{WP_USERNAME}:{WP_PASSWORD}"
    token = base64.b64encode(credentials.encode()).decode("utf-8")
    return {"Authorization": f"Basic {token}"}


def get_or_create_tags(tag_names: list[str]) -> list[int]:
    headers = get_auth_header()
    tag_ids = []

    for name in tag_names:
        res = requests.get(
            f"{WP_URL}/wp-json/wp/v2/tags",
            params={"search": name},
            headers=headers
        )
        tags = res.json()
        existing = [t for t in tags if t["name"] == name]

        if existing:
            tag_ids.append(existing[0]["id"])
        else:
            res = requests.post(
                f"{WP_URL}/wp-json/wp/v2/tags",
                json={"name": name},
                headers=headers
            )
            tag_ids.append(res.json()["id"])

    return tag_ids


def fetch_unsplash_image(keyword: str) -> bytes | None:
    if not UNSPLASH_ACCESS_KEY:
        return None

    res = requests.get(
        "https://api.unsplash.com/search/photos",
        params={"query": keyword, "per_page": 1, "orientation": "landscape"},
        headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
    )
    if res.status_code != 200:
        return None

    results = res.json().get("results", [])
    if not results:
        return None

    image_url = results[0]["urls"]["regular"]
    image_res = requests.get(image_url)
    return image_res.content if image_res.status_code == 200 else None


def upload_featured_image(image_bytes: bytes, filename: str) -> int | None:
    headers = get_auth_header()
    res = requests.post(
        f"{WP_URL}/wp-json/wp/v2/media",
        headers={**headers, "Content-Disposition": f'attachment; filename="{filename}"'},
        files={"file": (filename, image_bytes, "image/jpeg")},
    )
    if res.status_code in (200, 201):
        return res.json()["id"]
    return None


def post_article(article: dict, status: str = "publish") -> dict:
    headers = {**get_auth_header(), "Content-Type": "application/json"}

    tag_ids = get_or_create_tags(article.get("tags", []))
    description = article.get("description", article.get("excerpt", ""))

    # アイキャッチ画像を取得・アップロード（英語キーワードで検索）
    featured_media = None
    keyword = article.get("image_keyword", "AI technology business")
    print(f"  アイキャッチ取得中: {keyword}")
    image_bytes = fetch_unsplash_image(keyword)
    if image_bytes:
        featured_media = upload_featured_image(image_bytes, f"{keyword}.jpg")
        print(f"  アイキャッチアップロード完了: media_id={featured_media}")
    else:
        print("  アイキャッチ取得スキップ（APIキー未設定または取得失敗）")

    payload = {
        "title": article["title"],
        "content": article["content"],
        "excerpt": article.get("excerpt", ""),
        "status": status,
        "tags": tag_ids,
        "meta": {
            "_yoast_wpseo_metadesc": description,
            "rank_math_description": description,
        },
    }
    if featured_media:
        payload["featured_media"] = featured_media

    res = requests.post(
        f"{WP_URL}/wp-json/wp/v2/posts",
        json=payload,
        headers=headers,
    )
    res.raise_for_status()
    return res.json()


if __name__ == "__main__":
    headers = get_auth_header()
    res = requests.get(f"{WP_URL}/wp-json/wp/v2/posts", headers=headers)
    if res.status_code == 200:
        print("WordPress接続OK")
    else:
        print(f"接続エラー: {res.status_code} {res.text}")
