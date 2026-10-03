import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime
from typing import Optional

class TicketsPanel(commands.Cog):
    """Ticket panel system with persistent messages"""

    def __init__(self, bot):
        self.bot = bot
        self.config_file = 'tickets_panel_config.json'
        self.ensure_config()

    def ensure_config(self):
        """Ensure config file exists"""
        if not os.path.exists(self.config_file):
            with open(self.config_file, 'w') as f:
                json.dump({}, f, indent=2)

    def load_config(self) -> dict:
        """Load config from file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except:
            return {}

    def save_config(self, config: dict):
        """Save config to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    @app_commands.command(name='setticketpanel', description='Create ticket panel (Admin)')
    @app_commands.describe(channel='Channel for panel')
    async def set_panel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Create the ticket panel"""
        try:
            # Permission check
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message('❌ Admin only', ephemeral=True)
                return

            # Permission check for bot
            if not channel.permissions_for(interaction.guild.me).send_messages:
                await interaction.response.send_message('❌ I cannot send messages in that channel', ephemeral=True)
                return

            # Create embed
            embed = discord.Embed(
                title='🎫 Tickets',
                description='Click a button below to create a ticket',
                color=discord.Color.blurple(),
                timestamp=datetime.now()
            )
            embed.add_field(
                name='Support Categories',
                value='🐛 Bug • 💡 Feature • ❓ Support • 📝 General',
                inline=False
            )
            embed.set_footer(text='Our team will respond shortly')

            # Send message with buttons
            view = TicketButtonView(self.bot)
            message = await channel.send(embed=embed, view=view)

            # Save config
            config = self.load_config()
            guild_id = str(interaction.guild_id)
            config[guild_id] = {
                'channel_id': channel.id,
                'message_id': message.id
            }
            self.save_config(config)

            await interaction.response.send_message(f'✅ Panel created in {channel.mention}', ephemeral=True)

        except Exception as e:
            print(f"Error in set_panel: {e}")
            await interaction.response.send_message(f'❌ Error: {str(e)[:100]}', ephemeral=True)

    @app_commands.command(name='viewticketpanel', description='View panel info (Admin)')
    async def view_panel(self, interaction: discord.Interaction):
        """View panel info"""
        try:
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message('❌ Admin only', ephemeral=True)
                return

            config = self.load_config()
            guild_id = str(interaction.guild_id)

            if guild_id not in config:
                await interaction.response.send_message('❌ No panel set', ephemeral=True)
                return

            panel_info = config[guild_id]
            channel = await self.bot.fetch_channel(panel_info['channel_id'])

            embed = discord.Embed(
                title='🎫 Panel Info',
                color=discord.Color.blurple()
            )
            embed.add_field(name='Channel', value=channel.mention, inline=False)
            embed.add_field(name='Status', value='🟢 Active', inline=False)

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            print(f"Error in view_panel: {e}")
            await interaction.response.send_message(f'❌ Error: {str(e)[:100]}', ephemeral=True)


class TicketButtonView(discord.ui.View):
    """Ticket panel buttons"""

    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label='Bug', style=discord.ButtonStyle.red, emoji='🐛', custom_id='ticket_bug')
    async def bug_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_modal(interaction, 'bug')

    @discord.ui.button(label='Feature', style=discord.ButtonStyle.blurple, emoji='💡', custom_id='ticket_feature')
    async def feature_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_modal(interaction, 'feature')

    @discord.ui.button(label='Support', style=discord.ButtonStyle.green, emoji='❓', custom_id='ticket_support')
    async def support_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_modal(interaction, 'support')

    @discord.ui.button(label='General', style=discord.ButtonStyle.grey, emoji='📝', custom_id='ticket_general')
    async def general_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_modal(interaction, 'general')

    async def show_modal(self, interaction: discord.Interaction, category: str):
        """Show ticket creation modal"""
        try:
            # Create simple modal
            class TicketModal(discord.ui.Modal, title=f'Create {category.title()} Ticket'):
                name = discord.ui.TextInput(
                    label='Ticket Title',
                    placeholder='Brief description...',
                    max_length=100,
                    required=True
                )
                description = discord.ui.TextInput(
                    label='Description',
                    placeholder='More details...',
                    max_length=1000,
                    style=discord.TextStyle.paragraph,
                    required=True
                )

                async def on_submit(modal_self, modal_interaction: discord.Interaction):
                    try:
                        tickets_cog = self.bot.get_cog('Tickets')
                        if not tickets_cog:
                            await modal_interaction.response.send_message('❌ Tickets system error', ephemeral=True)
                            return

                        # Create ticket
                        ticket_id = tickets_cog.create_ticket(
                            modal_interaction.user.id,
                            modal_self.name.value,
                            modal_self.description.value,
                            category,
                            modal_interaction.guild_id
                        )

                        # Response
                        embed = discord.Embed(
                            title='✅ Ticket Created',
                            description='Your support ticket has been created.',
                            color=discord.Color.green(),
                            timestamp=datetime.now()
                        )
                        embed.add_field(name='Ticket ID', value=f'`{ticket_id}`', inline=False)
                        embed.add_field(name='Category', value=category.title(), inline=True)
                        embed.add_field(name='Status', value='🟢 Open', inline=True)
                        embed.set_footer(text='Use /viewticket to check status')

                        await modal_interaction.response.send_message(embed=embed, ephemeral=True)

                    except Exception as e:
                        print(f"Modal submit error: {e}")
                        await modal_interaction.response.send_message(
                            f'❌ Error creating ticket: {str(e)[:80]}',
                            ephemeral=True
                        )

            # Show modal
            await interaction.response.send_modal(TicketModal())

        except Exception as e:
            print(f"Error in show_modal: {e}")
            await interaction.response.send_message(f'❌ Error: {str(e)[:100]}', ephemeral=True)


async def setup(bot):
    await bot.add_cog(TicketsPanel(bot))
