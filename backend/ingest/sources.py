"""信源 RSS 配置 v0.1

每个信源包含：
- name: 显示名
- url: RSS / Atom feed URL（只列有 feed 的，没有的留 None 走人工路径）
- tier: 必装 / 推荐 / 加分
- type: newsletter / blog / media / research
- lang: en / zh
- default_domain: 路由默认 domain
- default_category: 路由默认 category

原则：
1. 只列**有真实 RSS feed**的信源（v0.1 不爬 HTML 页面，太贵）
2. 找不到 feed 的（如 Twitter/X、Reddit 主页）留 None，靠 v0.3 接 RSSHub 或人工补充
3. 跑通后通过候选 JSON 看到信源覆盖情况，迭代补源

信源清单 1:1 对应 data/source-list-v0.1.md。
"""
from typing import Literal, Optional

Tier = Literal["core", "recommended", "bonus"]
Lang = Literal["en", "zh"]
Type = Literal["newsletter", "blog", "media", "research", "official"]


class Source:
    __slots__ = ("name", "url", "tier", "type", "lang", "default_domain", "default_category")

    def __init__(
        self,
        name: str,
        url: Optional[str],
        tier: Tier,
        type: Type,
        lang: Lang,
        default_domain: str,
        default_category: str,
    ):
        self.name = name
        self.url = url
        self.tier = tier
        self.type = type
        self.lang = lang
        self.default_domain = default_domain
        self.default_category = default_category

    def to_dict(self):
        return {
            "name": self.name,
            "url": self.url,
            "tier": self.tier,
            "type": self.type,
            "lang": self.lang,
            "default_domain": self.default_domain,
            "default_category": self.default_category,
        }


# ===== 英文核心 (10) =====
EN_CORE = [
    Source("Stratechery", "https://stratechery.com/feed/", "core", "blog", "en", "business", "partnership"),
    Source("Latent Space", "https://www.latent.space/feed", "core", "newsletter", "en", "agent", "agent_framework"),
    Source("Import AI", "https://importai.substack.com/feed", "core", "newsletter", "en", "policy", "policy"),
    Source("Simon Willison", "https://simonwillison.net/atom/everything/", "core", "blog", "en", "tooling", "product_launch"),
    Source("TLDR AI", "https://tldr.tech/ai/feed", "core", "newsletter", "en", "llm", "model_release"),
    Source("The Pragmatic Engineer", "https://newsletter.pragmaticengineer.com/feed", "core", "newsletter", "en", "infra", "product_launch"),
    Source("Ben's Bites", "https://www.bensbites.com/feed", "core", "newsletter", "en", "application", "product_launch"),
    Source("The Batch (DeepLearning.AI)", "https://www.deeplearning.ai/the-batch/feed/", "core", "newsletter", "en", "llm", "model_capability"),
    Source("AlphaSignal", "https://alphasignal.ai/feed", "core", "newsletter", "en", "llm", "model_release"),
    Source("Hacker News (AI filter)", "https://hnrss.org/newest?q=AI+OR+LLM+OR+agent", "core", "media", "en", "llm", "product_launch"),
]

# ===== 英文推荐 (10) =====
EN_RECOMMENDED = [
    Source("Sequoia AI", "https://www.sequoiacap.com/feed/", "recommended", "blog", "en", "business", "funding"),
    Source("a16z AI", "https://a16z.com/category/ai/feed/", "recommended", "blog", "en", "business", "funding"),
    Source("Hugging Face Blog", "https://huggingface.co/blog/feed.xml", "recommended", "blog", "en", "llm", "open_source"),
    Source("LangChain Blog", "https://blog.langchain.dev/rss/", "recommended", "blog", "en", "agent", "agent_framework"),
    Source("Anthropic News", "https://www.anthropic.com/news/rss.xml", "recommended", "official", "en", "llm", "model_release"),
    Source("OpenAI Blog", "https://openai.com/blog/rss.xml", "recommended", "official", "en", "llm", "model_release"),
    Source("Google DeepMind Blog", "https://deepmind.google/discover/blog/rss.xml", "recommended", "official", "en", "llm", "research"),
    Source("Microsoft AI Blog", "https://blogs.microsoft.com/ai/feed/", "recommended", "blog", "en", "application", "product_launch"),
    Source("MIT Tech Review AI", "https://www.technologyreview.com/topic/artificial-intelligence/feed", "recommended", "media", "en", "llm", "research"),
    Source("Papers With Code", "https://paperswithcode.com/feed", "recommended", "research", "en", "llm", "research"),
]

# ===== 英文加分 (10) =====
EN_BONUS = [
    Source("The Information AI", None, "bonus", "media", "en", "business", "funding"),  # 付费墙
    Source("VentureBeat AI", "https://venturebeat.com/ai/feed/", "bonus", "media", "en", "business", "funding"),
    Source("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/", "bonus", "media", "en", "business", "funding"),
    Source("The Verge AI", "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml", "bonus", "media", "en", "application", "product_launch"),
    Source("ArXiv cs.AI", "https://export.arxiv.org/rss/cs.AI", "bonus", "research", "en", "llm", "research"),
    Source("ArXiv cs.CL", "https://export.arxiv.org/rss/cs.CL", "bonus", "research", "en", "llm", "research"),
    Source("ArXiv cs.LG", "https://export.arxiv.org/rss/cs.LG", "bonus", "research", "en", "llm", "research"),
    Source("r/MachineLearning", "https://www.reddit.com/r/MachineLearning/.rss", "bonus", "media", "en", "llm", "research"),
    Source("r/LocalLLaMA", "https://www.reddit.com/r/LocalLLaMA/.rss", "bonus", "media", "en", "llm", "open_source"),
    Source("Hacker News (frontpage)", "https://hnrss.org/frontpage", "bonus", "media", "en", "llm", "product_launch"),
]

# ===== 中文 (10) =====
ZH = [
    Source("机器之心", "https://www.jiqizhixin.com/rss", "core", "media", "zh", "llm", "model_release"),
    Source("量子位", "https://www.qbitai.com/feed", "core", "media", "zh", "llm", "model_release"),
    Source("36氪 AI", "https://36kr.com/feed", "core", "media", "zh", "business", "funding"),
    Source("AI 前线 (InfoQ)", "https://www.infoq.cn/feed.xml", "recommended", "media", "zh", "application", "product_launch"),
    Source("虎嗅", "https://www.huxiu.com/rss/0.xml", "recommended", "media", "zh", "business", "partnership"),
    Source("Founder Park", "https://founderpark.com/feed", "recommended", "media", "zh", "agent", "agent_framework"),
    Source("AI 科技评论", "https://www.leiphone.com/feed", "recommended", "media", "zh", "llm", "model_capability"),
    Source("APPSO", "https://www.appso.com.cn/feed", "bonus", "media", "zh", "application", "product_launch"),
    Source("晚点 LatePost", None, "bonus", "media", "zh", "business", "funding"),  # 付费
    Source("硬地骇客", "https://hardhacker.com/feed", "bonus", "blog", "zh", "agent", "agent_framework"),
]

ALL_SOURCES = EN_CORE + EN_RECOMMENDED + EN_BONUS + ZH


def active_sources():
    """只返回有 RSS URL 的信源（url=None 走人工路径）"""
    return [s for s in ALL_SOURCES if s.url]


if __name__ == "__main__":
    print(f"信源总数: {len(ALL_SOURCES)}")
    print(f"  有 RSS feed: {len(active_sources())}")
    print(f"  待人工补充: {len(ALL_SOURCES) - len(active_sources())}")
    by_lang = {"en": 0, "zh": 0}
    for s in ALL_SOURCES:
        by_lang[s.lang] += 1
    print(f"  英文: {by_lang['en']}  中文: {by_lang['zh']}")
