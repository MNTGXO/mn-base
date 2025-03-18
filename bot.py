import asyncio
import feedparser
import logging
import threading
import re
from flask import Flask
from pyrogram import Client
from config import BOT, API, OWNER, CHANNEL  # Removed unused WEB import

# Logging setup
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

# Flask app for health check
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8000)

class MN_Bot(Client):  # Changed class name to MN_Bot

    def __init__(self):
        super().__init__(
            "MN-Bot",
            API.ID,
            API.HASH,
            bot_token=BOT.TOKEN,
            plugins=dict(root="plugins"),
            workers=16,
        )
        self.channel_id = int(CHANNEL.ID)  # Use the new channel ID from config
        self.last_posted_links = set()  # To track previously posted torrents

    async def start(self):
        await super().start()
        me = await self.get_me()
        if me.username:
            BOT.USERNAME = f"@{me.username}"
        self.mention = me.mention
        self.username = me.username

        # Start background task for auto-posting torrents
        asyncio.create_task(self.auto_post_yts())

        await self.send_message(
            chat_id=int(OWNER.ID),
            text=f"{me.first_name} ✅✅ BOT started successfully ✅✅",
        )

        logging.info(f"{me.first_name} ✅✅ BOT started successfully ✅✅")

    async def stop(self, *args):
        await super().stop()
        logging.info("Bot Stopped 🙄")

    async def auto_post_yts(self):
        """Fetch and send new YTS torrents every 30 minutes"""
        while True:
            try:
                torrents = crawl_yts()
                new_torrents = [t for t in torrents if t["link"] not in self.last_posted_links]
                
                if new_torrents:
                    for torrent in new_torrents:
                        message = f"{torrent['link']}\n\n🎬 {torrent['title']}\n📦 {torrent['size']}\n\n#yts powered by @MNBOTS"
                        await self.send_message(self.channel_id, message)
                        self.last_posted_links.add(torrent["link"])

                    logging.info("✅ Auto-posted new YTS torrents")
            except Exception as e:
                logging.error(f"⚠️ Error in auto_post_yts: {e}")

            await asyncio.sleep(1800)  # Wait 30 minutes before checking again

# Function to fetch torrents from YTS RSS feed
def crawl_yts():
    url = "https://yts.mx/rss/0/all/all/0"
    feed = feedparser.parse(url)

    torrents = []
    for entry in feed.entries:
        title = entry.title  # Movie title
        size = parse_size_yts(entry.description)  # Extract size
        link = entry.enclosures[0]["href"]  # Torrent link

        if size:
            torrents.append({
                "title": title,
                "size": size,
                "link": link
            })

    return torrents[:15]  # Limit to the latest 15 torrents

# Extract size from description (YTS format: "<b>Size:</b> 1.2 GB")
def parse_size_yts(description):
    match = re.search(r"<b>Size:</b>\s*([\d.]+\s*[GMK]B)", description)
    return match.group(1) if match else "Unknown"

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    MN_Bot().run()  # Updated to use MN_Bot

