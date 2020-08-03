

# is_muted takes an int user_id and a database connection, for example bot.db_conn
#  It check if user is muted or not
#  Reason for not returning active is because if row doesn't exist
#  It returns true if user is muted, false if user isn't muted
async def is_muted(user_id: int, conn: any) -> bool:
    if await conn.fetch("SELECT * \
                         FROM modmail.muted \
                         WHERE \
                            user_id = $1 AND \
                            active = true", user_id):
        return True
    else:
        return False
