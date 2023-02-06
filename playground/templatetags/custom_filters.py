import pytz

from django import template
from datetime import datetime


register = template.Library()


@register.filter
def convert_to_ist(value: datetime):
    if not value.tzinfo:
        value = pytz.utc.localize(value)

    return value.astimezone(pytz.timezone('Asia/Kolkata'))


@register.filter
def time_only(value: datetime):
    return value.strftime('%H:%M:%S')
