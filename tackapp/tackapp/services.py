import json


def form_websocket_message(*, model: str, action: str, obj: dict) -> str:
    template = {
            'model': model,
            'message': {
                'action': action,
                'id': obj['id'],
                'object': obj
            }
        }
    if action == 'delete':
        template['id'] = obj
        template['object'] = None

    response = json.dumps(template)
    return response
