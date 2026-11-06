from src.limits import parse_limit


def list_rows(request):
    limit = parse_limit(request.args["limit"])
    return limit
