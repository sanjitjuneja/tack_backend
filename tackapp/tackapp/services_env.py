def read_secrets(app: str, env_values, secret_name) -> str:
    if app == "local":
        return env_values.get_value(secret_name)
    else:
        return env_values.get(secret_name)
