def codeblock(code, *, lang=''):
    return '```{}\n{}\n```'.format(lang, code)


def format_list(items, *, format, separator='\n'):
    return separator.join(format.format(item=item) for item in items)
