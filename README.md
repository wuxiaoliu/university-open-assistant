# 大学开放助手（v0.2 自动抓取版）

沙河高教园周边 9 所高校开放信息查询，**自动抓取各校公众号最新文章**。

## 文件结构

```
大学开放助手/
├── index.html                  # 手机网页 UI（搜索/筛选/卡片）
├── schools.json                # 学校基础信息（手动维护）
├── articles.json               # 抓取到的最新公众号文章（脚本生成）
├── fetch_news.py               # 抓取脚本
└── .github/workflows/update.yml  # GitHub Actions：每日自动抓取
```

## 数据流

```
schools.json ─┐
              ├──> index.html （前端 fetch 渲染）
articles.json ┘     ▲
                    │ 每天自动更新
              fetch_news.py ──> 搜狗微信 / Bing 搜索
```

## 本地运行

```bash
# 1) 抓一次最新数据（可选，首次跑会生成 articles.json）
pip install requests beautifulsoup4
python3 fetch_news.py

# 2) 启动本地服务（必须！直接双击 file:// 打开浏览器无法读取 json）
python3 -m http.server 8000

# 3) 浏览器访问 http://localhost:8000
#    手机同 WiFi 访问 http://你电脑的IP:8000
```

## 部署到线上（推荐）

最简单：**GitHub Pages + GitHub Actions 自动更新**

1. 在 GitHub 新建 repo，把整个 `大学开放助手/` 目录推上去
2. Settings → Pages → Branch 选 `main` / Folder 选 `/(root)` → 保存
3. 拿到网址 `https://你的用户名.github.io/repo名/`
4. **抓取脚本会每天北京时间早上 7 点自动跑**，更新 `articles.json` 并 commit 推送，网页内容自动刷新
5. 也可以在 Actions 页面手动点 "Run workflow" 立即触发一次

> 推到 GitHub 之前先在仓库根目录运行一次 `python3 fetch_news.py`，让 articles.json 有内容；之后每天自动维护。

## 维护

- **改学校信息**：编辑 `schools.json`，commit 即可
- **加学校**：在 `schools.json` 数组追加一条，字段参考已有
- **抓不到怎么办**：搜狗微信偶尔会触发反爬，脚本会自动降级到 Bing；都失败时会保留上次结果不清空。多跑几次或等下一轮即可

## 抓取策略说明

- 主源：**搜狗微信**（`weixin.sogou.com`）—— 直接搜公众号文章
- 备源：**Bing 中文搜索**（`cn.bing.com`）—— 反爬较弱
- 关键词过滤：标题包含「开放/预约/参观/访客/入校/校园」才入选
- 礼貌延迟：每个学校间隔 2-4 秒，避免被封
- 失败兜底：本次抓不到的学校，沿用 `articles.json` 中上次的结果

## 注意

- 抓取的文章只是**辅助参考**，最权威的还是各校公众号最新公告 + 校门电话
- 学校开放政策变化频繁，每次出行前请再次确认
