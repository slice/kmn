import io
import logging
import textwrap
import traceback
from contextlib import redirect_stdout

import discord
from discord.ext import commands
from discord.ext.commands import command

from kmn.checks import is_bot_admin
from kmn.cog import Cog
from kmn.formatting import codeblock

log = logging.getLogger(__name__)


class Code(commands.Converter):
    def __init__(self, *, wrap_code=False, strip_ticks=True, indent_width=4, implicit_return=False):
        """
        Code converter.

        Args:
            wrap_code: Specifies whether to wrap the resulting code in a function.
            strip_ticks: Specifies whether to strip the code of formatting-related backticks.
            indent_width: Specifies the indent width, if wrapping.
            implicit_return: Automatically adds a return statement, when wrapping code.
        """
        self.wrap_code = wrap_code
        self.strip_ticks = strip_ticks
        self.indent_width = indent_width
        self.implicit_return = implicit_return

    async def convert(self, ctx, arg: str) -> str:
        result = arg

        if self.strip_ticks:
            # remove codeblock ticks
            if result.startswith('```') and result.endswith('```'):
                result = '\n'.join(result.split('\n')[1:-1])

            # remove inline code ticks
            result = result.strip('` \n')

        if self.wrap_code:
            # wrap in a coroutine and indent
            result = 'async def func():\n' + textwrap.indent(result, ' ' * self.indent_width)

        if self.wrap_code and self.implicit_return:
            last_line = result.splitlines()[-1]

            # if the last line isn't indented and not returning, add it
            if not last_line[4:].startswith(' ') and 'return' not in last_line:
                last_line = (' ' * self.indent_width) + 'return ' + last_line[4:]

            result = '\n'.join(result.splitlines()[:-1] + [last_line])

        return result


def format_syntax_error(e: SyntaxError) -> str:
    """ Formats a SyntaxError. """
    if e.text is None:
        return '```py\n{0.__class__.__name__}: {0}\n```'.format(e)
    # display a nice arrow
    return '```py\n{0.text}{1:>{0.offset}}\n{2}: {0}```'.format(e, '^', type(e).__name__)


class Exec(Cog):
    def __init__(self, bot):
        super().__init__(bot)
        self.last_result = None
        self.previous_code = None

    async def execute(self, ctx, code):
        log.info('Eval: %s', code)

        async def upload(file_name):
            with open(file_name, 'rb') as fp:
                return await ctx.send(file=discord.File(fp))

        async def send(*args, **kwargs):
            return await ctx.send(*args, **kwargs)

        async def react(emoji):
            try:
                await ctx.message.add_reaction(emoji)
            except discord.HTTPException:
                pass

        env = {
            'bot': ctx.bot,
            'ctx': ctx,
            'msg': ctx.message,
            'guild': ctx.guild,
            'channel': ctx.channel,
            'me': ctx.message.author,

            # modules
            'discord': discord,
            'commands': commands,

            # utilities
            '_get': discord.utils.get,
            '_find': discord.utils.find,
            '_upload': upload,
            '_send': send,

            # last result
            '_': self.last_result,
            '_p': self.previous_code
        }

        env.update(globals())

        # simulated stdout
        stdout = io.StringIO()

        # define the wrapped function
        try:
            exec(compile(code, '<exec>', 'exec'), env)
        except SyntaxError as e:
            # send pretty syntax errors
            return await ctx.send(format_syntax_error(e))

        # grab the defined function
        func = env['func']

        try:
            # execute the code
            with redirect_stdout(stdout):
                ret = await func()
        except Exception:
            await react('\N{CACTUS}')

            original_traceback = traceback.format_exc(limit=7)

            # remove 1st and 2nd lines (irrelevant)
            split_traceback = original_traceback.splitlines()
            split_traceback.remove(split_traceback[1])
            split_traceback.remove(split_traceback[1])

            # send stream and what we have
            return await ctx.send(codeblock('\n'.join(split_traceback), lang='py'))

        # code was good, grab stdout
        stream = stdout.getvalue()

        await react('\N{HIBISCUS}')

        # set the last result, but only if it's not none
        if ret is not None:
            self.last_result = ret

        # form simulated stdout and repr of return value
        meat = stream + repr(ret)
        message = codeblock(meat, lang='py')

        if len(message) > 2000:
            # too long
            await ctx.send('result was too long.')
        else:
            # message was under 2k chars, just send!
            await ctx.send(message)

    @command(name='retry', hidden=True)
    @is_bot_admin()
    async def retry(self, ctx):
        """retries the previously executed code."""
        if not self.previous_code:
            return await ctx.send('no previous code.')

        await self.execute(ctx, self.previous_code)

    @command(name='eval', aliases=['exec', 'debug'], hidden=True)
    @is_bot_admin()
    async def _eval(self, ctx, *, code: Code(wrap_code=True, implicit_return=True)):
        """executes code."""

        # store previous code
        self.previous_code = code

        await self.execute(ctx, code)


def setup(bot):
    bot.add_cog(Exec(bot))
