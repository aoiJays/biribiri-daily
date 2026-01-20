import argparse
import re
from html.parser import HTMLParser
from pathlib import Path

import requests


class _MarkdownBuilder:
    def __init__(self):
        self.parts = []
        self.blockquote_level = 0
        self.list_stack = []
        self.link_stack = []
        self.in_pre = False
        self.pre_buffer = []
        self.pre_lang = ""
        self.pending_line_prefix = ""
        self.at_line_start = True
        self.skip_data_stack = []

    def _append(self, text):
        if text:
            self.parts.append(text)

    def _start_block(self):
        if not self.parts:
            self.at_line_start = True
            return
        tail = self.parts[-1]
        if tail.endswith("\n\n"):
            self.at_line_start = True
            return
        if tail.endswith("\n"):
            self.parts.append("\n")
        else:
            self.parts.append("\n\n")
        self.at_line_start = True

    def _write(self, text):
        if not text:
            return
        lines = text.splitlines(keepends=True)
        for chunk in lines:
            if self.at_line_start:
                if self.blockquote_level > 0:
                    self.parts.append("> " * self.blockquote_level)
                if self.pending_line_prefix:
                    self.parts.append(self.pending_line_prefix)
                    self.pending_line_prefix = ""
                self.at_line_start = False
            self.parts.append(chunk)
            if chunk.endswith("\n"):
                self.at_line_start = True

    def start_tag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip_data_stack.append(tag)
            return
        attrs_dict = dict(attrs or [])
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._start_block()
            level = int(tag[1])
            self.pending_line_prefix = "#" * level + " "
        elif tag in ("p", "section"):
            self._start_block()
        elif tag == "br":
            self._append("\n")
            self.at_line_start = True
        elif tag in ("strong", "b"):
            self._append("**")
        elif tag in ("em", "i"):
            self._append("*")
        elif tag == "code":
            if self.in_pre:
                class_name = attrs_dict.get("class", "")
                match = re.search(r"language-([A-Za-z0-9_+-]+)", class_name)
                if match:
                    self.pre_lang = match.group(1)
            else:
                self._append("`")
        elif tag == "pre":
            self._start_block()
            self.in_pre = True
            self.pre_buffer = []
            self.pre_lang = ""
        elif tag == "blockquote":
            self._start_block()
            self.blockquote_level += 1
        elif tag in ("ul", "ol"):
            self._start_block()
            self.list_stack.append({"type": tag, "index": 0})
        elif tag == "li":
            if not self.at_line_start:
                self._append("\n")
            indent = "  " * max(len(self.list_stack) - 1, 0)
            if self.list_stack and self.list_stack[-1]["type"] == "ol":
                self.list_stack[-1]["index"] += 1
                bullet = f"{self.list_stack[-1]['index']}. "
            else:
                bullet = "- "
            self.pending_line_prefix = indent + bullet
            self.at_line_start = True
        elif tag == "hr":
            self._start_block()
            self._append("---")
            self._append("\n\n")
            self.at_line_start = True
        elif tag == "a":
            href = attrs_dict.get("href") or attrs_dict.get("data-src") or ""
            self._append("[")
            self.link_stack.append(href)
        elif tag == "img":
            src = attrs_dict.get("data-src") or attrs_dict.get("src") or ""
            alt = attrs_dict.get("alt") or attrs_dict.get("data-caption") or ""
            if src:
                self._write(f"![{alt}]({src})")

    def end_tag(self, tag):
        if self.skip_data_stack:
            if tag == self.skip_data_stack[-1]:
                self.skip_data_stack.pop()
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._start_block()
        elif tag == "p":
            self._start_block()
        elif tag in ("strong", "b"):
            self._append("**")
        elif tag in ("em", "i"):
            self._append("*")
        elif tag == "code":
            if not self.in_pre:
                self._append("`")
        elif tag == "pre":
            self.in_pre = False
            code = "".join(self.pre_buffer).rstrip("\n")
            lang = self.pre_lang
            fence = f"```{lang}\n{code}\n```"
            self._append(fence)
            self._append("\n\n")
            self.at_line_start = True
        elif tag == "blockquote":
            if self.blockquote_level > 0:
                self.blockquote_level -= 1
            self._start_block()
        elif tag in ("ul", "ol"):
            if self.list_stack:
                self.list_stack.pop()
            self._start_block()
        elif tag == "a":
            href = ""
            if self.link_stack:
                href = self.link_stack.pop()
            self._append(f"]({href})")

    def handle_data(self, data_text):
        if self.skip_data_stack:
            return
        if self.in_pre:
            self.pre_buffer.append(data_text)
        else:
            self._write(data_text)

    def get_markdown(self):
        markdown_body = "".join(self.parts)
        markdown_body = re.sub(r"\n{3,}", "\n\n", markdown_body).strip()
        return markdown_body


class _WechatArticleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title_parts = []
        self.author_parts = []
        self.time_parts = []
        self.in_title = False
        self.in_author = False
        self.in_time = False
        self.in_content = False
        self.content_depth = 0
        self.markdown = _MarkdownBuilder()

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs or [])
        element_id = attrs_dict.get("id", "")
        if element_id == "activity-name":
            self.in_title = True
        elif element_id == "js_name":
            self.in_author = True
        elif element_id == "publish_time":
            self.in_time = True

        if tag == "div" and element_id == "js_content":
            self.in_content = True
            self.content_depth = 1
            return

        if self.in_content:
            self.content_depth += 1
            self.markdown.start_tag(tag, attrs)

    def handle_endtag(self, tag):
        if self.in_title and tag == "h1":
            self.in_title = False
        if self.in_author and tag in ("a", "span"):
            self.in_author = False
        if self.in_time and tag in ("em", "span"):
            self.in_time = False

        if self.in_content:
            if self.content_depth == 1 and tag == "div":
                self.in_content = False
                self.content_depth = 0
                return
            self.content_depth -= 1
            self.markdown.end_tag(tag)

    def handle_data(self, data):
        text = data.strip()
        if self.in_title and text:
            self.title_parts.append(text)
        elif self.in_author and text:
            self.author_parts.append(text)
        elif self.in_time and text:
            self.time_parts.append(text)

        if self.in_content:
            self.markdown.handle_data(data)

    def get_title(self):
        return " ".join(self.title_parts).strip()

    def get_author(self):
        return " ".join(self.author_parts).strip()

    def get_publish_time(self):
        return " ".join(self.time_parts).strip()


def _sanitize_filename(name):
    safe = re.sub(r'[\\/:*?"<>|]+', "_", name)
    safe = re.sub(r"\s+", " ", safe).strip()
    return safe or "wechat_article"


def fetch_wechat_article(url, timeout=15):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    if not response.encoding:
        response.encoding = "utf-8"
    return response.text


def parse_wechat_article(html, url):
    parser = _WechatArticleParser()
    parser.feed(html)
    title = parser.get_title()
    author = parser.get_author()
    publish_time = parser.get_publish_time()
    body = parser.markdown.get_markdown()

    header_lines = []
    if title:
        header_lines.append(f"# {title}")
    meta_line = " - ".join([item for item in [author, publish_time, url] if item])
    if meta_line:
        header_lines.append(meta_line)
    if header_lines:
        header_lines.append("")
    header = "\n".join(header_lines)
    return f"{header}{body}".strip(), title


def main():
    parser = argparse.ArgumentParser(description="抓取微信公众号文章并输出 Markdown")
    parser.add_argument("url", help="微信公众号文章 URL")
    parser.add_argument(
        "-o",
        "--output-dir",
        default="spider/wechat/output",
        help="输出目录",
    )
    parser.add_argument("--timeout", type=int, default=15, help="请求超时(秒)")
    args = parser.parse_args()

    html = fetch_wechat_article(args.url, timeout=args.timeout)
    markdown, title = parse_wechat_article(html, args.url)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = _sanitize_filename(title) + ".md"
    output_path = output_dir / filename
    output_path.write_text(markdown, encoding="utf-8")
    print(f"[ok] 已保存: {output_path}")

    print(markdown)

if __name__ == "__main__":
    main()
