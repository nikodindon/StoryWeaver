"""Text normalization for book content."""
import re


class TextCleaner:
    def clean(self, text: str) -> str:
        # Normalize whitespace
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        # Remove common epub artifacts
        text = re.sub(r'\[Illustration[^\]]*\]', '', text)
        text = re.sub(r'\* \* \*', '\n\n', text)
        return text.strip()
