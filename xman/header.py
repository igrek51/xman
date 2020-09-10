from typing import Dict


def get_header(headers: Dict[str, str], name: str, default_value: str) -> str:
    for header_name, header_value in headers.items():
        if header_name.lower() == name.lower():
            return header_value
    return default_value


def has_header(headers: Dict[str, str], name: str) -> bool:
    for header_name, header_value in headers.items():
        if header_name.lower() == name.lower():
            return True
    return False
