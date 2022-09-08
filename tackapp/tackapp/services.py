import json


def form_websocket_message(*, model: str, action: str, obj: dict) -> str:
    return json.dumps(
        {
            'model': model,
            'message': {
                'action': action,
                'id': obj['id'],
                'object': obj
            }
        }
    )
