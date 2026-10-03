import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime, timedelta

class Economy(commands.Cog):
    """Economy system for the Discord bot"""

    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'economy_data.json'
        self.load_data()

    def load_data(self):
        """Load economy data from file"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                self.economy_data = json.load(f)
        else:
            self.economy_data = {}

    def save_data(self):
        """Save economy data to file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.economy_data, f, indent=4)

    def get_user_data(self, user_id):
        """Get or create user data"""
        user_id = str(user_id)
        if user_id not in self.economy_data:
            self.economy_data[user_id] = {
                'balance': 0,
                'bank_balance': 0,
                'last_work': None,
                'last_crime': None,
                'last_rob': None
            }
            self.save_data()
        # Ensure existing users have bank_balance field
        elif 'bank_balance' not in self.economy_data[user_id]:
            self.economy_data[user_id]['bank_balance'] = 0
            self.save_data()
        return self.economy_data[user_id]

    def can_action(self, user_id, action_type, cooldown_minutes=5):
        """Check if user can perform an action (cooldown system)"""
        user_data = self.get_user_data(user_id)
        last_action = user_data.get(f'last_{action_type}')

        if last_action is None:
            return True, 0

        last_time = datetime.fromisoformat(last_action)
        now = datetime.now()
        diff = (now - last_time).total_seconds() / 60

        if diff < cooldown_minutes:
            return False, int(cooldown_minutes - diff)
        return True, 0

    def update_action_time(self, user_id, action_type):
        """Update the last action time"""
        user_data = self.get_user_data(user_id)
        user_data[f'last_{action_type}'] = datetime.now().isoformat()
        self.save_data()

    @app_commands.command(name='work', description='Work and earn money')
    async def work(self, interaction: discord.Interaction):
        """Work to earn money"""
        user_id = interaction.user.id
        can_work, cooldown = self.can_action(user_id, 'work', 3)

        if not can_work:
            await interaction.response.send_message(f'❌ You can work again in **{cooldown} minutes**.', ephemeral=True)
            return

        import random
        earnings = random.randint(50, 200)
        user_data = self.get_user_data(user_id)
        user_data['balance'] += earnings
        self.update_action_time(user_id, 'work')

        await interaction.response.send_message(f'💼 You worked hard and earned **${earnings}**!\nTotal balance: **${user_data["balance"]}**')

    @app_commands.command(name='crime', description='Commit a crime and earn money')
    async def crime(self, interaction: discord.Interaction):
        """Commit a crime to earn money (risky)"""
        user_id = interaction.user.id
        can_crime, cooldown = self.can_action(user_id, 'crime', 5)

        if not can_crime:
            await interaction.response.send_message(f'❌ You can commit a crime again in **{cooldown} minutes**.', ephemeral=True)
            return

        import random
        success_rate = random.randint(1, 100)
        user_data = self.get_user_data(user_id)

        if success_rate > 50:  # 50% success rate
            earnings = random.randint(100, 400)
            user_data['balance'] += earnings
            self.update_action_time(user_id, 'crime')
            await interaction.response.send_message(f'🔓 Crime successful! You earned **${earnings}**!\nTotal balance: **${user_data["balance"]}**')
        else:
            loss = random.randint(50, 150)
            user_data['balance'] = max(0, user_data['balance'] - loss)
            self.update_action_time(user_id, 'crime')
            await interaction.response.send_message(f'🚨 Crime failed! You lost **${loss}**!\nTotal balance: **${user_data["balance"]}**')

        self.save_data()

    @app_commands.command(name='rob', description='Rob another user')
    @app_commands.describe(target='The user to rob')
    async def rob(self, interaction: discord.Interaction, target: discord.Member):
        """Rob another user"""
        user_id = interaction.user.id
        target_id = target.id

        if target_id == user_id:
            await interaction.response.send_message('❌ You cannot rob yourself!', ephemeral=True)
            return

        can_rob, cooldown = self.can_action(user_id, 'rob', 10)

        if not can_rob:
            await interaction.response.send_message(f'❌ You can rob again in **{cooldown} minutes**.', ephemeral=True)
            return

        import random
        success_rate = random.randint(1, 100)
        robber_data = self.get_user_data(user_id)
        target_data = self.get_user_data(target_id)

        if target_data['balance'] == 0:
            await interaction.response.send_message(f'❌ {target.mention} has no money to rob!', ephemeral=True)
            return

        if success_rate > 60:  # 40% success rate
            steal_amount = random.randint(max(10, target_data['balance'] // 4), target_data['balance'] // 2)
            robber_data['balance'] += steal_amount
            target_data['balance'] -= steal_amount
            self.update_action_time(user_id, 'rob')
            self.save_data()
            await interaction.response.send_message(f'💰 Rob successful! You stole **${steal_amount}** from {target.mention}!\nYour balance: **${robber_data["balance"]}**')
        else:
            loss = random.randint(50, 200)
            robber_data['balance'] = max(0, robber_data['balance'] - loss)
            self.update_action_time(user_id, 'rob')
            self.save_data()
            await interaction.response.send_message(f'🚨 Rob failed! You were caught and lost **${loss}**!\nYour balance: **${robber_data["balance"]}**')

    @app_commands.command(name='add_money', description='[ADMIN] Add money to a user')
    @app_commands.describe(user='The user to give money to', amount='Amount of money to add')
    async def add_money(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        """Add money to a user (admin only)"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message('❌ Only administrators can use this command.', ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message('❌ Amount must be greater than 0.', ephemeral=True)
            return

        user_data = self.get_user_data(user.id)
        user_data['balance'] += amount
        self.save_data()

        await interaction.response.send_message(f'✅ Added **${amount}** to {user.mention}\'s balance.\nNew balance: **${user_data["balance"]}**')

    @app_commands.command(name='remove_money', description='[ADMIN] Remove money from a user')
    @app_commands.describe(user='The user to remove money from', amount='Amount of money to remove')
    async def remove_money(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        """Remove money from a user (admin only)"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message('❌ Only administrators can use this command.', ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message('❌ Amount must be greater than 0.', ephemeral=True)
            return

        user_data = self.get_user_data(user.id)
        user_data['balance'] = max(0, user_data['balance'] - amount)
        self.save_data()

        await interaction.response.send_message(f'✅ Removed **${amount}** from {user.mention}\'s balance.\nNew balance: **${user_data["balance"]}**')

    @app_commands.command(name='balance', description='Check your balance')
    @app_commands.describe(user='The user to check balance for (optional)')
    async def balance(self, interaction: discord.Interaction, user: discord.Member = None):
        """Check your or another user's balance"""
        if user is None:
            user = interaction.user

        user_data = self.get_user_data(user.id)
        wallet = user_data['balance']
        bank = user_data['bank_balance']
        total = wallet + bank

        embed = discord.Embed(
            title=f'💰 {user.name}\'s Balance',
            color=discord.Color.gold()
        )
        embed.add_field(name='Wallet', value=f'**${wallet}**', inline=True)
        embed.add_field(name='Bank', value=f'**${bank}**', inline=True)
        embed.add_field(name='Total', value=f'**${total}**', inline=False)
        embed.set_thumbnail(url=user.avatar.url if user.avatar else None)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='deposit', description='Deposit money into your bank account')
    @app_commands.describe(amount='Amount of money to deposit')
    async def deposit(self, interaction: discord.Interaction, amount: int):
        """Deposit money from wallet to bank"""
        user_id = interaction.user.id
        user_data = self.get_user_data(user_id)

        if amount <= 0:
            await interaction.response.send_message('❌ Amount must be greater than 0.', ephemeral=True)
            return

        if user_data['balance'] < amount:
            await interaction.response.send_message(f'❌ You don\'t have enough money! Wallet: **${user_data["balance"]}**.', ephemeral=True)
            return

        user_data['balance'] -= amount
        user_data['bank_balance'] += amount
        self.save_data()

        embed = discord.Embed(
            title='🏦 Deposit Successful',
            description=f'Deposited **${amount}** into your bank account.',
            color=discord.Color.green()
        )
        embed.add_field(name='Wallet', value=f'**${user_data["balance"]}**', inline=True)
        embed.add_field(name='Bank', value=f'**${user_data["bank_balance"]}**', inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='withdraw', description='Withdraw money from your bank account')
    @app_commands.describe(amount='Amount of money to withdraw')
    async def withdraw(self, interaction: discord.Interaction, amount: int):
        """Withdraw money from bank to wallet"""
        user_id = interaction.user.id
        user_data = self.get_user_data(user_id)

        if amount <= 0:
            await interaction.response.send_message('❌ Amount must be greater than 0.', ephemeral=True)
            return

        if user_data['bank_balance'] < amount:
            await interaction.response.send_message(f'❌ You don\'t have enough money in your bank! Bank balance: **${user_data["bank_balance"]}**.', ephemeral=True)
            return

        user_data['bank_balance'] -= amount
        user_data['balance'] += amount
        self.save_data()

        embed = discord.Embed(
            title='💸 Withdrawal Successful',
            description=f'Withdrew **${amount}** from your bank account.',
            color=discord.Color.green()
        )
        embed.add_field(name='Wallet', value=f'**${user_data["balance"]}**', inline=True)
        embed.add_field(name='Bank', value=f'**${user_data["bank_balance"]}**', inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='leaderboard', description='View the richest users')
    @app_commands.describe(page='Page number (default: 1)')
    async def leaderboard(self, interaction: discord.Interaction, page: int = 1):
        """Display leaderboard of richest users"""
        if not self.economy_data:
            await interaction.response.send_message('❌ No economy data yet!', ephemeral=True)
            return

        # Sort users by total balance (wallet + bank)
        sorted_users = sorted(
            self.economy_data.items(),
            key=lambda x: x[1]['balance'] + x[1]['bank_balance'],
            reverse=True
        )

        # Pagination
        per_page = 10
        total_pages = (len(sorted_users) + per_page - 1) // per_page

        if page < 1 or page > total_pages:
            await interaction.response.send_message(f'❌ Invalid page number. Pages: 1-{total_pages}', ephemeral=True)
            return

        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_users = sorted_users[start_idx:end_idx]

        # Build leaderboard text
        leaderboard_text = ''
        for idx, (user_id, user_data) in enumerate(page_users, start=start_idx + 1):
            total = user_data['balance'] + user_data['bank_balance']
            try:
                user = await self.bot.fetch_user(int(user_id))
                username = user.name
            except:
                username = f'User {user_id}'

            medal = ['🥇', '🥈', '🥉'][idx - 1] if idx <= 3 else f'{idx}.'
            leaderboard_text += f'{medal} **{username}** - **${total:,}**\n'

        embed = discord.Embed(
            title='💰 Economy Leaderboard',
            description=leaderboard_text,
            color=discord.Color.gold()
        )
        embed.set_footer(text=f'Page {page}/{total_pages} • Top {len(sorted_users)} users')

        await interaction.response.send_message(embed=embed)

# Setup function to load the cog
async def setup(bot):
    await bot.add_cog(Economy(bot))
