import math
from typing import Any, Sequence

def paginate_sequence(
    items: Sequence[Any],
    total: int,
    limit: int = 50,
    offset: int = 0
) -> dict[str, Any]:
    """
    Standard pagination calculation supporting both offset-based and page-based conventions.
    Returns:
      rows: slice of items
      total: total items count in database
      limit: items requested per page
      offset: starting index
      page: 1-based page number
      pages: total number of pages
      has_next: boolean indicator if more items follow
      has_prev: boolean indicator if preceding items exist
      next_offset: offset for next page (or None)
      prev_offset: offset for previous page (or None)
    """
    limit = max(1, min(int(limit), 1000))
    offset = max(0, int(offset))
    page = (offset // limit) + 1
    pages = math.ceil(total / limit) if total > 0 else 1
    has_next = (offset + limit) < total
    has_prev = offset > 0
    next_offset = (offset + limit) if has_next else None
    prev_offset = max(0, offset - limit) if has_prev else None
    return {
        "rows": list(items),
        "total": total,
        "limit": limit,
        "offset": offset,
        "page": page,
        "pages": pages,
        "has_next": has_next,
        "has_prev": has_prev,
        "next_offset": next_offset,
        "prev_offset": prev_offset,
    }
