from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class TrendItem:
    id:           str
    source:       str
    title:        str
    description:  str           = ""
    url:          str           = ""
    thumbnail:    str           = ""
    author:       str           = ""
    hashtags:     list          = field(default_factory=list)
    views:        int           = 0
    likes:        int           = 0
    comments:     int           = 0
    shares:       int           = 0
    category:     str           = "general"
    region:       str           = "US"
    language:     str           = "en"
    fetched_at:   datetime      = field(default_factory=datetime.now)
    published_at: Optional[datetime] = None
    trend_score:  float         = 0.0
    raw:          dict          = field(default_factory=dict)

    @property
    def engagement(self) -> int:
        return self.views + self.likes + self.comments + self.shares

    def to_dict(self) -> dict:
        return {
            "id":           self.id,
            "source":       self.source,
            "title":        self.title,
            "description":  self.description,
            "url":          self.url,
            "thumbnail":    self.thumbnail,
            "author":       self.author,
            "hashtags":     self.hashtags,
            "views":        self.views,
            "likes":        self.likes,
            "comments":     self.comments,
            "shares":       self.shares,
            "category":     self.category,
            "region":       self.region,
            "language":     self.language,
            "trend_score":  round(self.trend_score, 2),
            "fetched_at":   self.fetched_at.isoformat(),
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "engagement":   self.engagement,
        }


@dataclass
class AggregatedResults:
    fetched_at: datetime = field(default_factory=datetime.now)
    items:      dict     = field(default_factory=dict)
    errors:     dict     = field(default_factory=dict)
    meta:       dict     = field(default_factory=dict)

    def add(self, source: str, items: list):
        self.items[source] = items

    def add_error(self, source: str, error: str):
        self.errors[source] = error

    def all_items(self) -> list:
        out = []
        for items in self.items.values():
            out.extend(items)
        return sorted(out, key=lambda x: x.trend_score, reverse=True)

    def total(self) -> int:
        return sum(len(v) for v in self.items.values())
