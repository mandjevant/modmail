from discord.ext import commands


# exc is an exception handler wrapper.
#  it's neat
def exc(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            return False

    return wrapper


# owner_check takes context
#  checks if user in context is an owner
#  returns boolean
@exc
def owner_check(ctx) -> bool:
    owners = [204184798200201216, 586715866129891328, 357918459058978816]

    return ctx.author.id in owners


def is_owner():
    async def wrapper(ctx):
        return owner_check(ctx)

    return commands.check(wrapper)
