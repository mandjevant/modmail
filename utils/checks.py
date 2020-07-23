from discord.ext import commands


def exc(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            return False

    return wrapper


@exc
def owner_check(ctx):
    owners = [204184798200201216, 586715866129891328, 357918459058978816]

    return ctx.author.id in owners


def is_owner():
    def wrapper(ctx):
        return owner_check(ctx)

    return commands.check(wrapper)
