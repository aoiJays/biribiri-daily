import re
from html.parser import HTMLParser
from ..config import SOURCE_URL, API_TOKEN, WECHAT_LIST
from datetime import datetime, timedelta, timezone

DEBUG = False
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


def get_title_markdown(url, timeout=15):
    html = fetch_wechat_article(url, timeout=timeout)
    markdown, title = parse_wechat_article(html, url)
    return title, markdown



def fetch_wechat_user_articles(item):

    if DEBUG:
        with open("example/wechat/cn5eplay.json", "r", encoding="utf-8") as f:
            import json
            return json.load(f)
        
    try:

        wxid = item.get("wxid", "")
        if not wxid:
            print("[fetch_wechat_user_articles]缺少wxid")
            return None


        url = f"{SOURCE_URL}/api/weixin/get-user-post/v1?token={API_TOKEN}&wxid={wxid}"
        response = requests.get(url)
        
        # 检查响应状态码
        response.raise_for_status()
        
        # 返回 JSON 数据
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"[fetch_zhihu_column_articles]请求发生错误: {e}")
        return None
    
def check_item_keyword(item, title):
    for keyword in item.get("KEY_WORD",[]):
        if keyword.lower() in title.lower():
            return True
    return False


def parse_wechat_user_articles(item, data):

    results = []

    if not data:
        return results
    
    article_list = data.get("data", {}).get("data", [])
    if not article_list:
        return results

    for article in article_list:
        
        article_time = article.get("time", 0)
        publish_datetime = datetime.fromtimestamp(article_time, tz=timezone(timedelta(hours=8)))
        now_datetime = datetime.now(tz=timezone(timedelta(hours=8)))
        
        # 差距超过24h
        if (now_datetime - publish_datetime) > timedelta(days=1):
            print(f"[parse_wechat_user_articles] 文章过期 skipped")
            break
        
        # 同时发布的多篇文章
        articles = article.get('articles', [])
        for art in articles:
            try:
                title = art['title']
                url = art['url']
                
                # 检查文章关键词
                if not check_item_keyword(item, title):
                    print(f"[parse_wechat_user_articles] 关键词不匹配 skipped {title}")
                    continue
                
                results.append({
                    "title": title,
                    "url": url,
                    "CATEGORY": item.get("CATEGORY", "未分类"),
                })

            except Exception as e:
                print(f"[parse_wechat_user_articles] 解析列表错误 {e}")
                continue

    return results

if __name__ == "__main__":

    final_articles = []
    for item in WECHAT_LIST:
        print(f"[main] 开始处理公众号: {item.get('title','未知公众号')}")
        data = fetch_wechat_user_articles(item)
        print("[main] 数据获取完成，开始解析文章列表...")
        articles = parse_wechat_user_articles(item, data)
        final_articles.extend(articles)
        print("[main] 文章列表解析完成。")

    print(f"[main] 共获取到 {len(final_articles)} 篇文章")
    print('Start saving articles...')

    for article in final_articles:
        print("-" * 40)
        print(f"Title: {article['title']}")
        print(f"URL: {article['url']}")
        print(f"Category: {article['CATEGORY']}")
        print("-" * 40)
        try:
            title, markdown = get_title_markdown(article['url'])
            category = article.get("CATEGORY", "未分类")

            title = re.sub(r'[\\/*?:"<>|]', "", title)
            
            with open(f"output/md/{category}_wechat_{title}.md", "w", encoding="utf-8") as f:
                f.write(markdown)
            print(f"[main] 文章内容已保存: output/md/{category}_wechat_{title}.md")
        except Exception as e:
            print(f"[main] 获取保存文章内容失败 {e}")
            continue

    print('All articles have been processed.')

