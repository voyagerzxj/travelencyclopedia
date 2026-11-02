# Geography Now 笔记

这里是 YouTube 频道 [Geography Now](https://www.youtube.com/@GeographyNow) 全部视频的中文笔记，按发布先后逐个整理。

- **国家介绍集**：放在本文件夹根目录，一个国家一个文件，如 `阿富汗.md`
- **其他视频**按类别放在子文件夹，文件名以视频序号开头：
  - `国旗粉丝日/`：Flag/Fan Friday
  - `地理欣赏/`：Geograppreciation
  - `实地探访/`：Geography Go
  - `补充集/`：Geography More
  - `专题与其他/`：专题讲解、频道动态、问答等

国家介绍集的笔记按节目自己的版块整理：
- 地图与地理位置
- 地形与自然
- 人口与文化
- 外交关系

每篇开头注明视频序号、发布日期和链接。

笔记根据视频字幕整理。只在画面上显示、没有说出来的内容可能有遗漏。

## 目录与工具

- 笔记目录：[00_目录索引.md](00_目录索引.md)
- 跟踪工具 `_tools/gn.py`（需要安装 `yt-dlp`：`pip install yt-dlp`）：
  - `python gn.py update`：刷新频道视频列表，报告新视频（记录在 `_tools/videos.json`）
  - `python gn.py next`：取下一个未处理的视频（加 `--country` 只取国家集），下载字幕到 `_cache/`（不进仓库）
  - `python gn.py done <视频id> <笔记文件名>`：标记完成并重建目录
  - `python gn.py skip <视频id> [原因]`、`python gn.py list [all|pending|done|skipped] [--country]`
