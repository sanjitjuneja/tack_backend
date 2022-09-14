from random import randint


def generate_sms_code() -> str:
    sms_code = ""
    for _ in range(6):
        sms_code += str(randint(0, 9))
    return sms_code
