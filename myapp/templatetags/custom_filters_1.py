from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """ 將 value 與 arg 轉成整數後相乘，失敗則回傳空字串 """
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return ''