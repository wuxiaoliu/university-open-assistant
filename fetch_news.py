#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_news.py
抓取各高校公众号 / 网络上关于「校园开放、访客预约」的最新文章。

策略（多数据源 + 优雅降级）：
  1. 搜狗微信搜索（weixin.sogou.com）—— 主源，能直达学校公众号文章
  2. Bing 搜索（cn.bing.com）—— 备用源，反爬较弱
  失败的学校保留上次的 articles，不会清空。

输出：articles.json，结构：
{
  "lastFetched": "2026-05-27 10:00",
  "items": {
    "buaa": [ { "title": "...", "url": "...", "source": "搜狗微信/Bing", "date": "..." }, ... ],
    ...
  }
}

依赖：requests、beautifulsoup4
  pip install requests beautifulsoup4
"""

import json
import os
import re
import sys
import time
import random
from datetime import datetime
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("请先安装依赖：pip install requests beautifulsoup4", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).parent
SCHOOLS_FILE = ROOT / "schools.json"
ARTICLES_FILE = ROOT / "articles.json"

UA_LIST = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
]

MAX_PER_SCHOOL = 5
TIMEOUT = 12


def headers():
    return {
        "User-Agent": random.choice(UA_LIST),
        "Accept-Language": "zh-CN,zh;q=0.9",
    }


def fetch_sogou(query: str):
    """搜狗微信搜索结果。"""
    url = "https://weixin.sogou.com/weixin"
    params = {"type": "2", "query": query, "ie": "utf8"}
    try:
        r = requests.get(url, params=params, headers=headers(), timeout=TIMEOUT)
        if r.status_code != 200:
            return []
        # 搜狗反爬时会跳验证码页，简单识别一下
        if "请输入验证码" in r.text or "antispider" in r.url:
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        results = []
        for li in soup.select("ul.news-list li"):
            a = li.select_one("h3 a") or li.select_one("a")
            if not a:
                continue
            title = a.get_text(" ", strip=True)
            href = a.get("href", "")
            if href.startswith("/"):
                href = "https://weixin.sogou.com" + href
            date_el = li.select_one(".s2") or li.select_one(".s-p")
            date_text = date_el.get_text(" ", strip=True) if date_el else ""
            if title and href:
                results.append({
                    "title": title,
                    "url": href,
                    "source": "搜狗微信",
                    "date": date_text,
                })
            if len(results) >= MAX_PER_SCHOOL:
                break
        return results
    except Exception as e:
        print(f"  [搜狗失败] {e}", file=sys.stderr)
        return []


def fetch_bing(query: str):
    """Bing 搜索作为备用源。"""
    url = "https://cn.bing.com/search"
    params = {"q": query + " 公众号", "ensearch": "0"}
    try:
        r = requests.get(url, params=params, headers=headers(), timeout=TIMEOUT)
        if r.status_code != 200:
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        results = []
        for li in soup.select("li.b_algo"):
            a = li.select_one("h2 a")
            if not a:
                continue
            title = a.get_text(" ", strip=True)
            href = a.get("href", "")
            if not title or not href:
                continue
            results.append({
                "title": title,
                "url": href,
                "source": "Bing",
                "date": "",
            })
            if len(results) >= MAX_PER_SCHOOL:
                break
        return results
    except Exception as e:
        print(f"  [Bing失败] {e}", file=sys.stderr)
        return []


def filter_relevant(items):
    """只保留标题包含「开放/预约/参观/访客」等关键词的条目。"""
    keys = ("开放", "预约", "参观", "访客", "入校", "校园")
    return [x for x in items if any(k in x["title"] for k in keys)]


def main():
    if not SCHOOLS_FILE.exists():
        print(f"找不到 {SCHOOLS_FILE}", file=sys.stderr)
        sys.exit(1)

    schools = json.loads(SCHOOLS_FILE.read_text(encoding="utf-8"))

    # 复用历史结果作为兜底
    prev = {}
    if ARTICLES_FILE.exists():
        try:
            prev = json.loads(ARTICLES_FILE.read_text(encoding="utf-8")).get("items", {})
        except Exception:
            prev = {}

    items = {}
    for s in schools:
        sid = s["id"]
        query = s.get("search_query") or s["name"]
        print(f"[{sid}] {query}")

        articles = fetch_sogou(query)
        if not articles:
            time.sleep(1 + random.random())
            articles = fetch_bing(query)

        articles = filter_relevant(articles)

        if not articles and prev.get(sid):
            print(f"  → 本次未抓到，沿用上次结果 {len(prev[sid])} 条")
            items[sid] = prev[sid]
        else:
            items[sid] = articles
            print(f"  → 收录 {len(articles)} 条")

        # 礼貌延迟，避免被封
        time.sleep(2 + random.random() * 2)

    out = {
        "lastFetched": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "items": items,
    }
    ARTICLES_FILE.write_text(
        json.dumps(out, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    total = sum(len(v) for v in items.values())
    print(f"\n完成：{ARTICLES_FILE.name}，共 {total} 条文章。")


if __name__ == "__main__":
    main()
