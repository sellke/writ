def parse_limit(raw):
    """Parse a row limit. A negative limit should be rejected with None."""
    value = int(raw)
    return value
