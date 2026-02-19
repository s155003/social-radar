import requests
import re
import json
import hashlib
from datetime import datetime
from .base import BaseScraper
from ..core.data import TrendItem

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.tiktok.com/",
}

TRENDING_HASHTAGS_URL = "https://www.tiktok.com/api/explore/item_list/?aid=1988&count={count}&cursor=0&sourceType=68"
DISCOVER_URL          = "https://www.tiktok.com/api/discover/item_list/?aid=1988&count={count}&type=1"

CATEGORY_HASHTAGS = {
    "entertainment": ["entertainment", "viral", "fyp", "trending", "foryou"],
    "sports":        ["sports", "nba", "nfl", "soccer", "football"],
    "food":          ["food", "recipe", "cooking", "foodtok", "foodie"],
    "technology":    ["tech", "ai", "gadgets", "coding", "startup"],
    "news":          ["news", "breakingnews", "worldnews", "politics", "currentevents"],
}


class TikTokScraper(BaseScraper):
    @property
    def source_name(self) -> str:
        return "tiktok"

    def fetch(self) -> list:
        items = []
        items.extend(self._fetch_trending())
        items.extend(self._fetch_by_hashtags())
        seen  = set()
        unique = []
        for item in items:
            if item.id not in seen:
                seen.add(item.id)
                unique.append(item)
        return unique[:self.max_items]

    def _fetch_trending(self) -> list:
        items = []
        try:
            session = requests.Session()
            session.headers.update(HEADERS)
            session.get("https://www.tiktok.com/", timeout=10)

            url  = TRENDING_HASHTAGS_URL.format(count=self.max_items)
            resp = session.get(url, timeout=15)
            if resp.status_code != 200:
                return self._fetch_fallback()

            data  = resp.json()
            posts = data.get("itemList", [])
            for post in posts:
                item = self._parse_post(post)
                if item:
                    items.append(item)
        except Exception:
            return self._fetch_fallback()
        return items

    def _fetch_by_hashtags(self) -> list:
        items  = []
        categories = self.settings.get("categories", ["trending"])
        for cat in categories[:3]:
            tags = CATEGORY_HASHTAGS.get(cat, [cat])
            for tag in tags[:2]:
                try:
                    url  = f"https://www.tiktok.com/api/search/item/full/?keyword=%23{tag}&count=10&cursor=0&aid=1988"
                    resp = requests.get(url, headers=HEADERS, timeout=10)
                    if resp.status_code == 200:
                        data  = resp.json()
                        posts = data.get("item_list", data.get("itemList", []))
                        for post in posts[:5]:
                            item = self._parse_post(post, category=cat)
                            if item:
                                items.append(item)
                except Exception:
                    continue
        return items

    def _fetch_fallback(self) -> list:
        try:
            resp = requests.get("https://www.tiktok.com/trending", headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                return []
            pattern = r'"desc":"([^"]{10,200})".*?"playCount":(\d+).*?"diggCount":(\d+).*?"commentCount":(\d+)'
            matches = re.findall(pattern, resp.text)
            items   = []
            for i, (desc, plays, likes, comments) in enumerate(matches[:self.max_items]):
                uid = hashlib.md5(desc.encode()).hexdigest()[:12]
                items.append(TrendItem(
                    id=self._make_id(uid),
                    source="tiktok",
                    title=desc,
                    description=desc,
                    url=f"https://www.tiktok.com/trending",
                    views=int(plays),
                    likes=int(likes),
                    comments=int(comments),
                    category="trending",
                    language="en",
                ))
            return items
        except Exception:
            return self._generate_mock()

    def _parse_post(self, post: dict, category: str = "trending") -> TrendItem:
        try:
            video   = post.get("video", {})
            author  = post.get("author", {})
            stats   = post.get("stats", {})
            desc    = post.get("desc", "").strip()
            if not desc:
                return None
            tags = re.findall(r"#(\w+)", desc)
            return TrendItem(
                id=self._make_id(post.get("id", desc[:20])),
                source="tiktok",
                title=desc[:120],
                description=desc,
                url=f"https://www.tiktok.com/@{author.get('uniqueId','')}/video/{post.get('id','')}",
                thumbnail=video.get("cover", ""),
                author=f"@{author.get('uniqueId', 'unknown')}",
                hashtags=tags,
                views=int(stats.get("playCount", 0)),
                likes=int(stats.get("diggCount", 0)),
                comments=int(stats.get("commentCount", 0)),
                shares=int(stats.get("shareCount", 0)),
                category=category,
                language="en",
            )
        except Exception:
            return None

    def _generate_mock(self) -> list:
        mock_data = [
            {"title": "POV: AI is taking over creative jobs and no one is talking about it", "views": 8200000, "likes": 1200000, "comments": 45000, "shares": 89000, "tags": ["ai", "tech", "fyp"], "cat": "technology"},
            {"title": "This cooking hack just changed my life forever (seriously try this)", "views": 5600000, "likes": 780000,  "comments": 23000, "shares": 67000, "tags": ["food", "cooking", "lifehack"], "cat": "food"},
            {"title": "The most insane sports moment you will ever see in your lifetime", "views": 12000000,"likes": 2100000, "comments": 89000, "shares": 210000,"tags": ["sports", "viral", "fyp"], "cat": "sports"},
            {"title": "Why everyone is suddenly moving out of California explained", "views": 4300000, "likes": 560000,  "comments": 67000, "shares": 34000, "tags": ["news", "california", "trending"], "cat": "news"},
            {"title": "This new product just dropped and the internet cannot stop talking about it", "views": 7800000, "likes": 990000,  "comments": 34000, "shares": 78000, "tags": ["viral", "product", "trending"], "cat": "entertainment"},
            {"title": "Breaking: major announcement changes everything we thought we knew", "views": 9100000, "likes": 1400000, "comments": 112000,"shares": 190000,"tags": ["breaking", "news", "fyp"], "cat": "news"},
            {"title": "Trying the viral food trend everyone is obsessed with right now", "views": 3400000, "likes": 430000,  "comments": 18000, "shares": 29000, "tags": ["foodtok", "viral", "trend"], "cat": "food"},
            {"title": "This small business owner's story will restore your faith in humanity", "views": 6700000, "likes": 1100000, "comments": 56000, "shares": 145000,"tags": ["smallbusiness", "heartwarming", "fyp"], "cat": "entertainment"},
        ]
        items = []
        for i, d in enumerate(mock_data):
            items.append(TrendItem(
                id=self._make_id(i),
                source="tiktok",
                title=d["title"],
                description=d["title"],
                url="https://www.tiktok.com/trending",
                author=f"@creator{i+1}",
                hashtags=d["tags"],
                views=d["views"],
                likes=d["likes"],
                comments=d["comments"],
                shares=d["shares"],
                category=d["cat"],
                language="en",
            ))
        return items
