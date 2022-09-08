import json


def form_websocket_message(*, model: str, action: str, obj: dict) -> str:
    template = {
        'model': model,
        'message': {
            'action': action
            # 'id': '',
            # 'object': ''
        }
    }
    if action == 'delete':
        template['message']['id'] = obj
        template['message']['object'] = None
    else:
        template['message']['id'] = obj['id']
        template['message']['object'] = obj

    response = json.dumps(template)
    return response
