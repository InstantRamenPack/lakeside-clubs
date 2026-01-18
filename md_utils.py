import re

import bleach
import markdown

from app import app

from markdown.extensions import Extension
from markdown.inlinepatterns import SimpleTagInlineProcessor
from markdown.preprocessors import Preprocessor

class EnsureHttpsPreprocessor(Preprocessor):
    LINK_PATTERN = re.compile(r"(!?\[[^\]]*\]\()([^)\s]+)([^)]*)\)")
    ALT_IMAGE_PATTERN = re.compile(r"(!\()([^)\s]+)([^)]*)\)")
    SCHEME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")
    SCHEMELESS_PROTOCOLS_PATTERN = re.compile(r"^(?:mailto|tel|data):", re.IGNORECASE)
    RELATIVE_PATTERN = re.compile(r"^(?:/|\\./|\\.\\./|#)")

    def run(self, lines):
        return [self.process_line(line) for line in lines]

    def process_line(self, line):
        line = self.LINK_PATTERN.sub(self._replace_url, line)
        return self.ALT_IMAGE_PATTERN.sub(self._replace_url, line)

    def _replace_url(self, match):
        url = match.group(2).strip()
        if not url:
            return match.group(0)
        fixed_url = self.ensure_https(url)
        return f"{match.group(1)}{fixed_url}{match.group(3)})"

    @classmethod
    def ensure_https(cls, url):
        if cls.SCHEME_PATTERN.match(url) or cls.SCHEMELESS_PROTOCOLS_PATTERN.match(url):
            return url
        if url.startswith("//"):
            return f"https://{url.lstrip('/')}"
        if cls.RELATIVE_PATTERN.match(url):
            return url
        return f"https://{url}"

class AltImagePreprocessor(Preprocessor):
    # Allow images without alt
    # ChatGPT

    IMAGE_PATTERN = re.compile(r"!\(([^)\n]+)\)")

    def run(self, lines):
        return [self.IMAGE_PATTERN.sub(self.process_image, line) for line in lines]

    @staticmethod
    def process_image(match):
        url = match.group(1).strip()
        if not url:
            return match.group(0)
        return f"![]({url})"

class ClubMarkdownExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(EnsureHttpsPreprocessor(md), "ensure_https", 210)
        md.preprocessors.register(AltImagePreprocessor(md), "alt_image", 200)
        # https://github.com/honzajavorek/markdown-del-ins/blob/master/markdown_del_ins.py
        md.inlinePatterns.register(
            SimpleTagInlineProcessor(r'(\~\~)(.+?)(\~\~)', 'del'), "strikethrough", 200
        )

def render_markdown_safe(markdown_text):
    html = markdown.markdown(
        markdown_text,
        extensions = app.config["MD_EXTENSIONS"],
        output_format = "html5"
    )
    clean = bleach.clean(
        html,
        tags = app.config["ALLOWED_TAGS"],
        attributes = app.config["ALLOWED_ATTRS"],
        protocols = app.config["ALLOWED_PROTOCOLS"],
        strip = True,
        strip_comments = True,
    )
    clean = bleach.linkify(clean, skip_tags = ["code", "pre"])
    return clean

def render_markdown_plain(markdown_text):
    html = render_markdown_safe(markdown_text)
    return bleach.clean(
        html,
        tags = [],
        attributes = {},
        protocols = app.config["ALLOWED_PROTOCOLS"],
        strip = True,
        strip_comments = True,
    )

def makeExtension(**kwargs):
    return ClubMarkdownExtension(**kwargs)
