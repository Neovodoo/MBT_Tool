import datetime
import json
from decimal import Decimal


class UniversalJSONEncoder(json.JSONEncoder):
    """
    Кастомный JSONEncoder, который умеет обрабатывать
    datetime, Decimal и любые иные объекты,
    не поддерживаемые стандартным JSONEncoder.
    """

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)  # или str(obj)
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)

