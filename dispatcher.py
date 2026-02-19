from ..core.config import Config
from ..core.data import AggregatedResults
from .senders import DiscordSender, TelegramSender, EmailSender


class Dispatcher:
    def __init__(self, config: Config):
        self.config  = config
        self.senders = []
        self._init_senders()

    def _init_senders(self):
        channels = self.config.get("notifications.channels", {})

        if channels.get("discord", {}).get("enabled"):
            self.senders.append(DiscordSender(channels["discord"]))

        if channels.get("telegram", {}).get("enabled"):
            self.senders.append(TelegramSender(channels["telegram"]))

        if channels.get("email", {}).get("enabled"):
            self.senders.append(EmailSender(channels["email"]))

    def send(self, results: AggregatedResults):
        if not self.senders:
            return

        message = self._format_message(results)
        for sender in self.senders:
            try:
                sender.send(message, results)
                print(f"  Notification sent via {sender.__class__.__name__}")
            except Exception as e:
                print(f"  Notification failed ({sender.__class__.__name__}): {e}")

    def _format_message(self, results: AggregatedResults) -> str:
        items = results.all_items()[:10]
        lines = ["🔥 **SocialRadar — Top Trending Now**\n"]
        for i, item in enumerate(items, 1):
            lines.append(f"{i}. [{item.source.upper()}] {item.title[:80]}")
            lines.append(f"   👁 {item.views:,}  ❤ {item.likes:,}  ⚡ {item.trend_score:.0f}")
            lines.append(f"   {item.url}\n")
        return "\n".join(lines)
