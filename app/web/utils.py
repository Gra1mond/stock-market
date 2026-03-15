from aiohttp.web import json_response


def error_json_response(
    http_status: int, status: str, message: str, data: dict | None = None
):
    """Формирование JSON-ответа с ошибкой"""
    return json_response(
        status=http_status,
        data={"status": status, "message": message, "data": data or {}},
    )
