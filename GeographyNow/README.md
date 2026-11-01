# Geography Now 笔记

这里是 YouTube 频道 [Geography Now](https://www.youtube.com/@GeographyNow) 国家介绍视频的中文笔记，每个国家一个文件。

每篇笔记按节目自己的版块整理：
- 地图与地理位置
- 地形与自然
- 人口与文化
- 外交关系

每篇末尾注明视频链接和发布日期。

笔记根据视频字幕整理。只在画面上显示、没有说出来的内容可能有遗漏。

## 目录与工具

- 笔记目录：[00_目录索引.md](00_目录索引.md)
- 跟踪工具 `_tools/gn.py`（需要安装 `yt-dlp`：`pip install yt-dlp`）：
  - `python gn.py update`：刷新频道视频列表，报告新视频（记录在 `_tools/videos.json`）
  - `python gn.py next --country`：取下一个未处理的国家集，下载字幕到 `_cache/`（不进仓库）
  - `python gn.py done <视频id> <笔记文件名>`：标记完成并重建目录
  - `python gn.py skip <视频id> [原因]`、`python gn.py list [all|pending|done|skipped] [--country]`
