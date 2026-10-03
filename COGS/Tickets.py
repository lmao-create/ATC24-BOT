import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime
from typing import Optional
import uuid

class Tickets(commands.Cog):
    """Ticket management system for support and issues"""

    def __init__(self, bot):
        self.bot = bot
        self.tickets_file = 'tickets_data.json'
        self.ensure_data_file()

    def ensure_data_file(self):
        """Ensure tickets data file exists"""
        if not os.path.exists(self.tickets_file):
            with open(self.tickets_file, 'w') as f:
                json.dump({}, f, indent=2)

    def load_tickets(self) -> dict:
        """Load all tickets from file"""
        try:
            with open(self.tickets_file, 'r') as f:
                return json.load(f)
        except:
            return {}

    def save_tickets(self, tickets: dict):
        """Save tickets to file"""
        try:
            with open(self.tickets_file, 'w') as f:
                json.dump(tickets, f, indent=2)
        except Exception as e:
            print(f"Error saving tickets: {e}")

    def create_ticket(self, user_id: int, title: str, description: str, category: str, guild_id: int) -> str:
        """Create a new ticket"""
        ticket_id = str(uuid.uuid4())[:8].upper()

        tickets = self.load_tickets()

        ticket_data = {
            'id': ticket_id,
            'user_id': user_id,
            'title': title,
            'description': description,
            'category': category,
            'status': 'open',
            'priority': 'medium',
            'guild_id': guild_id,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'closed_at': None,
            'comments': []
        }

        tickets[ticket_id] = ticket_data
        self.save_tickets(tickets)
        return ticket_id

    @app_commands.command(name='createticket', description='Create a support ticket')
    @app_commands.describe(
        title='Ticket title',
        description='Ticket description',
        category='Ticket category'
    )
    @app_commands.choices(category=[
        app_commands.Choice(name='🐛 Bug Report', value='bug'),
        app_commands.Choice(name='💡 Feature Request', value='feature'),
        app_commands.Choice(name='❓ Support', value='support'),
        app_commands.Choice(name='📝 General', value='general')
    ])
    async def create_ticket_cmd(self, interaction: discord.Interaction, title: str, description: str, category: str = 'general'):
        """Create a new ticket via slash command"""
        try:
            ticket_id = self.create_ticket(
                interaction.user.id,
                title,
                description,
                category,
                interaction.guild_id
            )

            embed = discord.Embed(
                title='✅ Ticket Created',
                description='Your support ticket has been created successfully.',
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            embed.add_field(name='Ticket ID', value=f'`{ticket_id}`', inline=False)
            embed.add_field(name='Category', value=category.capitalize(), inline=True)
            embed.add_field(name='Status', value='🟢 Open', inline=True)
            embed.set_footer(text='Use /viewticket to check status')

            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"Error in create_ticket_cmd: {e}")
            await interaction.response.send_message(f'❌ Error: {str(e)[:100]}', ephemeral=True)

    @app_commands.command(name='viewticket', description='View ticket details')
    @app_commands.describe(ticket_id='The ticket ID')
    async def view_ticket_cmd(self, interaction: discord.Interaction, ticket_id: str):
        """View a specific ticket"""
        try:
            tickets = self.load_tickets()
            ticket_id = ticket_id.upper()

            if ticket_id not in tickets:
                await interaction.response.send_message(f'❌ Ticket `{ticket_id}` not found', ephemeral=True)
                return

            ticket = tickets[ticket_id]

            embed = discord.Embed(
                title=f'🎫 {ticket["title"]}',
                description=ticket['description'],
                color=discord.Color.blurple(),
                timestamp=datetime.now()
            )
            embed.add_field(name='ID', value=f'`{ticket["id"]}`', inline=False)
            embed.add_field(name='Status', value=ticket['status'].capitalize(), inline=True)
            embed.add_field(name='Category', value=ticket['category'].capitalize(), inline=True)
            embed.add_field(name='Created', value=f'<t:{int(datetime.fromisoformat(ticket["created_at"]).timestamp())}:R>', inline=True)

            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"Error in view_ticket_cmd: {e}")
            await interaction.response.send_message(f'❌ Error: {str(e)[:100]}', ephemeral=True)

    @app_commands.command(name='mytickets', description='View your tickets')
    async def my_tickets_cmd(self, interaction: discord.Interaction):
        """View user's tickets"""
        try:
            tickets = self.load_tickets()
            user_tickets = [t for t in tickets.values() if t['user_id'] == interaction.user.id]

            if not user_tickets:
                await interaction.response.send_message('📭 You have no tickets', ephemeral=True)
                return

            embed = discord.Embed(
                title='📋 My Tickets',
                color=discord.Color.blurple(),
                timestamp=datetime.now()
            )

            for ticket in user_tickets[-10:]:
                status_emoji = '🟢' if ticket['status'] == 'open' else '⚫'
                embed.add_field(
                    name=f'{status_emoji} {ticket["title"][:50]}',
                    value=f"ID: `{ticket['id']}`\nCategory: {ticket['category']}",
                    inline=False
                )

            embed.set_footer(text=f'Total: {len(user_tickets)} tickets')
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"Error in my_tickets_cmd: {e}")
            await interaction.response.send_message(f'❌ Error: {str(e)[:100]}', ephemeral=True)

    @app_commands.command(name='alltickets', description='View all tickets (Admin)')
    async def all_tickets_cmd(self, interaction: discord.Interaction):
        """View all tickets"""
        try:
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message('❌ Admin only', ephemeral=True)
                return

            tickets = self.load_tickets()

            if not tickets:
                await interaction.response.send_message('📭 No tickets', ephemeral=True)
                return

            embed = discord.Embed(
                title='📋 All Tickets',
                color=discord.Color.blurple(),
                timestamp=datetime.now()
            )

            open_count = len([t for t in tickets.values() if t['status'] == 'open'])
            closed_count = len([t for t in tickets.values() if t['status'] == 'closed'])

            embed.add_field(
                name='📊 Summary',
                value=f'Open: {open_count} | Closed: {closed_count}',
                inline=False
            )

            for ticket in list(tickets.values())[-10:]:
                status_emoji = '🟢' if ticket['status'] == 'open' else '⚫'
                embed.add_field(
                    name=f'{status_emoji} {ticket["title"][:40]}',
                    value=f"ID: `{ticket['id']}`\nCategory: {ticket['category']}",
                    inline=False
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"Error in all_tickets_cmd: {e}")
            await interaction.response.send_message(f'❌ Error: {str(e)[:100]}', ephemeral=True)

    @app_commands.command(name='closeticket', description='Close a ticket')
    @app_commands.describe(ticket_id='The ticket ID to close')
    async def close_ticket_cmd(self, interaction: discord.Interaction, ticket_id: str):
        """Close a ticket"""
        try:
            tickets = self.load_tickets()
            ticket_id = ticket_id.upper()

            if ticket_id not in tickets:
                await interaction.response.send_message(f'❌ Ticket `{ticket_id}` not found', ephemeral=True)
                return

            ticket = tickets[ticket_id]

            # Check permission
            if ticket['user_id'] != interaction.user.id and not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message('❌ You can only close your own tickets', ephemeral=True)
                return

            ticket['status'] = 'closed'
            ticket['closed_at'] = datetime.now().isoformat()
            self.save_tickets(tickets)

            embed = discord.Embed(
                title='✅ Ticket Closed',
                description=f'Ticket `{ticket_id}` has been closed',
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"Error in close_ticket_cmd: {e}")
            await interaction.response.send_message(f'❌ Error: {str(e)[:100]}', ephemeral=True)


async def setup(bot):
    await bot.add_cog(Tickets(bot))
