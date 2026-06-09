import logging

import mwclient

logger = logging.getLogger(__name__)


def get_category_members(
    site: mwclient.Site,
    category_title: str,
    namespace: int = 0,
    limit: int | str | None = None,
) -> list[mwclient.page.Page]:
    """
    Retrieve all members of a specified category from a MediaWiki site.
    """
    try:
        category = site.pages[category_title]
        # Use list comprehension for efficiency - consumes the generator
        members = category.members(
            prop="ids|title",
            namespace=namespace,
            sort="sortkey",
            dir="asc",
            start=None,
            end=None,
            generator=True,
        )
        return list(members)
    except mwclient.errors.APIError as e:
        logger.warning(f"API error getting category members for {category_title}: {e}")
        return []
    except KeyError as e:
        logger.warning(f"Key error in API response for {category_title}: {e}")
        return []


__all__ = [
    "get_category_members",
]
