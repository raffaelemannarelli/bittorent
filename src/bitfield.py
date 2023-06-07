

from typing import List


class Bitfield:
    def __init__(self, raw: bytes) -> None:
        self.raw_bytes: bytes = raw
        self.list: List[bool] = [(byte & (1 << (7 - bit))) > 0 for byte in raw for bit in range(8)]
    def has_piece(self, index: int) -> bool:
        return self.list[index]
    def add_piece(self, index: int) -> None:
        self.list[index] = True
        changed_byte: int = self.raw_bytes[index // 8] | (1 << (7 - index % 8))
        self.raw_bytes: bytes = self.raw_bytes[:(index // 8)] + bytes([changed_byte]) + self.raw_bytes[(index // 8 + 1):]
    def copy(self) -> 'Bitfield':
        return Bitfield(self.raw_bytes)