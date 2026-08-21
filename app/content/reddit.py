import json
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


class RedditScraper:
    def __init__(self):
        self.reddit = None
        if settings.reddit_client_id and settings.reddit_client_secret:
            import praw
            self.reddit = praw.Reddit(
                client_id=settings.reddit_client_id,
                client_secret=settings.reddit_client_secret,
                user_agent=settings.reddit_user_agent,
            )

    def is_available(self) -> bool:
        return self.reddit is not None

    def fetch_posts(self, subreddit: str = "AskReddit", limit: int = 15, min_comments: int = 500):
        if not self.reddit:
            logger.warning("Reddit not configured")
            return []

        posts = []
        try:
            for post in self.reddit.subreddit(subreddit).hot(limit=limit * 2):
                if post.num_comments < min_comments:
                    continue
                if post.stickied:
                    continue

                comments = []
                post.comments.replace_more(limit=0)
                top_comments = post.comments[:30]

                for comment in top_comments:
                    if not comment.body or len(comment.body) < 20:
                        continue
                    if comment.body in ("[deleted]", "[removed]"):
                        continue

                    replies = []
                    comment.replies.replace_more(limit=0) if hasattr(comment.replies, 'replace_more') else None
                    for reply in comment.replies[:5]:
                        if reply.body and reply.body not in ("[deleted]", "[removed]"):
                            replies.append({
                                "text": reply.body,
                                "score": reply.score,
                                "author": str(reply.author),
                            })

                    comments.append({
                        "text": comment.body,
                        "score": comment.score,
                        "author": str(comment.author),
                        "replies": replies,
                    })

                posts.append({
                    "source": "reddit",
                    "source_url": f"https://reddit.com{post.permalink}",
                    "title": post.title,
                    "selftext": post.selftext,
                    "comments": comments,
                    "subreddit": subreddit,
                    "num_comments": post.num_comments,
                    "score": post.score,
                })

                if len(posts) >= limit:
                    break

            logger.info(f"Fetched {len(posts)} posts from r/{subreddit}")
        except Exception as e:
            logger.error(f"Reddit fetch error: {e}")

        return posts

    def format_script_for_review(self, post: dict) -> dict:
        sorted_comments = sorted(post["comments"], key=lambda c: c["score"], reverse=True)
        script_lines = []
        for c in sorted_comments:
            script_lines.append(f"COMMENT (score:{c['score']}): {c['text']}")
            for r in c.get("replies", []):
                script_lines.append(f"  REPLY (score:{r['score']}): {r['text']}")

        return {
            "id": post.get("source_url", "").split("/")[-1] or post["title"][:20],
            "title": post["title"],
            "source": "reddit",
            "source_url": post["source_url"],
            "content": "\n\n".join(script_lines),
            "comment_list": post["comments"],
            "score": post.get("score", 0),
            "subreddit": post.get("subreddit", "AskReddit"),
        }
