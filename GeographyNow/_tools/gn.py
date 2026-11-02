"""Geography Now 视频跟踪工具。

用法（在任意目录运行均可）:
  python gn.py update            抓取频道视频列表，合并进 videos.json，列出新视频
  python gn.py list [all|pending|done|skipped] [--country]
                                 列出视频（默认 pending）；--country 只看国家介绍集
  python gn.py next [--country]  取最早一个未处理的视频（默认所有类别），下载字幕，转成纯文本
  python gn.py fetch <id>        下载指定视频的字幕
  python gn.py done <id> <笔记文件名>   标记已写完笔记，并重建目录索引
  python gn.py skip <id> [原因]  跳过某个视频（如预告片、无字幕）
  python gn.py index             重建 00_目录索引.md

字幕只缓存在 _cache/（已被 .gitignore 忽略），不进仓库。
"""
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

CHANNEL = "https://www.youtube.com/@GeographyNow/videos"
TOOLS = Path(__file__).resolve().parent
GN_DIR = TOOLS.parent
DB = TOOLS / "videos.json"
CACHE = GN_DIR / "_cache"
INDEX = GN_DIR / "00_目录索引.md"
COUNTRY_RE = re.compile(r"^Geography Now!?\s+(.+)$", re.I)


def ytdlp(*args):
    cmd = [sys.executable, "-m", "yt_dlp", "--no-update", "--no-warnings", *args]
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    if r.returncode != 0 and not r.stdout:
        sys.exit(f"yt-dlp 出错:\n{r.stderr.strip()}")
    return r.stdout


def load():
    if DB.exists():
        return json.loads(DB.read_text(encoding="utf-8"))
    return {"videos": {}}


def save(db):
    db["updated"] = date.today().isoformat()
    DB.write_text(json.dumps(db, ensure_ascii=False, indent=1), encoding="utf-8")


NOT_COUNTRY = re.compile(r"trailer|update|q ?& ?a|more videos|subs|bandiaterra|award|play button|million|\?|special", re.I)

# 类别 -> (中文名, 笔记子文件夹)。国家介绍集放在 GeographyNow/ 根目录
CATEGORIES = {
    "country": ("国家介绍", ""),
    "flagfan": ("国旗/粉丝日", "国旗粉丝日"),
    "appreciation": ("地理欣赏", "地理欣赏"),
    "go": ("实地探访", "实地探访"),
    "more": ("补充集", "补充集"),
    "other": ("专题与其他", "专题与其他"),
}


def category(v):
    if v.get("cat"):  # videos.json 里可手动指定
        return v["cat"]
    t = v["title"]
    if re.search(r"flag\s*/?\s*(fan|friday|day)|fan\s*/?\s*(flag|friday|day)", t, re.I):
        return "flagfan"
    if re.search(r"geograppreciation", t, re.I):
        return "appreciation"
    if re.search(r"geography go\b", t, re.I):
        return "go"
    if re.search(r"geography more\b", t, re.I):
        return "more"
    if COUNTRY_RE.match(t) and not NOT_COUNTRY.search(t):
        return "country"
    return "other"


def is_country(v):
    return category(v) == "country"


def ordered(db, status=None, country=False):
    vs = list(db["videos"].values())
    if status:
        vs = [v for v in vs if v["status"] == status]
    if country:
        vs = [v for v in vs if is_country(v)]
    return sorted(vs, key=lambda v: v["order"])


def cmd_update(db):
    out = ytdlp("--flat-playlist", "--print", "%(id)s\t%(title)s\t%(duration)s", CHANNEL)
    rows = [l.split("\t") for l in out.splitlines() if l.count("\t") == 2]
    # 频道列表是新→旧；order 用倒序编号，使最早的视频 order 最小
    n = len(rows)
    new = []
    for i, (vid, title, dur) in enumerate(rows):
        order = n - i
        v = db["videos"].get(vid)
        if v:
            v["title"], v["order"] = title, order
        else:
            v = {"id": vid, "title": title, "order": order, "status": "pending",
                 "duration": float(dur) if dur not in ("", "NA") else None,
                 "found": date.today().isoformat()}
            db["videos"][vid] = v
            new.append(v)
    save(db)
    print(f"频道共 {n} 个视频；本次新增 {len(new)} 个。")
    if len(new) < n:  # 首次运行时不刷屏
        for v in sorted(new, key=lambda v: v["order"]):
            print(f"  新: {v['id']}  {v['title']}")


def cmd_list(db, which="pending", country=False):
    vs = ordered(db, None if which == "all" else which, country)
    for v in vs:
        print(f"{v['order']:>4}  {v['status']:<8} {v['id']}  {v['title']}")
    print(f"共 {len(vs)} 个")


def vtt_to_text(vtt):
    """把（自动）字幕转成去重的纯文本段落。"""
    lines, last = [], None
    for raw in vtt.splitlines():
        s = raw.strip()
        if not s or s.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")) or "-->" in s or s.isdigit():
            continue
        s = re.sub(r"<[^>]+>", "", s).strip()
        if s and s != last:
            lines.append(s)
            last = s
    text = " ".join(lines)
    # 自动字幕滚动造成的重复短语
    text = re.sub(r"\b(.{20,}?)\s+\1\b", r"\1", text)
    return re.sub(r"\s+", " ", text)


def cmd_fetch(db, vid):
    v = db["videos"].get(vid)
    if not v:
        sys.exit(f"videos.json 里没有 {vid}，先运行 update")
    CACHE.mkdir(exist_ok=True)
    url = f"https://www.youtube.com/watch?v={vid}"
    meta = ytdlp("--skip-download", "--print", "%(upload_date)s\t%(duration)s", url).strip().splitlines()
    if meta:
        up, dur = meta[-1].split("\t")
        v["upload_date"] = f"{up[:4]}-{up[4:6]}-{up[6:]}" if len(up) == 8 else up
    for f in CACHE.glob(f"{vid}*.vtt"):
        f.unlink()
    # 只要英文原轨，避免请求大量翻译字幕导致 429
    ytdlp("--skip-download", "--write-subs", "--write-auto-subs",
          "--sub-langs", "en,en-US,en-GB,en-orig", "--sub-format", "vtt",
          "-o", str(CACHE / "%(id)s.%(ext)s"), url)
    vtts = sorted(CACHE.glob(f"{vid}*.vtt"), key=lambda p: (".en.vtt" not in p.name, p.name))
    if not vtts:
        save(db)
        sys.exit(f"{vid} 没有英文字幕。可用: python gn.py skip {vid} 无字幕")
    txt = CACHE / f"{vid}.txt"
    body = vtt_to_text(vtts[0].read_text(encoding="utf-8"))
    txt.write_text(f"{v['title']}\n{url}\n上传: {v.get('upload_date', '?')}\n\n{body}\n", encoding="utf-8")
    save(db)
    print(f"标题: {v['title']}\n链接: {url}\n上传: {v.get('upload_date', '?')}\n"
          f"字幕: {txt}  ({len(body.split())} 词)")


def cmd_next(db, country=False):
    vs = ordered(db, "pending", country)
    if not vs:
        print("没有待处理的视频。")
        return
    cmd_fetch(db, vs[0]["id"])


def cmd_done(db, vid, note):
    v = db["videos"][vid]
    v["status"], v["note"], v["done"] = "done", note, date.today().isoformat()
    save(db)
    cmd_index(db)
    print(f"已完成: {v['title']} -> {note}")


def cmd_skip(db, vid, reason=""):
    v = db["videos"][vid]
    v["status"], v["skip_reason"] = "skipped", reason
    save(db)
    print(f"已跳过: {v['title']} ({reason})")


def cmd_index(db):
    done = ordered(db, "done")
    allv = ordered(db)
    counts = {}
    for v in allv:
        counts[category(v)] = counts.get(category(v), 0) + 1
    summary = "、".join(f"{CATEGORIES[c][0]} {counts.get(c, 0)}" for c in CATEGORIES)
    out = ["# Geography Now 笔记目录", "",
           f"已完成 {len(done)} / {len(allv)} 个视频（{summary}）。按视频发布先后排列。", "",
           "国家介绍集在本文件夹根目录，其他视频按类别放在子文件夹里。", "",
           "| # | 类别 | 笔记 | 视频 | 发布 |", "|---|---|---|---|---|"]
    for v in done:
        note = v["note"]
        out.append(f"| {v['order']} | {CATEGORIES[category(v)][0]} | [{Path(note).stem}]({note}) "
                   f"| [{v['title']}](https://www.youtube.com/watch?v={v['id']}) | {v.get('upload_date', '')} |")
    INDEX.write_text("\n".join(out) + "\n", encoding="utf-8")


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    country = "--country" in a
    a = [x for x in a if x != "--country"]
    db = load()
    c = a[0]
    if c == "update":
        cmd_update(db)
    elif c == "list":
        cmd_list(db, a[1] if len(a) > 1 else "pending", country)
    elif c == "next":
        cmd_next(db, country)
    elif c == "fetch":
        cmd_fetch(db, a[1])
    elif c == "done":
        cmd_done(db, a[1], a[2])
    elif c == "skip":
        cmd_skip(db, a[1], " ".join(a[2:]))
    elif c == "index":
        cmd_index(db)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
