from dataclasses import dataclass


@dataclass
class PageMeta:
    page: int
    page_size: int
    total: int

    @property
    def total_pages(self) -> int:
        if self.total == 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size


def to_offset(page: int, page_size: int) -> int:
    return (page - 1) * page_size


def build_page_meta(page: int, page_size: int, total: int) -> dict:
    meta = PageMeta(page=page, page_size=page_size, total=total)
    return {
        "page": meta.page,
        "page_size": meta.page_size,
        "total": meta.total,
        "total_pages": meta.total_pages,
    }
