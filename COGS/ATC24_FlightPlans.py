import asyncio
import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("FLIGHTPLAN_DB_PATH", "flightplans.db")
REVIEW_CHANNEL_ID = int(os.getenv("FLIGHTPLAN_REVIEW_CHANNEL_ID", "0") or 0)
LOG_CHANNEL_ID = int(os.getenv("FLIGHTPLAN_LOG_CHANNEL_ID", "0") or 0)
DISPATCHER_ROLE_ID = int(os.getenv("DISPATCHER_ROLE_ID", "0") or 0)
JUNIOR_FO_ROLE_ID = int(os.getenv("JUNIOR_FO_ROLE_ID", "0") or 0)
SENIOR_FO_ROLE_ID = int(os.getenv("SENIOR_FO_ROLE_ID", "0") or 0)
JUNIOR_CAPTAIN_ROLE_ID = int(os.getenv("JUNIOR_CAPTAIN_ROLE_ID", "0") or 0)
SFO_ROLE_ID = int(os.getenv("SFO_ROLE_ID", "0") or 0)

PILOT_RANKS = (
    ("Junior F/O", JUNIOR_FO_ROLE_ID),
    ("Senior F/O", SENIOR_FO_ROLE_ID),
    ("Junior Captain", JUNIOR_CAPTAIN_ROLE_ID),
    ("SFO", SFO_ROLE_ID),
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utcnow().isoformat()


class FlightPlanDB:
    """Small SQLite persistence layer used exclusively by the flight-plan system."""

    def __init__(self, path: str):
        self.path = path
        self.lock = asyncio.Lock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def _initialize(self) -> None:
        conn = self._connect()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    discord_user_id INTEGER PRIMARY KEY,
                    approved_flights INTEGER NOT NULL DEFAULT 0,
                    written_exam_passed INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS flight_submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_user_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    departure TEXT NOT NULL,
                    arrival TEXT NOT NULL,
                    flight_number TEXT NOT NULL,
                    aircraft TEXT NOT NULL,
                    screenshot_url TEXT NOT NULL,
                    screenshot_filename TEXT,
                    notes TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    rejection_reason TEXT,
                    dispatcher_id INTEGER,
                    submitted_at TEXT NOT NULL,
                    reviewed_at TEXT,
                    review_message_id INTEGER,
                    review_channel_id INTEGER,
                    FOREIGN KEY(discord_user_id) REFERENCES users(discord_user_id)
                );

                CREATE TABLE IF NOT EXISTS exams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_user_id INTEGER NOT NULL,
                    exam_type TEXT NOT NULL,
                    passed INTEGER NOT NULL DEFAULT 0,
                    score REAL,
                    completed_at TEXT NOT NULL,
                    reviewed_by INTEGER,
                    FOREIGN KEY(discord_user_id) REFERENCES users(discord_user_id)
                );

                CREATE INDEX IF NOT EXISTS idx_flight_status ON flight_submissions(status);
                CREATE INDEX IF NOT EXISTS idx_flight_user ON flight_submissions(discord_user_id);
                CREATE UNIQUE INDEX IF NOT EXISTS idx_obvious_duplicate_flight
                    ON flight_submissions(discord_user_id, departure, arrival, flight_number, aircraft, screenshot_url);
                """
            )
        finally:
            conn.close()

    async def ensure_user(self, user_id: int) -> None:
        now = iso_now()
        async with self.lock:
            conn = self._connect()
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO users(discord_user_id, created_at, updated_at) VALUES (?, ?, ?)",
                    (user_id, now, now),
                )
            finally:
                conn.close()

    async def create_submission(self, data: dict) -> int:
        await self.ensure_user(data["discord_user_id"])
        async with self.lock:
            conn = self._connect()
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO flight_submissions
                    (discord_user_id, guild_id, departure, arrival, flight_number, aircraft,
                     screenshot_url, screenshot_filename, notes, status, submitted_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                    """,
                    (
                        data["discord_user_id"], data["guild_id"], data["departure"], data["arrival"],
                        data["flight_number"], data["aircraft"], data["screenshot_url"],
                        data.get("screenshot_filename"), data.get("notes"), iso_now(),
                    ),
                )
                return int(cursor.lastrowid)
            except sqlite3.IntegrityError as exc:
                raise ValueError("duplicate") from exc
            finally:
                conn.close()

    async def get_submission(self, submission_id: int) -> Optional[sqlite3.Row]:
        async with self.lock:
            conn = self._connect()
            try:
                return conn.execute(
                    "SELECT * FROM flight_submissions WHERE id = ?", (submission_id,)
                ).fetchone()
            finally:
                conn.close()

    async def pending_submission_ids(self) -> list[int]:
        async with self.lock:
            conn = self._connect()
            try:
                return [
                    int(row["id"])
                    for row in conn.execute(
                        "SELECT id FROM flight_submissions WHERE status = 'pending' ORDER BY id"
                    ).fetchall()
                ]
            finally:
                conn.close()

    async def reviewed_submission_ids(self) -> list[int]:
        """Return reviewed submissions that still have a stored Discord review message."""
        async with self.lock:
            conn = self._connect()
            try:
                return [
                    int(row["id"])
                    for row in conn.execute(
                        """
                        SELECT id FROM flight_submissions
                        WHERE status IN ('approved', 'rejected')
                          AND review_message_id IS NOT NULL
                        ORDER BY id
                        """
                    ).fetchall()
                ]
            finally:
                conn.close()

    async def set_review_message(self, submission_id: int, message_id: int, channel_id: int) -> None:
        async with self.lock:
            conn = self._connect()
            try:
                conn.execute(
                    "UPDATE flight_submissions SET review_message_id=?, review_channel_id=? WHERE id=?",
                    (message_id, channel_id, submission_id),
                )
            finally:
                conn.close()

    async def approve_submission(self, submission_id: int, dispatcher_id: int) -> Optional[dict]:
        """Atomically claim a pending submission and increment the flight count exactly once."""
        async with self.lock:
            conn = self._connect()
            try:
                conn.execute("BEGIN IMMEDIATE")
                row = conn.execute(
                    "SELECT * FROM flight_submissions WHERE id = ?", (submission_id,)
                ).fetchone()
                if row is None or row["status"] != "pending":
                    conn.rollback()
                    return None

                reviewed_at = iso_now()
                conn.execute(
                    """
                    UPDATE flight_submissions
                    SET status='approved', dispatcher_id=?, reviewed_at=?
                    WHERE id=? AND status='pending'
                    """,
                    (dispatcher_id, reviewed_at, submission_id),
                )
                if conn.execute("SELECT changes()").fetchone()[0] != 1:
                    conn.rollback()
                    return None

                conn.execute(
                    "UPDATE users SET approved_flights = approved_flights + 1, updated_at=? WHERE discord_user_id=?",
                    (reviewed_at, row["discord_user_id"]),
                )
                user = conn.execute(
                    "SELECT * FROM users WHERE discord_user_id=?", (row["discord_user_id"],)
                ).fetchone()
                conn.commit()
                return {**dict(row), **dict(user), "reviewed_at": reviewed_at, "dispatcher_id": dispatcher_id}
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    async def reject_submission(self, submission_id: int, dispatcher_id: int, reason: str) -> Optional[dict]:
        async with self.lock:
            conn = self._connect()
            try:
                conn.execute("BEGIN IMMEDIATE")
                row = conn.execute(
                    "SELECT * FROM flight_submissions WHERE id = ?", (submission_id,)
                ).fetchone()
                if row is None or row["status"] != "pending":
                    conn.rollback()
                    return None
                reviewed_at = iso_now()
                cursor = conn.execute(
                    """
                    UPDATE flight_submissions
                    SET status='rejected', dispatcher_id=?, reviewed_at=?, rejection_reason=?
                    WHERE id=? AND status='pending'
                    """,
                    (dispatcher_id, reviewed_at, reason, submission_id),
                )
                if cursor.rowcount != 1:
                    conn.rollback()
                    return None
                conn.commit()
                return {**dict(row), "reviewed_at": reviewed_at, "dispatcher_id": dispatcher_id, "rejection_reason": reason}
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    async def get_profile(self, user_id: int) -> Optional[sqlite3.Row]:
        await self.ensure_user(user_id)
        async with self.lock:
            conn = self._connect()
            try:
                return conn.execute("SELECT * FROM users WHERE discord_user_id=?", (user_id,)).fetchone()
            finally:
                conn.close()

    async def set_exam_passed(self, user_id: int, reviewer_id: int, score: Optional[float] = None) -> None:
        now = iso_now()
        await self.ensure_user(user_id)
        async with self.lock:
            conn = self._connect()
            try:
                conn.execute("BEGIN IMMEDIATE")
                conn.execute(
                    "UPDATE users SET written_exam_passed=1, updated_at=? WHERE discord_user_id=?",
                    (now, user_id),
                )
                conn.execute(
                    "INSERT INTO exams(discord_user_id, exam_type, passed, score, completed_at, reviewed_by) VALUES (?, 'sfo', 1, ?, ?, ?)",
                    (user_id, score, now, reviewer_id),
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    async def all_user_ids(self) -> list[int]:
        async with self.lock:
            conn = self._connect()
            try:
                return [int(r["discord_user_id"]) for r in conn.execute("SELECT discord_user_id FROM users").fetchall()]
            finally:
                conn.close()

    async def find_duplicate(self, user_id: int, departure: str, arrival: str, flight_number: str, aircraft: str, screenshot_url: str) -> bool:
        async with self.lock:
            conn = self._connect()
            try:
                row = conn.execute(
                    """
                    SELECT 1 FROM flight_submissions
                    WHERE discord_user_id=? AND departure=? AND arrival=? AND flight_number=? AND aircraft=? AND screenshot_url=?
                    LIMIT 1
                    """,
                    (user_id, departure, arrival, flight_number, aircraft, screenshot_url),
                ).fetchone()
                return row is not None
            finally:
                conn.close()


class RejectModal(discord.ui.Modal, title="Reject Flight Plan"):
    reason = discord.ui.TextInput(
        label="Rejection reason",
        placeholder="Explain why the proof or flight cannot be approved.",
        style=discord.TextStyle.paragraph,
        min_length=3,
        max_length=1000,
        required=True,
    )

    def __init__(self, cog: "FlightPlans", submission_id: int):
        super().__init__(timeout=300)
        self.cog = cog
        self.submission_id = submission_id

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.handle_rejection(interaction, self.submission_id, self.reason.value.strip())


class ReviewView(discord.ui.View):
    def __init__(self, cog: "FlightPlans", submission_id: int, disabled: bool = False, show_delete: bool = False):
        super().__init__(timeout=None)
        self.cog = cog
        self.submission_id = submission_id

        approve = discord.ui.Button(
            label="Approve",
            style=discord.ButtonStyle.success,
            emoji="✅",
            custom_id=f"flightplan:approve:{submission_id}",
            disabled=disabled,
        )
        reject = discord.ui.Button(
            label="Reject",
            style=discord.ButtonStyle.danger,
            emoji="❌",
            custom_id=f"flightplan:reject:{submission_id}",
            disabled=disabled,
        )
        approve.callback = self.approve
        reject.callback = self.reject
        self.add_item(approve)
        self.add_item(reject)

        # Reviewed submissions get a separate cleanup button. Deleting the
        # Discord review message does NOT delete the database/audit record.
        if show_delete:
            delete = discord.ui.Button(
                label="Delete",
                style=discord.ButtonStyle.danger,
                emoji="🗑️",
                custom_id=f"flightplan:delete:{submission_id}",
            )
            delete.callback = self.delete
            self.add_item(delete)

    async def approve(self, interaction: discord.Interaction):
        await self.cog.handle_approval(interaction, self.submission_id)

    async def reject(self, interaction: discord.Interaction):
        await self.cog.handle_reject_button(interaction, self.submission_id)

    async def delete(self, interaction: discord.Interaction):
        await self.cog.handle_delete_review(interaction, self.submission_id)


class FlightPlans(commands.Cog):
    """ATC24-only flight proof, dispatcher review, and pilot rank system."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = FlightPlanDB(DB_PATH)

    def is_dispatcher(self, member: discord.Member) -> bool:
        return bool(DISPATCHER_ROLE_ID and any(role.id == DISPATCHER_ROLE_ID for role in member.roles))

    def command_channel_ok(self, interaction: discord.Interaction) -> bool:
        return bool(REVIEW_CHANNEL_ID and interaction.channel_id == REVIEW_CHANNEL_ID)

    async def cog_load(self):
        # Re-register persistent views after a bot restart.
        for submission_id in await self.db.pending_submission_ids():
            self.bot.add_view(ReviewView(self, submission_id))
        for submission_id in await self.db.reviewed_submission_ids():
            self.bot.add_view(ReviewView(self, submission_id, disabled=True, show_delete=True))

    def rank_for(self, flights: int, exam_passed: bool) -> tuple[str, Optional[int]]:
        if flights >= 35 and exam_passed:
            return "SFO", SFO_ROLE_ID
        if flights >= 30:
            return "Junior Captain", JUNIOR_CAPTAIN_ROLE_ID
        if flights >= 20:
            return "Senior F/O", SENIOR_FO_ROLE_ID
        if flights >= 1:
            return "Junior F/O", JUNIOR_FO_ROLE_ID
        return "Unranked", None

    def next_rank_info(self, flights: int, exam_passed: bool) -> tuple[str, int]:
        if flights < 1:
            return "Junior F/O", 1 - flights
        if flights < 20:
            return "Senior F/O", 20 - flights
        if flights < 30:
            return "Junior Captain", 30 - flights
        if flights < 35:
            return "SFO", 35 - flights
        if not exam_passed:
            return "SFO (written exam required)", 0
        return "SFO", 0

    async def sync_member_rank(self, member: discord.Member, flights: int, exam_passed: bool) -> str:
        rank_name, rank_role_id = self.rank_for(flights, exam_passed)
        configured_ids = {role_id for _, role_id in PILOT_RANKS if role_id}
        rank_role = member.guild.get_role(rank_role_id) if rank_role_id else None

        if rank_role_id and rank_role is None:
            print(f"[FlightPlans] Missing configured rank role {rank_role_id} for guild {member.guild.id}")

        remove_roles = [r for r in member.roles if r.id in configured_ids and (not rank_role_id or r.id != rank_role_id)]
        try:
            if remove_roles:
                await member.remove_roles(*remove_roles, reason="ATC24 pilot rank synchronization")
            if rank_role and rank_role not in member.roles:
                await member.add_roles(rank_role, reason="ATC24 pilot rank synchronization")
        except discord.HTTPException as exc:
            print(f"[FlightPlans] Failed to sync rank for {member.id}: {exc}")

        return rank_name

    async def fetch_channel(self, channel_id: int) -> Optional[discord.abc.Messageable]:
        if not channel_id:
            return None
        channel = self.bot.get_channel(channel_id)
        if channel:
            return channel
        try:
            return await self.bot.fetch_channel(channel_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return None

    async def send_log(self, embed: discord.Embed) -> None:
        channel = await self.fetch_channel(LOG_CHANNEL_ID)
        if channel:
            try:
                await channel.send(embed=embed)
            except discord.HTTPException as exc:
                print(f"[FlightPlans] Could not send log: {exc}")

    def build_review_embed(self, row: sqlite3.Row) -> discord.Embed:
        embed = discord.Embed(title="✈️ NEW FLIGHT PLAN", color=discord.Color.gold(), timestamp=datetime.fromisoformat(row["submitted_at"]))
        embed.add_field(name="Flight Plan", value=f"`#{row['id']}`", inline=True)
        embed.add_field(name="Pilot", value=f"<@{row['discord_user_id']}> (`{row['discord_user_id']}`)", inline=True)
        embed.add_field(name="Flight", value=f"`{row['flight_number']}`", inline=True)
        embed.add_field(name="Route", value=f"`{row['departure']}` → `{row['arrival']}`", inline=True)
        embed.add_field(name="Aircraft", value=f"`{row['aircraft']}`", inline=True)
        embed.add_field(name="Status", value="🟡 Pending Approval", inline=True)
        if row["notes"]:
            embed.add_field(name="Notes", value=row["notes"][:1024], inline=False)
        embed.set_image(url=row["screenshot_url"])
        embed.set_footer(text="ATC24 proof review • Screenshot is the primary proof")
        return embed

    @app_commands.command(name="flightplan", description="Submit an ATC24 flight for dispatcher approval")
    @app_commands.describe(
        departure="ATC24 departure airport",
        arrival="ATC24 arrival airport",
        flight_number="Flight number",
        aircraft="Aircraft type",
        screenshot="Mandatory screenshot/proof of the ATC24 flight",
        notes="Optional additional notes",
    )
    async def flightplan(
        self,
        interaction: discord.Interaction,
        departure: str,
        arrival: str,
        flight_number: str,
        aircraft: str,
        screenshot: discord.Attachment,
        notes: Optional[str] = None,
    ):
        if interaction.guild is None:
            await interaction.response.send_message("❌ This command can only be used inside the ATC24 community server.", ephemeral=True)
            return
        if not self.command_channel_ok(interaction):
            await interaction.response.send_message(
                f"❌ `/flightplan` can only be used in <#{REVIEW_CHANNEL_ID}>.", ephemeral=True
            )
            return
        if not screenshot.content_type or not screenshot.content_type.startswith("image/"):
            await interaction.response.send_message("❌ The screenshot must be a Discord image attachment (PNG, JPG, WEBP, etc.).", ephemeral=True)
            return

        values = [departure.strip(), arrival.strip(), flight_number.strip(), aircraft.strip()]
        if not all(values):
            await interaction.response.send_message("❌ Departure, arrival, flight number, and aircraft are required.", ephemeral=True)
            return
        if len(departure) > 100 or len(arrival) > 100 or len(flight_number) > 50 or len(aircraft) > 50 or (notes and len(notes) > 1000):
            await interaction.response.send_message("❌ One or more fields are too long.", ephemeral=True)
            return

        if await self.db.find_duplicate(interaction.user.id, *values, screenshot.url):
            await interaction.response.send_message("❌ This exact flight submission has already been submitted.", ephemeral=True)
            return

        try:
            submission_id = await self.db.create_submission({
                "discord_user_id": interaction.user.id,
                "guild_id": interaction.guild.id,
                "departure": values[0].upper(),
                "arrival": values[1].upper(),
                "flight_number": values[2].upper(),
                "aircraft": values[3].upper(),
                "screenshot_url": screenshot.url,
                "screenshot_filename": screenshot.filename,
                "notes": notes.strip() if notes else None,
            })
        except ValueError:
            await interaction.response.send_message("❌ This flight submission is already recorded.", ephemeral=True)
            return

        row = await self.db.get_submission(submission_id)
        review_channel = await self.fetch_channel(REVIEW_CHANNEL_ID)
        if review_channel is None:
            await interaction.response.send_message("⚠️ Your submission was saved, but the dispatcher review channel is not configured or cannot be accessed. Please contact an administrator.", ephemeral=True)
            return

        try:
            message = await review_channel.send(embed=self.build_review_embed(row), view=ReviewView(self, submission_id))
            await self.db.set_review_message(submission_id, message.id, review_channel.id)
        except discord.HTTPException as exc:
            print(f"[FlightPlans] Failed to post review request #{submission_id}: {exc}")
            await interaction.response.send_message("⚠️ Your submission was saved, but Discord could not post the review request. An administrator should inspect the logs.", ephemeral=True)
            return

        await self.send_log(discord.Embed(
            title="📨 Flight Plan Submitted",
            description=f"Flight Plan `#{submission_id}` is pending dispatcher review.",
            color=discord.Color.blurple(),
            timestamp=utcnow(),
        ).add_field(name="Pilot", value=f"<@{interaction.user.id}>", inline=True).add_field(name="Flight", value=f"`{values[2].upper()}`", inline=True).add_field(name="Route", value=f"`{values[0].upper()}` → `{values[1].upper()}`", inline=True).add_field(name="Screenshot", value=screenshot.url, inline=False))

        await interaction.response.send_message(
            f"✅ Flight plan submitted successfully.\n\n**Flight Plan ID:** `#{submission_id}`\n**Status:** 🟡 Pending Dispatcher Approval",
            ephemeral=True,
        )

    async def dispatcher_check(self, interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member) or not self.is_dispatcher(interaction.user):
            if interaction.response.is_done():
                await interaction.followup.send("❌ Only members with the Dispatcher role can review flight plans.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Only members with the Dispatcher role can review flight plans.", ephemeral=True)
            return False
        return True

    async def handle_reject_button(self, interaction: discord.Interaction, submission_id: int):
        if not await self.dispatcher_check(interaction):
            return
        row = await self.db.get_submission(submission_id)
        if not row or row["status"] != "pending":
            await interaction.response.send_message("⚠️ This flight plan has already been reviewed.", ephemeral=True)
            return
        await interaction.response.send_modal(RejectModal(self, submission_id))

    async def handle_rejection(self, interaction: discord.Interaction, submission_id: int, reason: str):
        if not await self.dispatcher_check(interaction):
            return
        result = await self.db.reject_submission(submission_id, interaction.user.id, reason)
        if result is None:
            await interaction.response.send_message("⚠️ This flight plan was already reviewed by another dispatcher.", ephemeral=True)
            return

        await self.update_review_message(submission_id, "rejected", interaction.user, result)
        await self.notify_pilot(result, approved=False)
        await self.send_log(self.decision_log_embed(result, interaction.user, approved=False))
        await interaction.response.send_message(f"❌ Flight Plan `#{submission_id}` rejected and logged.", ephemeral=True)

    async def handle_approval(self, interaction: discord.Interaction, submission_id: int):
        if not await self.dispatcher_check(interaction):
            return
        row = await self.db.get_submission(submission_id)
        if not row or row["status"] != "pending":
            await interaction.response.send_message("⚠️ This flight plan has already been reviewed.", ephemeral=True)
            return
        if row["discord_user_id"] == interaction.user.id:
            await interaction.response.send_message("❌ You cannot approve your own flight submission.", ephemeral=True)
            return

        result = await self.db.approve_submission(submission_id, interaction.user.id)
        if result is None:
            await interaction.response.send_message("⚠️ This flight plan was already reviewed by another dispatcher.", ephemeral=True)
            return

        member = interaction.guild.get_member(result["discord_user_id"]) if interaction.guild else None
        rank = "Unranked"
        if member:
            rank = await self.sync_member_rank(member, result["approved_flights"], bool(result["written_exam_passed"]))
        else:
            print(f"[FlightPlans] Pilot {result['discord_user_id']} is no longer in the guild; flight remains approved.")

        result["rank"] = rank
        await self.update_review_message(submission_id, "approved", interaction.user, result)
        await self.notify_pilot(result, approved=True)
        await self.send_log(self.decision_log_embed(result, interaction.user, approved=True))
        await interaction.response.send_message(f"✅ Flight Plan `#{submission_id}` approved. Approved flights: **{result['approved_flights']}** • Rank: **{rank}**", ephemeral=True)

    async def update_review_message(self, submission_id: int, status: str, dispatcher: discord.Member, result: dict):
        channel = await self.fetch_channel(result.get("review_channel_id") or REVIEW_CHANNEL_ID)
        message_id = result.get("review_message_id")
        if not channel or not message_id:
            return
        try:
            message = await channel.fetch_message(message_id)
            embed = discord.Embed(
                title="✈️ FLIGHT PLAN REVIEWED",
                color=discord.Color.green() if status == "approved" else discord.Color.red(),
                timestamp=utcnow(),
            )
            embed.add_field(name="Flight Plan", value=f"`#{submission_id}`", inline=True)
            embed.add_field(name="Pilot", value=f"<@{result['discord_user_id']}>", inline=True)
            embed.add_field(name="Flight", value=f"`{result['flight_number']}`", inline=True)
            embed.add_field(name="Route", value=f"`{result['departure']}` → `{result['arrival']}`", inline=True)
            embed.add_field(name="Aircraft", value=f"`{result['aircraft']}`", inline=True)
            embed.add_field(name="Status", value="🟢 Approved" if status == "approved" else "🔴 Rejected", inline=True)
            embed.add_field(name="Reviewed by", value=dispatcher.mention, inline=True)
            embed.add_field(name="Reviewed", value=f"<t:{int(datetime.fromisoformat(result['reviewed_at']).timestamp())}:F>", inline=True)
            if status == "approved":
                embed.add_field(name="Approved Flights", value=str(result["approved_flights"]), inline=True)
                embed.add_field(name="Rank", value=result.get("rank", "Unranked"), inline=True)
            else:
                embed.add_field(name="Rejection Reason", value=result["rejection_reason"], inline=False)
            embed.set_image(url=result["screenshot_url"])
            await message.edit(embed=embed, view=ReviewView(self, submission_id, disabled=True, show_delete=True))
        except discord.HTTPException as exc:
            print(f"[FlightPlans] Failed to update review message #{submission_id}: {exc}")

    async def handle_delete_review(self, interaction: discord.Interaction, submission_id: int):
        """Delete only the Discord review message; keep the permanent audit/database record."""
        if not await self.dispatcher_check(interaction):
            return

        # A button interaction must be acknowledged within Discord's short
        # interaction window. Fetching the channel/message can take longer,
        # especially when Discord requires an API request, so acknowledge it
        # immediately and use a follow-up for the final result.
        await interaction.response.defer(ephemeral=True)

        row = await self.db.get_submission(submission_id)
        if not row:
            await interaction.followup.send("❌ Flight Plan not found.", ephemeral=True)
            return
        if row["status"] == "pending":
            await interaction.followup.send(
                "❌ Pending flight plans cannot be deleted. Review the submission first.",
                ephemeral=True,
            )
            return

        channel = await self.fetch_channel(row["review_channel_id"] or REVIEW_CHANNEL_ID)
        if channel is None or not row["review_message_id"]:
            await interaction.followup.send(
                "⚠️ The review message could not be located. The database record has been preserved.",
                ephemeral=True,
            )
            return

        try:
            message = await channel.fetch_message(row["review_message_id"])
            await message.delete(reason=f"Flight Plan #{submission_id} review cleanup by {interaction.user}")
        except discord.NotFound:
            # Already deleted; this is still a successful cleanup state.
            pass
        except (discord.Forbidden, discord.HTTPException) as exc:
            print(f"[FlightPlans] Failed to delete review message #{submission_id}: {exc}")
            await interaction.followup.send(
                "❌ I could not delete the review message. Check that I have **Manage Messages** permission in the review channel.",
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            f"🗑️ Flight Plan `#{submission_id}` review message deleted. The permanent flight record and audit data were kept.",
            ephemeral=True,
        )

    async def notify_pilot(self, result: dict, approved: bool):
        try:
            user = self.bot.get_user(result["discord_user_id"]) or await self.bot.fetch_user(result["discord_user_id"])
            if approved:
                embed = discord.Embed(title="✅ Flight Approved", color=discord.Color.green(), timestamp=utcnow())
                embed.description = f"Your ATC24 flight **{result['flight_number']} ({result['departure']} → {result['arrival']})** has been approved."
                embed.add_field(name="Approved flights", value=str(result["approved_flights"]), inline=True)
                embed.add_field(name="Current rank", value=result.get("rank", "Unranked"), inline=True)
                if result["approved_flights"] >= 35 and not result["written_exam_passed"]:
                    embed.add_field(name="SFO exam", value="❌ Written exam still required.", inline=False)
            else:
                embed = discord.Embed(title="❌ Flight Rejected", color=discord.Color.red(), timestamp=utcnow())
                embed.description = f"Your flight **{result['flight_number']} ({result['departure']} → {result['arrival']})** was rejected."
                embed.add_field(name="Reason", value=result["rejection_reason"], inline=False)
                embed.set_footer(text="You may submit another ATC24 flight plan.")
            await user.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            pass

    def decision_log_embed(self, result: dict, dispatcher: discord.Member, approved: bool) -> discord.Embed:
        embed = discord.Embed(
            title="✈️ Flight Approved" if approved else "❌ Flight Rejected",
            color=discord.Color.green() if approved else discord.Color.red(),
            timestamp=utcnow(),
        )
        embed.add_field(name="Pilot", value=f"<@{result['discord_user_id']}>", inline=True)
        embed.add_field(name="Flight", value=f"`{result['flight_number']}`", inline=True)
        embed.add_field(name="Route", value=f"`{result['departure']}` → `{result['arrival']}`", inline=True)
        embed.add_field(name="Aircraft", value=f"`{result['aircraft']}`", inline=True)
        embed.add_field(name="Dispatcher", value=dispatcher.mention, inline=True)
        if approved:
            embed.add_field(name="New flight count", value=str(result["approved_flights"]), inline=True)
            embed.add_field(name="Rank", value=result.get("rank", "Unranked"), inline=True)
        else:
            embed.add_field(name="Rejection reason", value=result["rejection_reason"], inline=False)
        embed.add_field(name="Screenshot", value=result["screenshot_url"], inline=False)
        return embed

    @app_commands.command(name="exam-pass", description="Mark a pilot's SFO written exam as passed")
    @app_commands.describe(user="Pilot who passed the exam", score="Optional exam score")
    async def exam_pass(self, interaction: discord.Interaction, user: discord.Member, score: Optional[float] = None):
        if not isinstance(interaction.user, discord.Member) or not (self.is_dispatcher(interaction.user) or interaction.user.guild_permissions.administrator):
            await interaction.response.send_message("❌ Only Dispatchers or administrators can mark exams as passed.", ephemeral=True)
            return
        if score is not None and not 0 <= score <= 100:
            await interaction.response.send_message("❌ Score must be between 0 and 100.", ephemeral=True)
            return

        await self.db.set_exam_passed(user.id, interaction.user.id, score)
        profile = await self.db.get_profile(user.id)
        rank = await self.sync_member_rank(user, profile["approved_flights"], True)
        await interaction.response.send_message(
            f"✅ SFO written exam marked as passed for {user.mention}.\nApproved flights: **{profile['approved_flights']}**\nCurrent rank: **{rank}**",
            ephemeral=True,
        )
        await self.send_log(discord.Embed(
            title="📝 SFO Written Exam Passed",
            description=f"{user.mention} passed the SFO written exam.",
            color=discord.Color.blurple(),
            timestamp=utcnow(),
        ).add_field(name="Reviewed by", value=interaction.user.mention, inline=True).add_field(name="Score", value=str(score) if score is not None else "Not recorded", inline=True).add_field(name="Current rank", value=rank, inline=True))

    @app_commands.command(name="pilotprofile", description="View an ATC24 pilot profile")
    @app_commands.describe(user="Optional pilot to inspect")
    async def pilotprofile(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        target = user or interaction.user
        profile = await self.db.get_profile(target.id)
        flights = int(profile["approved_flights"])
        exam = bool(profile["written_exam_passed"])
        rank, _ = self.rank_for(flights, exam)
        next_rank, needed = self.next_rank_info(flights, exam)
        embed = discord.Embed(title="✈️ Pilot Profile", color=discord.Color.blurple(), timestamp=utcnow())
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="User", value=target.mention, inline=True)
        embed.add_field(name="Rank", value=rank, inline=True)
        embed.add_field(name="Approved Flights", value=str(flights), inline=True)
        embed.add_field(name="Written Exam", value="✅ Passed" if exam else "❌ Not Passed", inline=True)
        if rank == "SFO":
            embed.add_field(name="Next Rank", value="Maximum rank", inline=True)
            embed.add_field(name="Flights Required", value="—", inline=True)
        elif next_rank.startswith("SFO") and flights >= 35 and not exam:
            embed.add_field(name="Next Rank", value="SFO", inline=True)
            embed.add_field(name="Requirement", value="Pass the written exam", inline=True)
        else:
            embed.add_field(name="Next Rank", value=next_rank, inline=True)
            embed.add_field(name="Flights Required", value=str(needed), inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="flightplan-view", description="Inspect an ATC24 flight-plan submission")
    @app_commands.describe(submission_id="Flight Plan ID")
    async def flightplan_view(self, interaction: discord.Interaction, submission_id: int):
        if not isinstance(interaction.user, discord.Member) or not self.is_dispatcher(interaction.user):
            await interaction.response.send_message("❌ Only Dispatchers can inspect flight-plan submissions.", ephemeral=True)
            return
        row = await self.db.get_submission(submission_id)
        if not row:
            await interaction.response.send_message("❌ Flight Plan not found.", ephemeral=True)
            return
        embed = self.build_review_embed(row)
        embed.set_footer(text=f"Status: {row['status'].upper()}")
        if row["rejection_reason"]:
            embed.add_field(name="Rejection Reason", value=row["rejection_reason"], inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="sync-ranks", description="Recalculate ATC24 pilot ranks")
    async def sync_ranks(self, interaction: discord.Interaction):
        if not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Only administrators can synchronize ranks.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        updated = 0
        missing = 0
        for user_id in await self.db.all_user_ids():
            member = interaction.guild.get_member(user_id)
            if not member:
                missing += 1
                continue
            profile = await self.db.get_profile(user_id)
            await self.sync_member_rank(member, profile["approved_flights"], bool(profile["written_exam_passed"]))
            updated += 1
        await interaction.followup.send(f"✅ Rank synchronization complete. Updated **{updated}** member(s); **{missing}** database user(s) are not currently in the server.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(FlightPlans(bot))
