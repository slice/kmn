from copy import deepcopy
from random import uniform

import discord
from discord.ext.commands import command, group

from kmn.checks import is_bot_admin
from kmn.cog import Cog
from kmn.errors import CommandFailure
from kmn.storage import JSONStorage


class Bank:
    def __init__(self, bot):
        self.bot = bot
        self.storage = JSONStorage('_currency.json', loop=self.bot.loop)

    async def create_account(self, user):
        await self.storage.put(str(user.id), {
            'wallet': 0.00,
            'grace_period': 0,
            'last_stole': 0
        })

    async def write(self, user, amount):
        account = deepcopy(self.get_account(user))
        account['wallet'] = amount
        await self.storage.put(str(user.id), account)

    def get_account(self, user):
        account = self.storage.get(str(user.id))

        if not account:
            raise CommandFailure('you have no account, create one with `{prefix}register`.')

        return account

    async def wallet(self, user):
        return self.get_account(user)['wallet']


class Currency(Cog):
    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot
        self.bank = Bank(bot)

    @command()
    async def wallet(self, ctx, who: discord.User=None):
        """view your balance"""
        who = who or ctx.author
        balance = await self.bank.wallet(who)
        await ctx.send(f'{who} \N{RIGHTWARDS ARROW} `{balance:.2f}bc`')

    @command()
    @is_bot_admin()
    async def write(self, ctx, user: discord.User, amount: float):
        """write someone's wallet lol"""
        await self.bank.write(user, amount)
        await ctx.send(f'\N{OK HAND SIGN} {user} \N{RIGHTWARDS ARROW} `{amount:.2f}bc`')

    @command()
    async def steal(self, ctx, target: discord.User, amount: float):
        """steal some monies"""
        if target == ctx.author:
            raise CommandFailure('what')

        # cap
        if amount > 80.0:
            raise CommandFailure("you're stealing too much. `80.0bc` max pls.")

        # grab thief wallet
        thief_wallet = await self.bank.wallet(ctx.author)

        # check wallet
        target_wallet = await self.bank.wallet(target)
        if amount > target_wallet:
            raise CommandFailure("that person doesn't have the money you want. look for someone else.")

        # can't steal more than 50%
        percentage_of_steal = amount / target_wallet
        if percentage_of_steal > 0.5:
            amount = target_wallet * 0.5
            raise CommandFailure(
                f"you can't steal more than 50% of someone's wallet. the max you can steal from {target} is"
                f" `{amount:.2f}bc`."
            )

        potential = amount + min(int(amount * 1.5), 10)
        chance = uniform(0, potential)

        if amount < chance:
            await self.bank.write(target, target_wallet - amount)
            await self.bank.write(ctx.author, thief_wallet + amount)
            await ctx.send(
                f'\N{PISTOL} ouch. {ctx.author} \N{RIGHTWARDS ARROW} `{amount:.2f}bc`'
                f'\n\n[amount:`{amount}` < rolled:`{chance:.2f}`] chance = `{potential:.2f}`'
            )
        else:
            if thief_wallet == 0:
                return await ctx.send('\N{ONCOMING POLICE CAR} oops, you failed.')

            penalty = min(amount * 1.5, thief_wallet)
            percentage = penalty / thief_wallet
            await self.bank.write(ctx.author, thief_wallet - penalty)
            await ctx.send(
                f'\N{ONCOMING POLICE CAR} oops, you failed. you have lost `{penalty:.2f}bc`'
                f' ({percentage * 100:.2f}% of your total wallet).'
            )

    @command(aliases=['transfer'])
    async def send(self, ctx, target: discord.User, amount: float):
        """send someone bottlecaps"""

        if target == ctx.author:
            raise CommandFailure('what')

        wallet = await self.bank.wallet(ctx.author)

        if wallet < amount:
            raise CommandFailure("you don't have enough...")

        try:
            # grab wallet of target
            target_wallet = await self.bank.wallet(target)
        except CommandFailure:
            # target doesn't have an account.
            raise CommandFailure(f"{target} doesn't have an account. make them create one with `"
                                 f"{ctx.prefix}register`.")

        # deduct from balance
        await self.bank.write(ctx.author, wallet - amount)

        # write!
        await self.bank.write(target, target_wallet + amount)

        await ctx.send(f'\N{MONEY WITH WINGS} {ctx.author} `--[ {amount:.2f}bc ]-->` {target}')

        try:
            await target.send(
                f'\N{MONEY WITH WINGS} you got money! you have received `{amount:.2f}bc` from {ctx.author.mention}.'
            )
        except discord.HTTPException:
            pass

    @command()
    async def register(self, ctx):
        """make an account"""

        if self.bank.storage.get(str(ctx.author.id)):
            raise CommandFailure('you already have an account lol')

        # make the account
        await self.bank.create_account(ctx.author)

        await ctx.send('\N{OK HAND SIGN}')


def setup(bot):
    bot.add_cog(Currency(bot))
