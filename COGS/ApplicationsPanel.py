import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime
from typing import Optional

class ApplicationsPanel(commands.Cog):
    """Application panel system with persistent messages and buttons"""

    def __init__(self, bot):
        self.bot = bot
        self.config_file = 'applications_panel_config.json'
        self.load_config()

    def load_config(self):
        """Load panel configuration"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            except:
                self.config = {}
        else:
            self.config = {}

    def save_config(self):
        """Save panel configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def get_panel_channel(self, guild_id: int) -> Optional[int]:
        """Get the application panel channel for a guild"""
        guild_key = str(guild_id)
        return self.config.get(guild_key, {}).get('panel_channel')

    def set_panel_channel(self, guild_id: int, channel_id: int):
        """Set the application panel channel"""
        guild_key = str(guild_id)
        if guild_key not in self.config:
            self.config[guild_key] = {}
        self.config[guild_key]['panel_channel'] = channel_id
        self.save_config()

    def get_panel_message_id(self, guild_id: int) -> Optional[int]:
        """Get the application panel message ID"""
        guild_key = str(guild_id)
        return self.config.get(guild_key, {}).get('panel_message_id')

    def set_panel_message_id(self, guild_id: int, message_id: int):
        """Set the application panel message ID"""
        guild_key = str(guild_id)
        if guild_key not in self.config:
            self.config[guild_key] = {}
        self.config[guild_key]['panel_message_id'] = message_id
        self.save_config()

    @app_commands.command(name='setapplicationpanel', description='Set the channel for the application panel (Admin only)')
    @app_commands.describe(channel='The channel to post the application panel')
    async def set_application_panel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Set the application panel channel and create the panel"""
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title='❌ Permission Denied',
                description='Only administrators can set the application panel',
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Save channel
        self.set_panel_channel(interaction.guild_id, channel.id)

        # Create the panel embed
        panel_embed = discord.Embed(
            title='📋 Applications',
            description='To create an application use the **Create Application** button below',
            color=discord.Color.blurple(),
            timestamp=datetime.now()
        )
        panel_embed.add_field(
            name='📝 Application System',
            value='Click the button below to submit an application to our community.',
            inline=False
        )
        panel_embed.set_footer(text='Applications help us understand who you are and why you want to join')

        # Create button view
        view = ApplicationPanelView(self.bot)

        # Send the panel message
        try:
            message = await channel.send(embed=panel_embed, view=view)
            self.set_panel_message_id(interaction.guild_id, message.id)

            embed = discord.Embed(
                title='✅ Application Panel Created',
                description=f'Application panel has been created in {channel.mention}',
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            embed.add_field(name='Channel', value=channel.mention, inline=True)
            embed.add_field(name='Message ID', value=f'`{message.id}`', inline=True)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title='❌ Error',
                description=f'Failed to create panel: {str(e)}',
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name='viewapplicationpanel', description='View application panel settings (Admin only)')
    async def view_application_panel(self, interaction: discord.Interaction):
        """View the current application panel settings"""
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title='❌ Permission Denied',
                description='Only administrators can view panel settings',
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        panel_channel_id = self.get_panel_channel(interaction.guild_id)
        panel_message_id = self.get_panel_message_id(interaction.guild_id)

        if not panel_channel_id:
            embed = discord.Embed(
                title='📭 No Application Panel',
                description='Use `/setapplicationpanel` to create an application panel',
                color=discord.Color.yellow(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        try:
            channel = await self.bot.fetch_channel(panel_channel_id)
            embed = discord.Embed(
                title='📋 Application Panel Settings',
                color=discord.Color.blurple(),
                timestamp=datetime.now()
            )
            embed.add_field(name='Channel', value=channel.mention, inline=True)
            embed.add_field(name='Channel ID', value=f'`{panel_channel_id}`', inline=True)
            if panel_message_id:
                embed.add_field(name='Message ID', value=f'`{panel_message_id}`', inline=True)
            embed.set_footer(text='Panel is active and ready to use')
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.NotFound:
            embed = discord.Embed(
                title='⚠️ Channel Not Found',
                description='The configured panel channel no longer exists. Use `/setapplicationpanel` to set a new one.',
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


class ApplicationPanelView(discord.ui.View):
    """View for the application panel with Create Application button"""

    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label='Create Application',
        style=discord.ButtonStyle.primary,
        emoji='📋',
        custom_id='create_application_btn'
    )
    async def create_application_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle the create application button press"""
        # Get the Applications cog
        applications_cog = self.bot.get_cog('Applications')

        if not applications_cog:
            await interaction.response.send_message('❌ Applications system not found', ephemeral=True)
            return

        # Show the modal from Applications cog
        from COGS.Applications import ApplicationModal
        await interaction.response.send_modal(ApplicationModal())


async def setup(bot):
    await bot.add_cog(ApplicationsPanel(bot))
