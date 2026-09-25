#!/usr/bin/env python3
"""Muse Icons 接入脚本：把 1muse 源码中的 Tabler / Material 图标引用替换为 MuseIcons.xxx()。

用法:
    python scripts/replace-icons.py --src <app/src/main/java>            # dry-run（只报告）
    python scripts/replace-icons.py --src <app/src/main/java> --apply    # 写回
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ICON_KEYS = set(json.loads((ROOT / "icons.json").read_text(encoding="utf-8")).keys())

KOTLIN_KEYWORDS = {
    "package", "is", "in", "object", "class", "fun", "val", "var", "when",
    "if", "else", "for", "while", "return", "as", "break", "continue",
}

# 旧名（PascalCase）→ Muse key 的特例映射；未命中特例时按 snake_case 自动匹配。
SPECIAL = {
    # 操作
    "Add": "plus", "Close": "x", "Cancel": "x", "Clear": "x",
    "Delete": "trash", "DeleteOutline": "trash", "Replay": "refresh",
    # 方向
    "ArrowBack": "arrow_left", "ArrowForward": "arrow_right",
    "ArrowDownward": "arrow_down", "ArrowUpward": "arrow_up", "ArrowDropDown": "chevron_down",
    "ExpandMore": "chevron_down", "ExpandLess": "chevron_up",
    "KeyboardArrowDown": "chevron_down", "KeyboardArrowUp": "chevron_up",
    "KeyboardArrowLeft": "chevron_left", "KeyboardArrowRight": "chevron_right",
    "ArrowsLeftRight": "swap_horizontal", "ArrowsRight": "arrow_right",
    "ArrowsMaximize": "maximize",
    "MoreVert": "more_vertical", "MoreHoriz": "more_horizontal",
    # 状态
    "CheckCircle": "circle_check", "Error": "alert_circle", "ErrorOutline": "alert_circle",
    "Warning": "alert_triangle", "PriorityHigh": "alert_circle",
    "Visibility": "eye", "VisibilityOff": "eye_off",
    "HowToVote": "check", "Pending": "clock",
    "Security": "shield", "VerifiedUser": "shield_check", "HealthAndSafety": "shield_check",
    # 复制 / 文件 / 媒体
    "ContentCopy": "copy", "ContentPaste": "clipboard", "AttachFile": "paperclip",
    "IosShare": "share",
    "Photo": "image", "Image": "image", "PhotoLibrary": "photo_library",
    "PhotoCamera": "camera", "CameraAlt": "camera",
    "Mic": "microphone", "RecordVoiceOver": "microphone", "GraphicEq": "wave_sine",
    "Description": "file_text", "Article": "file_text", "InsertDriveFile": "file",
    "FileMusic": "file", "FileSearch": "file",
    "CreateNewFolder": "folder_plus", "FolderOpen": "folder_open",
    "Unarchive": "archive", "Package": "package", "Storage": "database",
    "DeviceFloppy": "device_floppy", "DeviceMobile": "device_mobile",
    # 人物
    "Person": "user", "AccountCircle": "user", "SmartToy": "robot", "GroupWork": "users",
    # AI / Muse 域
    "Psychology": "brain", "Memory": "memory_chip", "AutoAwesome": "sparkle",
    "Celebration": "celebration", "Wand": "wand", "CleaningServices": "wand",
    "Build": "wrench", "Tool": "wrench", "Tools": "wrench",
    "Extension": "puzzle", "Plug": "plug",
    "MenuBook": "book_open", "LibraryBooks": "book_open",
    "AccountTree": "hierarchy", "Sitemap": "hierarchy", "Hierarchy": "hierarchy",
    "Adjustments": "sliders", "Tune": "sliders", "AdminPanelSettings": "sliders",
    "Settings": "sliders",
    # 通信 / 媒体
    "Chat": "chat", "ChatBubbleOutline": "chat", "Message": "chat",
    "MessageCircle": "chat", "Forum": "messages", "Messages": "messages",
    "MessagesOff": "messages",
    "Mail": "mail", "Email": "mail", "MarkEmailRead": "mail",
    "VideoLibrary": "video", "Movie": "movie",
    "VolumeUp": "volume", "Volume": "volume",
    "PlayArrow": "play", "PlayCircle": "play", "Pause": "pause", "Stop": "stop",
    "Send": "send", "Reply": "reply", "Forward": "forward",
    # 数据 / 云
    "CloudDownload": "cloud_download", "FileDownload": "download", "Download": "download",
    "FileUpload": "upload", "FileImport": "upload", "Upload": "upload",
    "CloudUpload": "cloud_upload", "CloudOff": "cloud_off",
    # 内容
    "Note": "note", "Notes": "note",
    "StarBorder": "star", "Favorite": "heart", "FavoriteBorder": "heart",
    "BookmarkBorder": "bookmark", "ThumbUp": "thumb_up", "PushPin": "pin", "Pinned": "pin",
    # 时间 / 天气
    "Schedule": "clock", "CalendarToday": "calendar", "AccessTime": "clock",
    "CalendarTime": "calendar_time", "CalendarStats": "calendar_stats",
    "WbSunny": "sun", "Sun": "sun", "Brightness": "sun",
    "DarkMode": "moon", "Moon": "moon", "MoonStars": "moon_stars",
    # 布局 / 图形
    "Sort": "sort", "SortByAlpha": "sort", "FilterList": "filter",
    "LayoutDistributeHorizontal": "layout_columns",
    "LayersSubtract": "stack", "ToggleLeft": "switch",
    "CallSplit": "git_merge", "SwapHoriz": "swap_horizontal",
    # 位置 / 其他
    "Compass": "compass", "Explore": "compass",
    "MapPin": "map_pin", "LocationOn": "map_pin",
    "World": "globe", "Planet": "planet", "Propeller": "wind",
    "Science": "flask", "Home": "home", "School": "school", "Rocket": "rocket",
    "Activity": "activity", "Analytics": "chart_line",
    "Bug": "bug", "BugReport": "bug", "Code": "code", "Braces": "braces",
    "Brush": "brush", "Palette": "palette", "ColorSwatch": "color_swatch",
    "Edit": "edit", "DriveFileRenameOutline": "edit", "Pencil": "edit",
    "Qrcode": "qrcode", "QrCode": "qrcode", "Wallet": "wallet",
    "TrendingDown": "trending_down", "TrendingUp": "trending_up",
    "Typography": "typography", "WaveSine": "wave_sine", "Infinity": "infinity",
    "HandFinger": "hand-finger",
    "BatteryFull": "battery", "Block": "ban", "Calculate": "calculator",
    "Language": "languages", "InfoCircle": "info", "Notifications": "bell",
    "PlayerPlay": "play", "SwitchHorizontal": "swap-horizontal",
    "HelpOutline": "help", "Lightbulb": "bulb",
    "OpenInNew": "external-link", "OpenInBrowser": "browser",
    "Summarize": "file-text", "EditNote": "edit", "DotsVertical": "more-vertical",
    "Translate": "languages",
    # 品牌
    "BrandAndroid": "brand_android", "BrandBing": "brand_bing",
    "BrandGithub": "brand_github", "BrandGoogle": "brand_google",
    "BrandTelegram": "brand_telegram",
}

PATTERNS = [
    re.compile(r"TablerIcons\.([A-Za-z]+)"),
    re.compile(r"Icons\.(?:Default|Filled|Outlined|Rounded)\.([A-Za-z]+)"),
    re.compile(r"Icons\.AutoMirrored\.(?:Filled|Outlined|Rounded)\.([A-Za-z]+)"),
    re.compile(r"icons\.automirrored\.(?:filled|outlined|rounded)\.([A-Za-z]+)"),
]

# 通配导入文件（import compose.icons.tablericons.*）的裸名替换词表。
_TABLER_RAW = """
Activity, Adjustments, Affiliate, AlertCircle, AlertTriangle, Archive, ArrowDown,
ArrowForward, ArrowLeft, ArrowRight, ArrowsLeftRight, ArrowsMaximize, ArrowsRight,
ArrowsVertical, ArrowUp, At, Atom, Ban, Bell, Bolt, Book, Bookmark, Box, Braces,
BrandAndroid, BrandBing, BrandGithub, BrandGoogle, BrandTelegram, Brightness, Browser,
Bug, Bulb, Calculator, Calendar, CalendarStats, CalendarTime, Camera, ChartBar, ChartLine,
Check, ChevronDown, ChevronLeft, ChevronRight, ChevronUp, Circle, CircleCheck, CircleMinus,
Clipboard, Clock, Cloud, CloudDownload, CloudOff, CloudUpload, Code, ColorSwatch, Compass,
Copy, Database, DeviceFloppy, DeviceMobile, DotsVertical, Download, Edit, ExternalLink,
Eye, EyeOff, Feather, File, FileDownload, FileImport, FileMusic, FileSearch, FileText,
FileUpload, Flame, Flask, Folder, Gauge, GitMerge, Globe, GripVertical, HandFinger, Heart,
Help, Hexagon, Hierarchy, History, Home, Infinity, InfoCircle, Key, Language, LayersSubtract,
LayoutColumns, LayoutDistributeHorizontal, Lifebuoy, Link, Lock, Mail, MapPin, Message,
MessageCircle, Messages, MessagesOff, Microphone, Minus, MoodSad, MoodSmile, Moon, MoonStars,
Note, Notes, Package, Palette, Paperclip, Pencil, Phone, Photo, Pinned, Planet, PlayerPlay,
Plug, Plus, Power, Propeller, Puzzle, Qrcode, Refresh, Rocket, Route, Router, Rss, School,
Search, Send, Server, Settings, Share, Shield, ShieldCheck, Sitemap, Square, Stack, Star,
Stars, Sun, Switch, SwitchHorizontal, Temperature, Template, Terminal, ThumbUp, ToggleLeft,
Tool, Tools, Trash, TrendingDown, Typography, User, Users, Video, Volume, Wallet, Wand,
WaveSine, Wifi, Wind, World, X
"""
TABLER_NAMES = sorted(
    {n.strip() for n in _TABLER_RAW.replace("\n", " ").split(",") if n.strip()},
    key=len,
    reverse=True,
)

# 通配文件里裸名的“图标位置”上下文（避免误伤类名 / import / 变量名）。
BARE_CONTEXT_PATTERNS = [
    re.compile(r"(\bIcon\(\s*)([A-Z][A-Za-z]+)\b"),
    re.compile(r"(\bimageVector\s*=\s*)([A-Z][A-Za-z]+)\b"),
    re.compile(
        r"(\b(?:icon|leadingIcon|trailingIcon|startIcon|endIcon)\s*=\s*)([A-Z][A-Za-z]+)\b"
    ),
]


def to_snake(name: str) -> str:
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name)
    s = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", "_", s)
    return s.lower()


def camel(key: str) -> str:
    parts = key.replace("-", "_").split("_")
    fn = parts[0] + "".join(p.capitalize() for p in parts[1:])
    if fn in KOTLIN_KEYWORDS:
        fn += "Icon"
    return fn


def map_name(pascal: str) -> str | None:
    key = (SPECIAL.get(pascal) or to_snake(pascal)).replace("_", "-")
    return key if key in ICON_KEYS else None


MUSE_IMPORT = "import io.zer0.muse.ui.common.icons.MuseIcons"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="app/src/main/java directory")
    ap.add_argument("--apply", action="store_true", help="write changes back")
    args = ap.parse_args()
    src = Path(args.src).resolve()

    unmapped: dict[str, list[str]] = {}
    mapped = 0
    files_changed = 0
    wildcard_files: list[str] = []

    for path in sorted(src.rglob("*.kt")):
        text = path.read_text(encoding="utf-8")
        if "TablerIcons." not in text and not re.search(
            r"Icons\.(?:Default|Filled|Outlined|Rounded|AutoMirrored)|icons\.automirrored", text
        ):
            continue
        is_wildcard = "import compose.icons.tablericons.*" in text
        if is_wildcard:
            wildcard_files.append(str(path.relative_to(src)))

        new_text = text

        # automirrored 系 import 行直接删除（引用点会被替换，import 不再需要；
        # 避免 PATTERN 4 命中 import 路径中的 "icons.automirrored.*" 片段）。
        new_text = re.sub(
            r"^import [^\n]*icons\.automirrored\.[^\n]*\n", "", new_text, flags=re.M
        )

        def sub(m: re.Match) -> str:
            nonlocal mapped
            old = m.group(1)
            key = map_name(old)
            if key is None:
                unmapped.setdefault(old, []).append(str(path.relative_to(src)))
                return m.group(0)
            mapped += 1
            return f"MuseIcons.{camel(key)}"

        for pat in PATTERNS:
            new_text = pat.sub(sub, new_text)

        if is_wildcard:

            def bare_sub(m: re.Match) -> str:
                nonlocal mapped
                key = map_name(m.group(2))
                if key is None:
                    return m.group(0)
                mapped += 1
                return m.group(1) + f"MuseIcons.{camel(key)}"

            for pat in BARE_CONTEXT_PATTERNS:
                new_text = pat.sub(bare_sub, new_text)

        if new_text == text:
            continue

        lines = new_text.split("\n")
        if MUSE_IMPORT not in new_text:
            insert_at = None
            last_import = None
            for i, line in enumerate(lines):
                if line.startswith("import "):
                    last_import = i
                    if line > MUSE_IMPORT:
                        insert_at = i
                        break
            if insert_at is None:
                insert_at = (last_import + 1) if last_import is not None else 0
            lines.insert(insert_at, MUSE_IMPORT)

        cleaned: list[str] = []
        for line in lines:
            s = line.strip()
            if s == "import compose.icons.TablerIcons" and "TablerIcons." not in new_text:
                continue
            if s == "import androidx.compose.material.icons.Icons" and not re.search(
                r"Icons\.(?:Default|Filled|Outlined|Rounded|AutoMirrored)", new_text
            ):
                continue
            if s == "import compose.icons.tablericons.*" and is_wildcard:
                continue
            cleaned.append(line)
        new_text = "\n".join(cleaned)

        files_changed += 1
        if args.apply:
            path.write_text(new_text, encoding="utf-8")

    mode = "APPLIED" if args.apply else "DRY-RUN"
    print(f"[{mode}] files changed: {files_changed}; replacements: {mapped}")
    if wildcard_files:
        print(f"wildcard-import files ({len(wildcard_files)}) — 需人工处理:")
        for f in wildcard_files:
            print("  ", f)
    if unmapped:
        print(f"UNMAPPED ({len(unmapped)}):")
        for k in sorted(unmapped):
            print(f"  {k}: {len(unmapped[k])} use(s), first: {unmapped[k][0]}")


if __name__ == "__main__":
    main()
