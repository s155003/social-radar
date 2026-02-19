import requests
import re
import json
import hashlib
from datetime import datetime
from .base import BaseScraper
from ..core.data import TrendItem

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "X-IG-App-ID": "936619743392459",
    "X-Requested-With": "XMLHttpRequest",
}

EXPLORE_URL  = "https://www.instagram.com/api/v1/discover/web/explore_grid/?include_fixed_destinations=true&surface=webShareSheet"
HASHTAG_URL  = "https://www.instagram.com/api/v1/tags/web_info/?tag_name={tag}"
TRENDING_URL = "https://www.instagram.com/explore/tags/{tag}/?__a=1&__d=dis"


class InstagramScraper(BaseScraper):
    @property
    def source_name(self) -> str:
        return "instagram"

    def fetch(self) -> list:
        items = []
        items.extend(self._fetch_explore())
        items.extend(self._fetch_hashtags())
        seen  = set()
        unique = []
        for item in items:
            if item.id not in seen:
                seen.add(item.id)
                unique.append(item)
        return unique[:self.max_items]

    def _fetch_explore(self) -> list:
        try:
            session = requests.Session()
            session.headers.update(HEADERS)
            resp = session.get("https://www.instagram.com/", timeout=10)
            csrf = re.search(r'"csrf_token":"([^"]+)"', resp.text)
            if csrf:
                session.headers["X-CSRFToken"] = csrf.group(1)

            resp  = session.get(EXPLORE_URL, timeout=15)
            if resp.status_code != 200:
                return self._fetch_hashtag_public("trending")

            data    = resp.json()
            medias  = data.get("sectional_items", [])
            items   = []
            for section in medias:
                for media in section.get("layout_content", {}).get("medias", []):
                    item = self._parse_media(media.get("media", {}))
                    if item:
                        items.append(item)
            return items
        except Exception:
            return self._fetch_hashtag_public("trending")

    def _fetch_hashtags(self) -> list:
        items = []
        sources  = self.settings.get("sources", [])
        tag_sources = [s for s in sources if s.get("type") == "hashtag"]
        tags = []
        for src in tag_sources:
            tags.extend(src.get("tags", []))

        for tag in tags[:5]:
            try:
                new_items = self._fetch_hashtag_public(tag)
                items.extend(new_items)
            except Exception:
                continue
        return items

    def _fetch_hashtag_public(self, tag: str) -> list:
        try:
            url  = f"https://www.instagram.com/explore/tags/{tag}/?__a=1&__d=dis"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                data  = resp.json()
                edges = data.get("graphql", {}).get("hashtag", {}).get("edge_hashtag_to_media", {}).get("edges", [])
                items = []
                for edge in edges[:10]:
                    node = edge.get("node", {})
                    item = self._parse_node(node, category=tag)
                    if item:
                        items.append(item)
                return items
        except Exception:
            pass
        return []

    def _parse_media(self, media: dict) -> TrendItem:
        try:
            caption = ""
            cap_edges = media.get("caption", {})
            if isinstance(cap_edges, dict):
                caption = cap_edges.get("text", "")
            elif isinstance(cap_edges, str):
                caption = cap_edges

            if not caption:
                return None

            tags    = re.findall(r"#(\w+)", caption)
            user    = media.get("user", {})
            pk      = str(media.get("pk", hashlib.md5(caption.encode()).hexdigest()[:12]))

            return TrendItem(
                id=self._make_id(pk),
                source="instagram",
                title=caption[:120].split("\n")[0],
                description=caption[:300],
                url=f"https://www.instagram.com/p/{media.get('code', '')}",
                thumbnail=media.get("image_versions2", {}).get("candidates", [{}])[0].get("url", "") if media.get("image_versions2") else "",
                author=f"@{user.get('username', 'unknown')}",
                hashtags=tags,
                likes=media.get("like_count", 0),
                comments=media.get("comment_count", 0),
                views=media.get("view_count", media.get("like_count", 0) * 8),
                category="explore",
                language="en",
            )
        except Exception:
            return None

    def _parse_node(self, node: dict, category: str = "trending") -> TrendItem:
        try:
            caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
            caption = caption_edges[0].get("node", {}).get("text", "") if caption_edges else ""
            if not caption:
                return None
            tags = re.findall(r"#(\w+)", caption)
            return TrendItem(
                id=self._make_id(node.get("id", caption[:20])),
                source="instagram",
                title=caption[:120].split("\n")[0],
                description=caption[:300],
                url=f"https://www.instagram.com/p/{node.get('shortcode', '')}",
                thumbnail=node.get("thumbnail_src", node.get("display_url", "")),
                hashtags=tags,
                likes=node.get("edge_liked_by", {}).get("count", 0),
                comments=node.get("edge_media_to_comment", {}).get("count", 0),
                views=node.get("video_view_count", node.get("edge_liked_by", {}).get("count", 0) * 8),
                category=category,
                language="en",
            )
        except Exception:
            return None

    def _generate_mock(self) -> list:
        mock_data = [
            {"title": "The aesthetic apartment tour everyone is reposting right now ✨", "likes": 892000, "comments": 12000, "views": 7100000, "tags": ["aesthetic", "apartment", "homedecor"], "cat": "lifestyle"},
            {"title": "New restaurant just opened and the food looks absolutely insane 🔥", "likes": 445000, "comments": 8900,  "views": 3600000, "tags": ["food", "restaurant", "foodie"], "cat": "food"},
            {"title": "Fitness transformation that has the whole internet inspired 💪", "likes": 1200000,"comments": 23000, "views": 9800000, "tags": ["fitness", "transformation", "gym"], "cat": "fitness"},
            {"title": "This travel destination just went viral and now everyone wants to go", "likes": 678000, "comments": 15000, "views": 5400000, "tags": ["travel", "viral", "wanderlust"], "cat": "travel"},
            {"title": "Celebrity couple spotted together and the internet is losing its mind", "likes": 2300000,"comments": 67000, "views": 18700000,"tags": ["celebrity", "trending", "entertainment"], "cat": "entertainment"},
            {"title": "Skincare routine that actually works according to dermatologists", "likes": 567000, "comments": 9800,  "views": 4500000, "tags": ["skincare", "beauty", "wellness"], "cat": "beauty"},
        ]
        items = []
        for i, d in enumerate(mock_data):
            items.append(TrendItem(
                id=self._make_id(i),
                source="instagram",
                title=d["title"],
                description=d["title"],
                url="https://www.instagram.com/explore",
                author=f"@influencer{i+1}",
                hashtags=d["tags"],
                likes=d["likes"],
                comments=d["comments"],
                views=d["views"],
                category=d["cat"],
                language="en",
            ))
        return items
