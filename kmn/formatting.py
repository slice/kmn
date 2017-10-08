from discord import Embed


def codeblock(code, *, lang=''):
    return '```{}\n{}\n```'.format(lang, code)


def describe(thing):
    return f'{thing} (`{thing.id}`)'


class KmnEmbed(Embed):
    def add_fields(self, *fields, inline=False):
        for name, value in fields:
            self.add_field(name=name, value=value, inline=inline)

    def add_blank_field(self):
        self.add_field(name='\u200b', value='\u200b')


def format_list(items, *, format, separator='\n'):
    return separator.join(format.format(item=item) for item in items)
