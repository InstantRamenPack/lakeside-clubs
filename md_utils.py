import re

import bleach
import markdown
from flask import current_app

from markdown.extensions import Extension
from markdown.inlinepatterns import SimpleTagInlineProcessor
from markdown.preprocessors import Preprocessor

class AltImagePreprocessor(Preprocessor):
    # Allow images without alt or https://
    # ChatGPT

    IMAGE_PATTERN = re.compile(r"!\(([^)\n]+)\)")

    def run(self, lines):
        return [self.IMAGE_PATTERN.sub(self.process_image, line) for line in lines]

    @staticmethod
    def process_image(match):
        url = match.group(1).strip()
        if not url:
            return match.group(0)
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
            url = f"https://{url.lstrip('/')}"
        return f"![]({url})"

class ClubMarkdownExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(AltImagePreprocessor(md), "alt_image", 200)
        # https://github.com/honzajavorek/markdown-del-ins/blob/master/markdown_del_ins.py
        md.inlinePatterns.register(
            SimpleTagInlineProcessor(r'(\~\~)(.+?)(\~\~)', 'del'), "strikethrough", 200
        )

def render_markdown_safe(markdown_text):
    html = markdown.markdown(
        markdown_text,
        extensions = current_app.config["MD_EXTENSIONS"],
        output_format = "html5"
    )
    clean = bleach.clean(
        html,
        tags = current_app.config["ALLOWED_TAGS"],
        attributes = current_app.config["ALLOWED_ATTRS"],
        protocols = current_app.config["ALLOWED_PROTOCOLS"],
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
        protocols = current_app.config["ALLOWED_PROTOCOLS"],
        strip = True,
        strip_comments = True,
    )

def makeExtension(**kwargs):
    return ClubMarkdownExtension(**kwargs)
