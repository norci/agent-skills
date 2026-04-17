---
name: rss-news-aggregation
description:凡需聚合 RSS feed、管理新闻源、增量更新内容，即当加载。
---

# RSS 聚合之道

## 要义
以 newsboat 代自研脚本，增量拉取，SQLite 缓存

## 何以 newsboat
- **增量更新**：仅取新篇，省带宽
- **本地缓存**：SQLite 存已读状态
- **鲁棒性**：善处编码、超时、畸形 feed

## 部署

```bash
# 安装
sudo pacman -S newsboat # Arch
sudo apt install newsboat # Debian

# 建目录
mkdir -p ~/.config/newsboat ~/.local/share/newsboat
```

**~/.config/newsboat/urls** 示例：
```
https://sspai.com/feed
https://36kr.com/feed
```

**~/.config/newsboat/config** 示例：
```
cache-file ~/.local/share/newsboat/cache.db
reload-time 30
reload-threads 5
```

## 用法

```bash
newsboat -x reload # 更新
newsboat # 交互浏览
```

## 避坑
- 中文大站 RSS 多废，先以 `curl -sI` 验之
- UTF-8 报错则删畸形 feed
- 配置元素仅可用：listnormal, listfocus, listnormal_unread, listfocus_unread, title, info, article, searchhighlight
