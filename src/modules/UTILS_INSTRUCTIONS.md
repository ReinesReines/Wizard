# Utils.py
This file is for utilities. Here is a step-by-step guide on how everything in `utils.py` works.

## Parsing
#### `parse_card_effect(card: Cards) -> list`
Returns the effect as a `dict` inside a `list`.

```py
dragon = SummonCard(..., effect="flying; haste")
result = parse_card_effect(dragon)
# [
#   {'trigger': None, 'action': 'static', 'status': 'flying', 'field': None, 'value': None},
#   {'trigger': None, 'action': 'static', 'status': 'haste', 'field': None, 'value': None}
# ]
```