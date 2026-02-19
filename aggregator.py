import time
from .config import Config
from .data import AggregatedResults
from .scorer import TrendScorer
from .filter import ContentFilter
from ..scrapers.tiktok import TikTokScraper
from ..scrapers.instagram import InstagramScraper
from ..scrapers.reddit import RedditScraper
from ..scrapers.youtube import YouTubeScraper


SCRAPERS = {
    "tiktok":    TikTokScraper,
    "instagram": InstagramScraper,
    "reddit":    RedditScraper,
    "youtube":   YouTubeScraper,
}


class Aggregator:
    def __init__(self, config: Config):
        self.config  = config
        self.scorer  = TrendScorer(weights=config.get("report.trending_score_weight"))
        self.filter  = ContentFilter(config)

    def run(self, sources: list = None) -> AggregatedResults:
        results = AggregatedResults()
        targets = sources or list(SCRAPERS.keys())

        print(f"\n{'='*55}")
        print(f"  SocialRadar — Trending Content Aggregator")
        print(f"{'='*55}\n")

        for name in targets:
            if not self.config.is_enabled(name):
                print(f"  [{name.upper()}] skipped (disabled in config)")
                continue

            cls     = SCRAPERS[name]
            scraper = cls(self.config)

            print(f"  [{name.upper()}] fetching...", end=" ", flush=True)
            t0 = time.time()

            try:
                items = scraper.fetch()
                items = self.filter.apply(items)
                items = self.scorer.score_all(items)
                results.add(name, items)
                elapsed = round(time.time() - t0, 1)
                print(f"{len(items)} items  ({elapsed}s)")
            except Exception as e:
                results.add_error(name, str(e))
                print(f"ERROR — {e}")

        print(f"\n  Total: {results.total()} trending items across {len(results.items)} sources\n")
        return results
