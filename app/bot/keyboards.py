from collections.abc import Iterable, Sequence


def _chunked(sequence: Sequence[str], size: int) -> Iterable[Sequence[str]]:
    for i in range(0, len(sequence), size):
        yield sequence[i : i + size]


def command_keyboard() -> dict:
    return {
        "keyboard": [
            [
                {"text": "Новая игра"},
                {"text": "Старт"},
                {"text": "Присоединиться"},
            ],
            [
                {"text": "Готов"},
                {"text": "Завершить игру"},
            ],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }


def quick_order_keyboard(
    tickers: Sequence[str],
    quantities: Sequence[int] = (1,),
    include_controls: bool = True,
) -> dict:
    keyboard: list[list[dict[str, str]]] = []
    for ticker in tickers:
        buy_row = [{"text": f"Купить {ticker} x{qty}"} for qty in quantities]
        sell_row = [{"text": f"Продать {ticker} x{qty}"} for qty in quantities]
        keyboard.append(buy_row)
        keyboard.append(sell_row)
    if include_controls:
        keyboard.append([{"text": "Готов"}, {"text": "Завершить игру"}])
    if not keyboard:
        return {"keyboard": [], "resize_keyboard": True}
    return {
        "keyboard": keyboard,
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }


def stock_keyboard(tickers: Sequence[str], mode: str) -> dict:
    command = mode.lstrip("/")
    if command not in {"buy", "sell"}:
        raise ValueError("mode must be 'buy' or 'sell'")

    rows = []
    for chunk in _chunked(tickers, 3):
        row = [
            {
                "text": ticket,
                "switch_inline_query_current_chat": f"/{command} {ticket} ",
            }
            for ticket in chunk
        ]
        rows.append(row)

    if not rows:
        rows.append(
            [
                {
                    "text": f"Нет доступных акций для {command}",
                    "switch_inline_query_current_chat": f"/{command} ",
                }
            ]
        )

    return {"inline_keyboard": rows}
