import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime

class Logs(commands.Cog):
    """Logging system for member and message events"""

    def __init__(self, bot):
        self.bot = bot
        self.logs_file = 'logs_data.json'
        self.load_logs()

    def load_logs(self):
        """Load logs from file"""
        if os.path.exists(self.logs_file):
            with open(self.logs_file, 'r') as f:
                self.logs_data = json.load(f)
        else:
            self.logs_data = {
                'joins': [],
                'leaves': [],
                'message_deletes': [],
                'message_edits': [],
                'bans': [],
                'unbans': []
            }

    def save_logs(self):
        """Save logs to file"""
        with open(self.logs_file, 'w') as f:
            json.dump(self.logs_data, f, indent=4)

    def add_log(self, log_type: str, data: dict):
        """Add a log entry"""
        data['timestamp'] = datetime.now().isoformat()
        self.logs_data[log_type].append(data)
        # Keep only last 1000 entries per type to avoid bloat
        if len(self.logs_data[log_type]) > 1000:
            self.logs_data[log_type] = self.logs_data[log_type][-1000:]
        self.save_logs()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Log when a member joins"""
        self.add_log('joins', {
            'user_id': member.id,
            'username': member.name,
            'guild': member.guild.name,
            'account_created': member.created_at.isoformat()
        })

        # Send to log channel if configured
        log_channel = self.bot.get_channel(1534174870076784670)
        if log_channel:
            embed = discord.Embed(
                title='📥 Member Joined',
                description=f'{member.mention} ({member.name})',
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            embed.add_field(name='User ID', value=member.id, inline=False)
            embed.add_field(name='Account Created', value=member.created_at.strftime('%Y-%m-%d %H:%M:%S'), inline=True)
            embed.add_field(name='Total Members', value=member.guild.member_count, inline=True)
            embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
            try:
                await log_channel.send(embed=embed)
            except:
                pass

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Log when a member leaves"""
        self.add_log('leaves', {
            'user_id': member.id,
            'username': member.name,
            'guild': member.guild.name,
            'joined_at': member.joined_at.isoformat() if member.joined_at else None
        })

        # Send to log channel if configured
        log_channel = self.bot.get_channel(1534174870076784670)
        if log_channel:
            embed = discord.Embed(
                title='📤 Member Left',
                description=f'{member.name}',
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            embed.add_field(name='User ID', value=member.id, inline=False)
            if member.joined_at:
                duration = (datetime.now(member.joined_at.tzinfo) - member.joined_at).days
                embed.add_field(name='Was Member For', value=f'{duration} days', inline=True)
            embed.add_field(name='Total Members', value=member.guild.member_count, inline=True)
            embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
            try:
                await log_channel.send(embed=embed)
            except:
                pass

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """Log when a message is deleted"""
        if message.author.bot:
            return

        self.add_log('message_deletes', {
            'author_id': message.author.id,
            'author_name': message.author.name,
            'channel': message.channel.name if hasattr(message.channel, 'name') else 'DM',
            'content': message.content[:500],  # Limit to 500 chars
            'guild': message.guild.name if message.guild else 'DM'
        })

        # Send to log channel if configured
        if message.guild:
            log_channel = self.bot.get_channel(1534174870076784670)
            if log_channel:
                embed = discord.Embed(
                    title='🗑️ Message Deleted',
                    description=message.content[:1024] if message.content else '*No content*',
                    color=discord.Color.orange(),
                    timestamp=datetime.now()
                )
                embed.add_field(name='Author', value=f'{message.author.mention} ({message.author.name})', inline=False)
                embed.add_field(name='Channel', value=message.channel.mention, inline=False)
                embed.set_thumbnail(url=message.author.avatar.url if message.author.avatar else None)
                try:
                    await log_channel.send(embed=embed)
                except:
                    pass

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Log when a message is edited"""
        if before.author.bot or before.content == after.content:
            return

        self.add_log('message_edits', {
            'author_id': before.author.id,
            'author_name': before.author.name,
            'channel': before.channel.name if hasattr(before.channel, 'name') else 'DM',
            'before': before.content[:500],
            'after': after.content[:500],
            'guild': before.guild.name if before.guild else 'DM'
        })

        # Send to log channel if configured
        if before.guild:
            log_channel = self.bot.get_channel(1534174870076784670)
            if log_channel:
                embed = discord.Embed(
                    title='✏️ Message Edited',
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                embed.add_field(name='Author', value=f'{before.author.mention} ({before.author.name})', inline=False)
                embed.add_field(name='Channel', value=before.channel.mention, inline=False)
                embed.add_field(name='Before', value=before.content[:1024] if before.content else '*No content*', inline=False)
                embed.add_field(name='After', value=after.content[:1024] if after.content else '*No content*', inline=False)
                embed.set_thumbnail(url=before.author.avatar.url if before.author.avatar else None)
                try:
                    await log_channel.send(embed=embed)
                except:
                    pass

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        """Log when a member is banned"""
        self.add_log('bans', {
            'user_id': user.id,
            'username': user.name,
            'guild': guild.name
        })

        # Send to log channel if configured
        log_channel = self.bot.get_channel(1534174870076784670)
        if log_channel:
            embed = discord.Embed(
                title='🔨 Member Banned',
                description=f'{user.mention} ({user.name})',
                color=discord.Color.dark_red(),
                timestamp=datetime.now()
            )
            embed.add_field(name='User ID', value=user.id, inline=False)
            embed.set_thumbnail(url=user.avatar.url if user.avatar else None)
            try:
                await log_channel.send(embed=embed)
            except:
                pass

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        """Log when a member is unbanned"""
        self.add_log('unbans', {
            'user_id': user.id,
            'username': user.name,
            'guild': guild.name
        })

        # Send to log channel if configured
        log_channel = self.bot.get_channel(1534174870076784670)
        if log_channel:
            embed = discord.Embed(
                title='✅ Member Unbanned',
                description=f'{user.mention} ({user.name})',
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            embed.add_field(name='User ID', value=user.id, inline=False)
            embed.set_thumbnail(url=user.avatar.url if user.avatar else None)
            try:
                await log_channel.send(embed=embed)
            except:
                pass

    @app_commands.command(name='logs', description='View recent logs')
    @app_commands.describe(log_type='Type of log to view (joins, leaves, message_deletes, message_edits, bans, unbans)')
    async def view_logs(self, interaction: discord.Interaction, log_type: str = 'joins'):
        """View recent logs"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message('❌ Only administrators can use this command.', ephemeral=True)
            return

        valid_types = ['joins', 'leaves', 'message_deletes', 'message_edits', 'bans', 'unbans']
        if log_type not in valid_types:
            await interaction.response.send_message(f'❌ Invalid log type. Choose from: {", ".join(valid_types)}', ephemeral=True)
            return

        logs = self.logs_data.get(log_type, [])
        if not logs:
            await interaction.response.send_message(f'❌ No {log_type} logs found.', ephemeral=True)
            return

        # Get last 10 entries
        recent_logs = logs[-10:]
        log_text = ''

        for idx, log in enumerate(recent_logs, 1):
            timestamp = log.get('timestamp', 'N/A')
            if log_type == 'joins':
                log_text += f'{idx}. **{log["username"]}** joined at {timestamp}\n'
            elif log_type == 'leaves':
                log_text += f'{idx}. **{log["username"]}** left at {timestamp}\n'
            elif log_type == 'message_deletes':
                log_text += f'{idx}. **{log["author_name"]}** - {log["content"][:50]}... (deleted)\n'
            elif log_type == 'message_edits':
                log_text += f'{idx}. **{log["author_name"]}** edited message at {timestamp}\n'
            elif log_type == 'bans':
                log_text += f'{idx}. **{log["username"]}** banned at {timestamp}\n'
            elif log_type == 'unbans':
                log_text += f'{idx}. **{log["username"]}** unbanned at {timestamp}\n'

        embed = discord.Embed(
            title=f'📋 Recent {log_type.replace("_", " ").title()} Logs',
            description=log_text,
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f'Total {log_type}: {len(logs)}')

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='clear_logs', description='Clear all logs (admin only)')
    async def clear_logs(self, interaction: discord.Interaction):
        """Clear all logs"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message('❌ Only administrators can use this command.', ephemeral=True)
            return

        self.logs_data = {
            'joins': [],
            'leaves': [],
            'message_deletes': [],
            'message_edits': [],
            'bans': [],
            'unbans': []
        }
        self.save_logs()

        await interaction.response.send_message('✅ All logs have been cleared.', ephemeral=True)

# Setup function to load the cog
async def setup(bot):
    await bot.add_cog(Logs(bot))
