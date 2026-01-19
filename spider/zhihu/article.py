from ..config import SOURCE_URL, API_TOKEN, ZHIHU_LIST

import requests
import re
from html.parser import HTMLParser
from datetime import datetime, timedelta, timezone

DEBUG = False

def fetch_zhihu_column_articles(item):

    if DEBUG:
        with open("example/zhihu/juya-column.json", "r", encoding="utf-8") as f:
            import json
            return json.load(f)
        

    try:

        column_id = item["column_id"]
        url = f"{SOURCE_URL}/api/zhihu/get-column-article-list/v1?token={API_TOKEN}&columnId={column_id}&offset=0"
        response = requests.get(url)
        
        # 检查响应状态码
        response.raise_for_status()
        
        # 返回 JSON 数据
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"[fetch_zhihu_column_articles]请求发生错误: {e}")
        return None


def parse_zhihu_column_articles(data, item):
    
    articles = data.get("data", {}).get("data", [])
    print('[parse_zhihu_column_articles]获取到文章数量:', len(articles))

    final_articles = []

    for article in articles:
        create_time = article.get("created")
        title = article.get("title")
        url = article.get("url")

        print(f"[parse_zhihu_column_articles] [Procesing]标题: {title}\n创建时间: {create_time}\n链接: {url}\n")
        try:
            # 确保两个都是东八区
            cn_tz = timezone(timedelta(hours=8))
            create_datetime = datetime.fromtimestamp(create_time, tz=cn_tz)
            current_datetime = datetime.now(tz=cn_tz)

            # 计算时间差
            time_difference = current_datetime - create_datetime

            # 判断时间差是否在一天之内
            if time_difference < timedelta(days=1):
                create_time_str = create_datetime.strftime("%Y-%m-%d %H:%M:%S")            
                current_time_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

                print(f"[parse_zhihu_column_articles]当前时间: {current_time_str} 文章时间: {create_time_str}")
            else:
                print("[parse_zhihu_column_articles] [Skipped] 过期文章")
                break
            
            if item['KEY_WORD'] not in title:
                print(f"[parse_zhihu_column_articles] [Skipped] 标题中不包含关键字: {item['KEY_WORD']}")
                continue

            final_articles.append(url)

        except Exception as e:
            print(f"[parse_zhihu_column_articles] 发生错误: {e}")

        print("[parse_zhihu_column_articles] 共获取到文章数量:", len(final_articles))
    return final_articles


def fetch_zhihu_article_content(article_pid):

    if DEBUG:
        with open("example/zhihu/juya-article.json", "r", encoding="utf-8") as f:
            import json
            return json.load(f)
        
    try:
        url = f"{SOURCE_URL}/api/zhihu/get-column-article-detail/v1?token={API_TOKEN}&id={article_pid}"
        response = requests.get(url)
        
        # 检查响应状态码
        response.raise_for_status()
        
        # 返回 JSON 数据
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"[fetch_zhihu_article_content]请求发生错误: {e}")
        return None
    
def parse_zhihu_article_content(data):
    article = data.get("data", {})
    title = article.get("title", "")
    url = article.get("url", "")
    author = article.get("author", {}).get("name", "")
    content = article.get("content", "")

    class _HTMLToMarkdown(HTMLParser):
        def __init__(self):
            super().__init__()
            self.parts = []
            self.blockquote_level = 0
            self.list_stack = []
            self.link_stack = []
            self.in_pre = False
            self.pre_buffer = []
            self.pre_lang = ""
            self.pending_line_prefix = ""
            self.at_line_start = True

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

        def handle_starttag(self, tag, attrs):
            attrs_dict = dict(attrs or [])
            if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
                self._start_block()
                level = int(tag[1])
                self.pending_line_prefix = "#" * level + " "
            elif tag == "p":
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
                href = attrs_dict.get("href", "")
                self._append("[")
                self.link_stack.append(href)
            elif tag == "img":
                src = attrs_dict.get("src", "")
                alt = attrs_dict.get("alt") or attrs_dict.get("data-caption") or ""
                self._write(f"![{alt}]({src})")

        def handle_endtag(self, tag):
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
            if self.in_pre:
                self.pre_buffer.append(data_text)
            else:
                self._write(data_text)

    parser = _HTMLToMarkdown()
    parser.feed(content)
    markdown_body = "".join(parser.parts)
    markdown_body = re.sub(r"\n{3,}", "\n\n", markdown_body).strip()

    header_lines = []
    if title:
        header_lines.append(f"# {title}")
    meta_line = " - ".join([item for item in [author, url] if item])
    if meta_line:
        header_lines.append(meta_line)
    if header_lines:
        header_lines.append("")
    header = "\n".join(header_lines)
    return f"{header}{markdown_body}".strip()


def zhihu_workflow():
    print('Zhihu Article Spider Workflow Start')
    for item in ZHIHU_LIST:
        print('Processing Column:', item.get('title'))
        data = fetch_zhihu_column_articles(item)
        print('[ok] 成功获取专栏数据')

        article_urls = parse_zhihu_column_articles(data, item)
        article_pids = [url.split("/")[-1] for url in article_urls]
        print('[ok] 成功解析专栏数据')

        final_content = ''
        for pid in article_pids:
            print(f'[Processing] 文章 PID: {pid}')
            article_data = fetch_zhihu_article_content(pid)
            print('[ok] 成功获取文章数据')

            article_content = parse_zhihu_article_content(article_data)
            print('[ok] 成功解析文章数据')
            final_content += article_content + "\n\n---\n\n"
        

        item_CATEGORY = item.get('CATEGORY')
        item_title = item.get('title')

        with open(f"output/md/{item_CATEGORY}_zhihu_{item_title}.md", "w", encoding="utf-8") as f:
            f.write(final_content.strip())
        print(f'[ok] 成功保存文章到 output/md/{item_CATEGORY}_zhihu_{item_title}.md')


if __name__ == "__main__":
    
    zhihu_workflow()