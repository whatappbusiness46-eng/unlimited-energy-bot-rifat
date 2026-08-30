# ============================================================
# PREMIUM TASKS SYSTEM
# MongoDB-persistent task storage + safe completion protection
# ============================================================

import logging
import time
from typing import Any, Dict, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import (
    db,
    get_user,
    add_balance,
    add_activity,
)

logger = logging.getLogger(__name__)

TASKS: Dict[str, Dict[str, Any]] = {}
TASK_COOLDOWN = 86400
DEFAULT_REWARD = 0

# Dedicated collections. Existing user data is not modified by this file.
tasks_collection = db["tasks"]
task_completions = db["task_completions"]

try:
    tasks_collection.create_index("id", unique=True, name="task_id_unique")
    tasks_collection.create_index(
        [("enabled", 1), ("created_at", -1)],
        name="task_enabled_created",
    )
    task_completions.create_index(
        [("user_id", 1), ("task_id", 1)],
        unique=True,
        name="task_completion_unique",
    )
except Exception:
    logger.exception("Task collection index setup warning")


def _now() -> int:
    return int(time.time())


def _safe_int(value, default=0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _get_user(user_id):
    try:
        return get_user(user_id, create=False)
    except TypeError:
        return get_user(user_id)


def _blocked(user: Optional[dict]) -> bool:
    return bool(
        not user
        or user.get("banned", False)
        or user.get("blacklisted", False)
    )


def _normalize_task(doc: dict) -> dict:
    task = dict(doc)
    task.pop("_id", None)

    task["id"] = str(task.get("id", task.get("task_id", "")))
    task["title"] = str(task.get("title", task["id"]))
    task["description"] = str(task.get("description", ""))
    task["reward"] = max(0, _safe_int(task.get("reward", 0), 0))
    task["url"] = task.get("url")
    task["cooldown"] = max(
        0,
        _safe_int(task.get("cooldown", TASK_COOLDOWN), TASK_COOLDOWN),
    )
    task["enabled"] = bool(task.get("enabled", True))

    return task


def register_task(
    task_id: str,
    title: str,
    description: str = "",
    reward: int = DEFAULT_REWARD,
    url: Optional[str] = None,
    cooldown: int = TASK_COOLDOWN,
    enabled: bool = True,
) -> bool:
    """Create or replace a persistent task."""
    task_id = str(task_id).strip()
    reward = _safe_int(reward, 0)
    cooldown = max(0, _safe_int(cooldown, TASK_COOLDOWN))

    if not task_id or reward < 0:
        return False

    now = _now()

    document = {
        "id": task_id,
        "title": str(title or task_id),
        "description": str(description or ""),
        "reward": reward,
        "url": url,
        "cooldown": cooldown,
        "enabled": bool(enabled),
        "updated_at": now,
    }

    try:
        tasks_collection.update_one(
            {"id": task_id},
            {
                "$set": document,
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )

        TASKS[task_id] = dict(document)
        return True

    except Exception:
        logger.exception("Failed to register task: %s", task_id)
        return False


def get_tasks(include_disabled: bool = False):
    """Return persistent tasks from MongoDB."""
    try:
        query = {} if include_disabled else {"enabled": True}

        result = [
            _normalize_task(doc)
            for doc in tasks_collection.find(query).sort(
                "created_at",
                1,
            )
        ]

        for task in result:
            TASKS[task["id"]] = dict(task)

        return result

    except Exception:
        logger.exception("Failed to load tasks")

        # Temporary in-memory fallback only if MongoDB is unavailable.
        return [
            dict(task)
            for task in TASKS.values()
            if include_disabled or task.get("enabled", True)
        ]


def get_task(task_id: str):
    task_id = str(task_id).strip()

    try:
        document = tasks_collection.find_one({"id": task_id})

        if document:
            task = _normalize_task(document)
            TASKS[task_id] = dict(task)
            return task

    except Exception:
        logger.exception("Failed to load task: %s", task_id)

    task = TASKS.get(task_id)
    return dict(task) if task else None


def update_task(task_id: str, **changes) -> bool:
    """Update only supported task fields."""
    task_id = str(task_id).strip()

    allowed = {
        "title",
        "description",
        "reward",
        "url",
        "cooldown",
        "enabled",
    }

    payload = {
        key: value
        for key, value in changes.items()
        if key in allowed
    }

    if not task_id or not payload:
        return False

    if "reward" in payload:
        payload["reward"] = max(
            0,
            _safe_int(payload["reward"], 0),
        )

    if "cooldown" in payload:
        payload["cooldown"] = max(
            0,
            _safe_int(payload["cooldown"], TASK_COOLDOWN),
        )

    payload["updated_at"] = _now()

    try:
        result = tasks_collection.update_one(
            {"id": task_id},
            {"$set": payload},
        )

        if result.matched_count <= 0:
            return False

        task = get_task(task_id)
        if task:
            TASKS[task_id] = task

        return True

    except Exception:
        logger.exception("Failed to update task: %s", task_id)
        return False


def delete_task(task_id: str) -> bool:
    """Delete a task. Completion history is intentionally retained."""
    task_id = str(task_id).strip()

    try:
        result = tasks_collection.delete_one({"id": task_id})
        TASKS.pop(task_id, None)
        return result.deleted_count > 0

    except Exception:
        logger.exception("Failed to delete task: %s", task_id)
        return False


def set_task_enabled(task_id: str, enabled: bool) -> bool:
    return update_task(
        task_id,
        enabled=bool(enabled),
    )


def _last_completion(user_id, task_id: str) -> int:
    try:
        record = task_completions.find_one(
            {
                "user_id": int(user_id),
                "task_id": str(task_id),
            }
        )

        if not record:
            return 0

        return _safe_int(
            record.get("completed_at", 0),
            0,
        )

    except Exception:
        logger.exception(
            "Failed to read task completion | user=%s task=%s",
            user_id,
            task_id,
        )
        return 0


def task_available(user_id, task_id: str) -> bool:
    user = _get_user(user_id)
    task = get_task(task_id)

    if _blocked(user) or not task or not task.get("enabled", True):
        return False

    last = _last_completion(
        user_id,
        task_id,
    )

    if last <= 0:
        return True

    cooldown = max(
        0,
        _safe_int(
            task.get("cooldown", TASK_COOLDOWN),
            TASK_COOLDOWN,
        ),
    )

    return _now() - last >= cooldown


def complete_task(user_id, task_id: str) -> bool:
    """
    Award a task once per cooldown window.

    The completion record is stored separately from the user document,
    avoiding the current database.py completed_tasks type mismatch.
    """
    user = _get_user(user_id)
    task = get_task(task_id)

    if _blocked(user) or not task or not task.get("enabled", True):
        return False

    if not task_available(user_id, task_id):
        return False

    user_id = int(user_id)
    task_id = str(task_id)
    now = _now()
    reward = max(
        0,
        _safe_int(task.get("reward", 0), 0),
    )

    try:
        # One-time task: unique user_id + task_id record.
        # Daily/repeating tasks are updated after cooldown.
        existing = task_completions.find_one(
            {
                "user_id": user_id,
                "task_id": task_id,
            }
        )

        if existing:
            cooldown = max(
                0,
                _safe_int(
                    task.get("cooldown", TASK_COOLDOWN),
                    TASK_COOLDOWN,
                ),
            )

            last = _safe_int(
                existing.get("completed_at", 0),
                0,
            )

            if last and now - last < cooldown:
                return False

            result = task_completions.update_one(
                {
                    "user_id": user_id,
                    "task_id": task_id,
                    "completed_at": last,
                },
                {
                    "$set": {
                        "completed_at": now,
                        "reward": reward,
                        "task_title": task["title"],
                    }
                },
            )

            if result.modified_count <= 0:
                return False

        else:
            try:
                task_completions.insert_one(
                    {
                        "user_id": user_id,
                        "task_id": task_id,
                        "completed_at": now,
                        "reward": reward,
                        "task_title": task["title"],
                    }
                )
            except Exception:
                # DuplicateKeyError/race: another click won.
                logger.info(
                    "Duplicate task completion prevented | user=%s task=%s",
                    user_id,
                    task_id,
                )
                return False

        # Credit only after the completion slot is claimed.
        if reward > 0:
            credited = add_balance(
                user_id,
                reward,
            )

            if credited is False:
                # Roll back the completion claim so the user can retry.
                task_completions.delete_one(
                    {
                        "user_id": user_id,
                        "task_id": task_id,
                        "completed_at": now,
                    }
                )
                return False

            try:
                add_activity(
                    user_id,
                    f"✅ Task completed: {task['title']}",
                    reward,
                )
            except Exception:
                logger.exception(
                    "Task activity failed | user=%s task=%s",
                    user_id,
                    task_id,
                )

        return True

    except Exception:
        logger.exception(
            "Task completion failed | user=%s task=%s",
            user_id,
            task_id,
        )
        return False


def tasks_menu(user_id=None):
    keyboard = []

    for task in get_tasks():
        task_id = task["id"]

        if user_id is not None:
            available = task_available(
                user_id,
                task_id,
            )
        else:
            available = True

        label = (
            f"🎯 {task['title']}"
            if available
            else f"⏳ {task['title']}"
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    label,
                    callback_data=f"task_{task_id}",
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "🏠 Home",
                callback_data="home",
            )
        ]
    )

    return InlineKeyboardMarkup(keyboard)


async def tasks_page(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user
    message = update.effective_message

    if not user or not message:
        return

    db_user = _get_user(user.id)

    if _blocked(db_user):
        await message.reply_text(
            "🚫 Your account is restricted."
        )
        return

    task_list = get_tasks()

    if not task_list:
        text = (
            "🎯 **TASK CENTER**\n\n"
            "No tasks are available right now.\n"
            "Please check again later."
        )

    else:
        lines = [
            "🎯 **TASK CENTER**",
            "",
            "Complete tasks to earn rewards:",
            "",
        ]

        for task in task_list:
            available = task_available(
                user.id,
                task["id"],
            )

            status = (
                "🟢 Available"
                if available
                else "⏳ Cooldown"
            )

            lines.append(
                f"{status} — {task['title']} "
                f"(+{task['reward']} Points)"
            )

        text = "\n".join(lines)

    await message.reply_text(
        text,
        reply_markup=tasks_menu(user.id),
        parse_mode="Markdown",
    )


async def task_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not query:
        return

    await query.answer()

    data = str(query.data or "")

    if not data.startswith("task_"):
        return

    # task_complete_* has its own handler.
    if data.startswith("task_complete_"):
        return

    task_id = data[len("task_"):]
    task = get_task(task_id)

    if not task:
        await query.edit_message_text(
            "⚠️ Task not found or removed.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ Tasks",
                            callback_data="tasks",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🏠 Home",
                            callback_data="home",
                        )
                    ],
                ]
            ),
        )
        return

    if not task.get("enabled", True):
        await query.edit_message_text(
            "⚠️ This task is currently disabled."
        )
        return

    if not task_available(
        query.from_user.id,
        task_id,
    ):
        await query.edit_message_text(
            "⏳ **TASK ON COOLDOWN**\n\n"
            "You have already completed this task.\n"
            "Please come back later.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ Tasks",
                            callback_data="tasks",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🏠 Home",
                            callback_data="home",
                        )
                    ],
                ]
            ),
            parse_mode="Markdown",
        )
        return

    if task.get("url"):
        keyboard = [
            [
                InlineKeyboardButton(
                    "🚀 Open Task",
                    url=str(task["url"]),
                )
            ],
            [
                InlineKeyboardButton(
                    "✅ Verify Task",
                    callback_data=f"task_complete_{task_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "🏠 Home",
                    callback_data="home",
                )
            ],
        ]

        text = (
            f"🎯 **{task['title']}**\n\n"
            f"{task['description']}\n\n"
            f"💰 Reward: {task['reward']} Points"
        )

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return

    success = complete_task(
        query.from_user.id,
        task_id,
    )

    if success:
        text = (
            "🎉 **TASK COMPLETED!**\n\n"
            f"🎯 {task['title']}\n"
            f"💰 +{task['reward']} Points"
        )
    else:
        text = (
            "⚠️ **TASK NOT COMPLETED**\n\n"
            "The task may be unavailable or already completed."
        )

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⬅️ Tasks",
                        callback_data="tasks",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🏠 Home",
                        callback_data="home",
                    )
                ],
            ]
        ),
        parse_mode="Markdown",
    )


async def task_complete_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not query:
        return

    await query.answer()

    data = str(query.data or "")

    if not data.startswith("task_complete_"):
        return

    task_id = data[len("task_complete_"):]
    task = get_task(task_id)

    if not task:
        await query.edit_message_text(
            "⚠️ Task not found."
        )
        return

    if not task.get("enabled", True):
        await query.edit_message_text(
            "⚠️ This task is disabled."
        )
        return

    success = complete_task(
        query.from_user.id,
        task_id,
    )

    if success:
        text = (
            "🎉 **VERIFIED!**\n\n"
            f"🎯 {task['title']}\n"
            f"💰 +{task['reward']} Points"
        )
    else:
        text = (
            "❌ **VERIFICATION FAILED**\n\n"
            "The task is already completed or still on cooldown."
        )

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⬅️ Tasks",
                        callback_data="tasks",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🏠 Home",
                        callback_data="home",
                    )
                ],
            ]
        ),
        parse_mode="Markdown",
    )


HANDLER_FUNCTIONS = {
    "tasks": tasks_page,
    "task_callback": task_callback,
    "task_complete_callback": task_complete_callback,
}

__all__ = [
    "TASKS",
    "TASK_COOLDOWN",
    "register_task",
    "get_tasks",
    "get_task",
    "update_task",
    "delete_task",
    "set_task_enabled",
    "task_available",
    "complete_task",
    "tasks_menu",
    "tasks_page",
    "task_callback",
    "task_complete_callback",
    "HANDLER_FUNCTIONS",
]
