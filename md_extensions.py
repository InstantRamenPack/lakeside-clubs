import re

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

def makeExtension(**kwargs):
    return ClubMarkdownExtension(**kwargs)
