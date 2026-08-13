# ============================================================
# DAILY STATUS
# ============================================================

async def dailystatus(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    telegram_user = update.effective_user

    if not telegram_user:
        return

    user_id = telegram_user.id

    user = get_user(user_id)

    if not user:

        await update.message.reply_text(
            "⚠️ User account not found."
        )

        return

    last_daily = user.get(
        "last_daily",
        0,
    )

    if not last_daily:

        await update.message.reply_text(

            "🎁 **DAILY BONUS**\n\n"

            "✅ Your daily bonus is ready!\n\n"

            f"🎁 Reward: "
            f"{DAILY_BONUS} Points",

            parse_mode="Markdown",
        )

        return

    now = int(time.time())

    remaining = (
        86400
        - (now - int(last_daily))
    )

    if remaining <= 0:

        await update.message.reply_text(

            "🎁 **DAILY BONUS**\n\n"

            "✅ Your bonus is ready!\n\n"

            f"🎁 Reward: "
            f"{DAILY_BONUS} Points",

            parse_mode="Markdown",
        )

        return

    hours = remaining // 3600

    minutes = (
        remaining % 3600
    ) // 60

    await update.message.reply_text(

        "⏳ **DAILY BONUS**\n\n"

        "Your bonus has already been claimed.\n\n"

        "🕐 Try again after:\n"

        f"{hours} Hours "
        f"{minutes} Minutes",

        parse_mode="Markdown",
    )


# ============================================================
# MY ID
# ============================================================

async def myid(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    telegram_user = update.effective_user

    if not telegram_user:
        return

    user_id = telegram_user.id

    await update.message.reply_text(

        "🆔 **YOUR TELEGRAM ID**\n\n"
        f"`{user_id}`",

        parse_mode="Markdown",
    )


# ============================================================
# VERIFY JOIN
# ============================================================

async def verify_join(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    user_id = query.from_user.id

    user = get_user(user_id)

    if not user:

        await query.edit_message_text(
            "⚠️ User account not found."
        )

        return

    if user.get(
        "banned",
        False,
    ):

        await query.edit_message_text(
            "🚫 Your account has been banned."
        )

        return

    not_joined = await check_force_join(
        user_id,
        context,
    )

    if not_joined:

        await query.edit_message_text(

            "❌ **JOIN NOT COMPLETED**\n\n"

            "You still haven't joined all "
            "required groups.\n\n"

            "Join all groups and press "
            "✅ Verify Join again.",

            reply_markup=force_join_menu(),

            parse_mode="Markdown",
        )

        return

    # --------------------------------------------------------
    # One-time group reward
    # --------------------------------------------------------

    group_reward_given = user.get(
        "group_reward",
        False,
    )

    reward_text = ""

    if not group_reward_given:

        current_balance = user.get(
            "balance",
            0,
        )

        current_xp = user.get(
            "xp",
            0,
        )

        new_balance = (
            current_balance
            + GROUP_JOIN_REWARD
        )

        new_xp = (
            current_xp
            + DAILY_XP
        )

        update_user(
            user_id,
            {
                "balance": new_balance,
                "total_earned": (
                    user.get(
                        "total_earned",
                        0,
                    )
                    + GROUP_JOIN_REWARD
                ),
                "xp": new_xp,
                "level": calculate_level(
                    new_xp
                ),
                "rank": calculate_rank(
                    new_balance
                ),
                "group_reward": True,
            },
        )

        add_activity(
            user_id,
            (
                "Group join reward "
                f"+{GROUP_JOIN_REWARD} Points"
            ),
        )

        reward_text = (
            "\n\n🎁 Group Reward: "
            f"+{GROUP_JOIN_REWARD} Points"
        )

    await query.edit_message_text(

        "✅ **VERIFICATION SUCCESSFUL!**\n\n"

        "🎉 You can now use "
        "Unlimited Energy Bot."

        f"{reward_text}",

        reply_markup=main_menu(),

        parse_mode="Markdown",
    )


# ============================================================
# EXPORTS
# ============================================================

HANDLER_FUNCTIONS = {

    "start":
        start,

    "profile":
        profile,

    "balance":
        balance,

    "rank":
        rank,

    "stats":
        stats,

    "leaderboard":
        leaderboard_command,

    "activity":
        activity,

    "dailystatus":
        dailystatus,

    "help":
        help_command,

    "myid":
        myid,

    "verify_join":
        verify_join,
        }
