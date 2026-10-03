import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime


class Moderation(commands.Cog):
    """Moderation commands for the Discord bot"""

    def __init__(self, bot):
        self.bot = bot
        self.warns_file = 'warns_data.json'
        self.load_warns()

    def load_warns(self):
        """Load warns data from file"""
        if os.path.exists(self.warns_file):
            with open(self.warns_file, 'r') as f:
                self.warns_data = json.load(f)
        else:
            self.warns_data = {}

    def save_warns(self):
        """Save warns data to file"""
        with open(self.warns_file, 'w') as f:
            json.dump(self.warns_data, f, indent=4)

    def add_warn(self, user_id: int, reason: str, moderator: str):
        """Add a warning to a user"""
        user_id = str(user_id)
        if user_id not in self.warns_data:
            self.warns_data[user_id] = []

        self.warns_data[user_id].append({
            'reason': reason,
            'moderator': moderator,
            'timestamp': datetime.now().isoformat(),
            'warn_number': len(self.warns_data[user_id]) + 1
        })
        self.save_warns()

    def get_warns(self, user_id: int):
        """Get warns for a user"""
        return self.warns_data.get(str(user_id), [])

    @app_commands.command(name='ban', description='Ban a member from the server')
    @app_commands.describe(member='The member to ban', reason='Reason for banning')
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = 'No reason provided'):
        """Ban a member from the server"""

        # Check if user has permission
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message('❌ You do not have permission to ban members.', ephemeral=True)
            return

        try:
            await member.ban(reason=reason)
            await interaction.response.send_message(f'✅ {member.mention} has been banned.\n**Reason:** {reason}')
        except discord.Forbidden:
            await interaction.response.send_message('❌ I do not have permission to ban this member.', ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f'❌ An error occurred: {str(e)}', ephemeral=True)

    @app_commands.command(name='kick', description='Kick a member from the server')
    @app_commands.describe(member='The member to kick', reason='Reason for kicking')
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = 'No reason provided'):
        """Kick a member from the server"""

        # Check if user has permission
        if not interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message('❌ You do not have permission to kick members.', ephemeral=True)
            return

        try:
            await member.kick(reason=reason)
            await interaction.response.send_message(f'✅ {member.mention} has been kicked.\n**Reason:** {reason}')
        except discord.Forbidden:
            await interaction.response.send_message('❌ I do not have permission to kick this member.', ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f'❌ An error occurred: {str(e)}', ephemeral=True)

    @app_commands.command(name='mute', description='Mute a member for a specified duration')
    @app_commands.describe(member='The member to mute', timeout='Timeout duration (e.g., 1h, 30m, 1d)')
    async def mute(self, interaction: discord.Interaction, member: discord.Member, timeout: str):
        """Mute a member for a specified duration"""

        # Check if user has permission
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message('❌ You do not have permission to mute members.', ephemeral=True)
            return

        # Parse timeout string
        timeout_dict = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        try:
            value = int(timeout[:-1])
            unit = timeout[-1].lower()

            if unit not in timeout_dict:
                await interaction.response.send_message('❌ Invalid timeout format. Use: 1h, 30m, 1d, 60s', ephemeral=True)
                return

            seconds = value * timeout_dict[unit]
            duration = discord.utils.utcnow() + discord.utils.timedelta(seconds=seconds)
        except (ValueError, IndexError):
            await interaction.response.send_message('❌ Invalid timeout format. Use: 1h, 30m, 1d, 60s', ephemeral=True)
            return

        try:
            await member.timeout(duration)
            await interaction.response.send_message(f'✅ {member.mention} has been muted for {timeout}.')
        except discord.Forbidden:
            await interaction.response.send_message('❌ I do not have permission to mute this member.', ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f'❌ An error occurred: {str(e)}', ephemeral=True)

    @app_commands.command(name='unmute', description='Unmute a member')
    @app_commands.describe(member='The member to unmute', reason='Reason for unmuting')
    async def unmute(self, interaction: discord.Interaction, member: discord.Member, reason: str = 'No reason provided'):
        """Unmute a member"""

        # Check if user has permission
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message('❌ You do not have permission to unmute members.', ephemeral=True)
            return

        try:
            await member.timeout(None)
            await interaction.response.send_message(f'✅ {member.mention} has been unmuted.\n**Reason:** {reason}')
        except discord.Forbidden:
            await interaction.response.send_message('❌ I do not have permission to unmute this member.', ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f'❌ An error occurred: {str(e)}', ephemeral=True)

    @app_commands.command(name='unban', description='Unban a user from the server')
    @app_commands.describe(user='The user to unban (username or user ID)', reason='Reason for unbanning')
    async def unban(self, interaction: discord.Interaction, user: str, reason: str = 'No reason provided'):
        """Unban a user from the server"""

        # Check if user has permission
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message('❌ You do not have permission to unban users.', ephemeral=True)
            return

        try:
            # Try to parse as user ID first
            try:
                user_id = int(user)
                ban_entry = None
                async for entry in interaction.guild.bans(limit=None):
                    if entry.user.id == user_id:
                        ban_entry = entry
                        break
            except ValueError:
                # If not a number, search by username
                ban_entry = None
                async for entry in interaction.guild.bans(limit=None):
                    if entry.user.name.lower() == user.lower():
                        ban_entry = entry
                        break

            if ban_entry is None:
                await interaction.response.send_message(f'❌ User "{user}" is not banned or not found.', ephemeral=True)
                return

            await interaction.guild.unban(ban_entry.user, reason=reason)
            await interaction.response.send_message(f'✅ {ban_entry.user.mention} ({ban_entry.user.name}) has been unbanned.\n**Reason:** {reason}')
        except discord.Forbidden:
            await interaction.response.send_message('❌ I do not have permission to unban users.', ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f'❌ An error occurred: {str(e)}', ephemeral=True)

    @app_commands.command(name='warn', description='Warn a member')
    @app_commands.describe(member='The member to warn', reason='Reason for warning')
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = 'No reason provided'):
        """Warn a member and send them a DM"""

        # Check if user has permission
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message('❌ You do not have permission to warn members.', ephemeral=True)
            return

        # Add the warn
        self.add_warn(member.id, reason, interaction.user.name)
        warns = self.get_warns(member.id)
        warn_count = len(warns)

        # Try to send DM to the member
        try:
            embed = discord.Embed(
                title='⚠️ You Have Been Warned',
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            embed.add_field(
                name='Server', value=interaction.guild.name, inline=False)
            embed.add_field(name='Reason', value=reason, inline=False)
            embed.add_field(name='Moderator',
                            value=interaction.user.mention, inline=False)
            embed.add_field(name='Total Warns',
                            value=f'{warn_count}', inline=True)
            embed.set_thumbnail(
                url=interaction.guild.icon.url if interaction.guild.icon else None)

            await member.send(embed=embed)
            dm_sent = True
        except discord.Forbidden:
            dm_sent = False

        # Send response to moderator
        embed = discord.Embed(
            title='✅ Member Warned',
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name='Member', value=member.mention, inline=False)
        embed.add_field(name='Reason', value=reason, inline=False)
        embed.add_field(name='Total Warns', value=f'{warn_count}', inline=True)
        embed.add_field(
            name='DM Sent', value='✅ Yes' if dm_sent else '❌ No (DMs closed)', inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='warns', description='Check warns for a member')
    @app_commands.describe(member='The member to check warns for')
    async def warns(self, interaction: discord.Interaction, member: discord.Member):
        """View warns for a member"""

        # Check if user has permission
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message('❌ You do not have permission to view warns.', ephemeral=True)
            return

        warns = self.get_warns(member.id)

        if not warns:
            await interaction.response.send_message(f'✅ {member.mention} has no warns.', ephemeral=True)
            return

        embed = discord.Embed(
            title=f'⚠️ Warns for {member.name}',
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )

        for warn in warns:
            embed.add_field(
                name=f'Warn #{warn["warn_number"]}',
                value=f'**Reason:** {warn["reason"]}\n**Moderator:** {warn["moderator"]}\n**Time:** {warn["timestamp"]}',
                inline=False
            )

        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
        embed.set_footer(text=f'Total warns: {len(warns)}')

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='clear_warns', description='Clear warns for a member (admin only)')
    @app_commands.describe(member='The member to clear warns for')
    async def clear_warns(self, interaction: discord.Interaction, member: discord.Member):
        """Clear all warns for a member"""

        # Check if user has permission
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message('❌ Only administrators can clear warns.', ephemeral=True)
            return

        user_id = str(member.id)
        if user_id in self.warns_data:
            del self.warns_data[user_id]
            self.save_warns()
            await interaction.response.send_message(f'✅ Cleared all warns for {member.mention}.', ephemeral=True)
        else:
            await interaction.response.send_message(f'❌ {member.mention} has no warns to clear.', ephemeral=True)

    @app_commands.command(name='purge', description='Delete messages from the channel')
    @app_commands.describe(amount='Number of messages to delete (1-100)', member='Optional: only delete messages from this user')
    async def purge(self, interaction: discord.Interaction, amount: int, member: discord.Member = None):
        """Purge/delete messages from the channel"""

        # Check if user has permission
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message('❌ You do not have permission to manage messages.', ephemeral=True)
            return

        # Validate amount
        if amount < 1 or amount > 100:
            await interaction.response.send_message('❌ Amount must be between 1 and 100.', ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            # Define filter function
            def check(msg):
                if member:
                    return msg.author == member
                return True

            # Delete messages
            deleted = await interaction.channel.purge(limit=amount, check=check)

            embed = discord.Embed(
                title='🗑️ Messages Purged',
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            embed.add_field(name='Amount Deleted',
                            value=f'**{len(deleted)}**', inline=True)
            embed.add_field(
                name='Channel', value=interaction.channel.mention, inline=True)
            if member:
                embed.add_field(name='From User',
                                value=member.mention, inline=True)
            embed.add_field(name='Moderator',
                            value=interaction.user.mention, inline=True)

            await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send('❌ I do not have permission to delete messages.', ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f'❌ An error occurred: {str(e)}', ephemeral=True)


# Setup function to load the cog
async def setup(bot):
    await bot.add_cog(Moderation(bot))
