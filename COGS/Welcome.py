import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime

class Welcome(commands.Cog):
    """Welcome system for new members"""

    def __init__(self, bot):
        self.bot = bot
        self.config_file = 'welcome_config.json'
        self.load_config()

    def load_config(self):
        """Load welcome configuration"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                'welcome_channel': None,
                'welcome_enabled': True,
                'dm_enabled': True,
                'welcome_message': 'Welcome to {guild_name}! 👋'
            }
            self.save_config()

    def save_config(self):
        """Save welcome configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Welcome new members"""

        # Send DM to user
        if self.config.get('dm_enabled', True):
            try:
                embed = discord.Embed(
                    title=f'Welcome to {member.guild.name}! 👋',
                    description='We\'re excited to have you here!',
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                embed.add_field(name='Server', value=member.guild.name, inline=False)
                embed.add_field(name='Members', value=f'{member.guild.member_count}', inline=True)
                embed.add_field(name='Joined At', value=member.joined_at.strftime('%Y-%m-%d %H:%M:%S'), inline=True)
                embed.set_thumbnail(url=member.guild.icon.url if member.guild.icon else None)
                embed.set_footer(text='Be respectful and follow the rules!')

                await member.send(embed=embed)
            except discord.Forbidden:
                pass  # User has DMs disabled

        # Send to welcome channel
        if self.config.get('welcome_enabled', True):
            welcome_channel_id = self.config.get('welcome_channel')
            if welcome_channel_id:
                try:
                    welcome_channel = self.bot.get_channel(welcome_channel_id)
                    if welcome_channel:
                        embed = discord.Embed(
                            title='📥 New Member',
                            description=f'{member.mention} just joined!',
                            color=discord.Color.green(),
                            timestamp=datetime.now()
                        )
                        embed.add_field(name='Username', value=member.name, inline=True)
                        embed.add_field(name='Account Age', value=f'<t:{int(member.created_at.timestamp())}:R>', inline=True)
                        embed.add_field(name='Total Members', value=member.guild.member_count, inline=True)
                        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)

                        await welcome_channel.send(embed=embed)
                except Exception as e:
                    print(f"Error sending welcome message: {e}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Say goodbye to leaving members"""
        welcome_channel_id = self.config.get('welcome_channel')
        if welcome_channel_id:
            try:
                welcome_channel = self.bot.get_channel(welcome_channel_id)
                if welcome_channel:
                    embed = discord.Embed(
                        title='📤 Member Left',
                        description=f'{member.name} has left the server',
                        color=discord.Color.red(),
                        timestamp=datetime.now()
                    )
                    embed.add_field(name='Username', value=member.name, inline=True)
                    if member.joined_at:
                        duration = (datetime.now(member.joined_at.tzinfo) - member.joined_at).days
                        embed.add_field(name='Was Member For', value=f'{duration} days', inline=True)
                    embed.set_thumbnail(url=member.avatar.url if member.avatar else None)

                    await welcome_channel.send(embed=embed)
            except Exception as e:
                print(f"Error sending goodbye message: {e}")

    @app_commands.command(name='setwelcomechannel', description='Set the welcome channel (admin only)')
    @app_commands.describe(channel='The channel to send welcome messages to')
    async def set_welcome_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Set where welcome messages should be sent"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message('❌ Only administrators can use this command.', ephemeral=True)
            return

        self.config['welcome_channel'] = channel.id
        self.save_config()

        embed = discord.Embed(
            title='✅ Welcome Channel Set',
            description=f'Welcome messages will now be sent to {channel.mention}',
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='togglewelcome', description='Enable/disable welcome messages (admin only)')
    @app_commands.describe(enabled='Enable or disable welcome messages')
    async def toggle_welcome(self, interaction: discord.Interaction, enabled: bool):
        """Toggle welcome messages on/off"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message('❌ Only administrators can use this command.', ephemeral=True)
            return

        self.config['welcome_enabled'] = enabled
        self.save_config()

        status = '✅ enabled' if enabled else '❌ disabled'
        embed = discord.Embed(
            title='Welcome Messages',
            description=f'Welcome channel messages are now {status}',
            color=discord.Color.green() if enabled else discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='togglewelcomedm', description='Enable/disable welcome DMs (admin only)')
    @app_commands.describe(enabled='Enable or disable welcome DMs')
    async def toggle_welcome_dm(self, interaction: discord.Interaction, enabled: bool):
        """Toggle welcome DMs on/off"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message('❌ Only administrators can use this command.', ephemeral=True)
            return

        self.config['dm_enabled'] = enabled
        self.save_config()

        status = '✅ enabled' if enabled else '❌ disabled'
        embed = discord.Embed(
            title='Welcome DMs',
            description=f'Welcome DMs are now {status}',
            color=discord.Color.green() if enabled else discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='welcomeconfig', description='View welcome configuration (admin only)')
    async def welcome_config(self, interaction: discord.Interaction):
        """View current welcome configuration"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message('❌ Only administrators can use this command.', ephemeral=True)
            return

        welcome_channel_id = self.config.get('welcome_channel')
        channel_name = f'<#{welcome_channel_id}>' if welcome_channel_id else 'Not set'
        welcome_enabled = '✅' if self.config.get('welcome_enabled', True) else '❌'
        dm_enabled = '✅' if self.config.get('dm_enabled', True) else '❌'

        embed = discord.Embed(
            title='📋 Welcome Configuration',
            color=discord.Color.blurple()
        )
        embed.add_field(name='Welcome Channel', value=channel_name, inline=False)
        embed.add_field(name='Channel Messages', value=welcome_enabled, inline=True)
        embed.add_field(name='Direct Messages', value=dm_enabled, inline=True)
        embed.set_footer(text='Use /setwelcomechannel, /togglewelcome, /togglewelcomedm to configure')

        await interaction.response.send_message(embed=embed)

# Setup function to load the cog
async def setup(bot):
    await bot.add_cog(Welcome(bot))
