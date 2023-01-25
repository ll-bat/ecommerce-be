from typing import Dict, List

from rest_framework.exceptions import ErrorDetail


def normalize_serializer_errors(errors: Dict[str, List[ErrorDetail]]):
    return {
        field: str(errors_list[0] if len(errors_list) else None)
        for field, errors_list in errors.items()
    }
