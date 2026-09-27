from dataclasses import dataclass, field


@dataclass
class Chunk:
    index: int
    text: str
    start_char: int
    end_char: int


class TextChunker:
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[Chunk]:
        if len(text) <= self.chunk_size:
            return [Chunk(index=0, text=text.strip(), start_char=0, end_char=len(text))]

        chunks: list[Chunk] = []
        start = 0
        idx = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end]

            last_period = chunk_text.rfind('.')
            if last_period > self.chunk_size * 0.5:
                end = start + last_period + 1
                chunk_text = text[start:end]

            chunks.append(Chunk(
                index=idx,
                text=chunk_text.strip(),
                start_char=start,
                end_char=end,
            ))
            idx += 1
            start = end - self.overlap

        return chunks
