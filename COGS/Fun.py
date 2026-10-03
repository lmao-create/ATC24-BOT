import discord
from discord.ext import commands
from discord import app_commands
import random
from datetime import datetime

class Fun(commands.Cog):
    """Fun and entertaining commands"""

    def __init__(self, bot):
        self.bot = bot

    # 8-ball responses
    EIGHTBALL_RESPONSES = {
        'positive': [
            'Yes, definitely!',
            'Absolutely!',
            'For sure!',
            'You bet!',
            'Signs point to yes',
            'Looks good!',
            'It is certain',
            'Most likely',
            'Outlook good',
            'Yes!',
        ],
        'negative': [
            'No way!',
            'Definitely not',
            'Don\'t count on it',
            'No',
            'Outlook not so good',
            'Chances are slim',
            'Very doubtful',
            'My sources say no',
            'Not happening',
            'Nope!',
        ],
        'maybe': [
            'Ask again later',
            'Maybe?',
            'Can\'t predict now',
            'Uncertain',
            'Don\'t know yet',
            'It\'s unclear',
            'Concentrate and ask again',
            'The answer is fuzzy',
            'Possibly...',
            'Hmm, unsure',
        ]
    }

    @app_commands.command(name='8ball', description='Ask the magic 8-ball a question')
    @app_commands.describe(question='Your question for the magic 8-ball')
    async def eightball(self, interaction: discord.Interaction, question: str):
        """Ask the magic 8-ball for wisdom"""

        # Pick random category and response
        category = random.choice(list(self.EIGHTBALL_RESPONSES.keys()))
        response = random.choice(self.EIGHTBALL_RESPONSES[category])

        # Color based on response type
        colors = {
            'positive': discord.Color.green(),
            'negative': discord.Color.red(),
            'maybe': discord.Color.yellow()
        }

        embed = discord.Embed(
            title='🎱 Magic 8-Ball',
            color=colors[category],
            timestamp=datetime.now()
        )
        embed.add_field(name='Your Question', value=f'*{question}*', inline=False)
        embed.add_field(name='The Answer', value=f'**{response}**', inline=False)
        embed.set_footer(text=f'Asked by {interaction.user.name}')

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='flip', description='Flip a coin')
    async def flip(self, interaction: discord.Interaction):
        """Flip a coin - heads or tails"""
        result = random.choice(['Heads', 'Tails'])
        emoji = '🪙'

        embed = discord.Embed(
            title=f'{emoji} Coin Flip',
            description=f'**{result}**!',
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        embed.set_footer(text=f'Flipped by {interaction.user.name}')

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='roll', description='Roll a dice')
    @app_commands.describe(dice='Dice notation (e.g., 1d20, 2d6, 3d10). Default: 1d6')
    async def roll(self, interaction: discord.Interaction, dice: str = '1d6'):
        """Roll dice in standard notation (e.g., 1d20, 2d6)"""

        try:
            # Parse dice notation
            parts = dice.lower().split('d')
            if len(parts) != 2:
                await interaction.response.send_message('❌ Invalid dice notation. Use format like: 1d20, 2d6, 3d10', ephemeral=True)
                return

            num_dice = int(parts[0])
            num_sides = int(parts[1])

            # Validate ranges
            if num_dice < 1 or num_dice > 100:
                await interaction.response.send_message('❌ Number of dice must be 1-100', ephemeral=True)
                return
            if num_sides < 2 or num_sides > 1000:
                await interaction.response.send_message('❌ Dice sides must be 2-1000', ephemeral=True)
                return

            # Roll the dice
            rolls = [random.randint(1, num_sides) for _ in range(num_dice)]
            total = sum(rolls)

            # Build response
            rolls_str = ', '.join(map(str, rolls))
            if num_dice > 10:
                rolls_str = f'{len(rolls)} rolls'

            embed = discord.Embed(
                title='🎲 Dice Roll',
                color=discord.Color.blurple(),
                timestamp=datetime.now()
            )
            embed.add_field(name='Dice', value=f'**{dice.upper()}**', inline=True)
            embed.add_field(name='Total', value=f'**{total}**', inline=True)
            if num_dice <= 10:
                embed.add_field(name='Rolls', value=rolls_str, inline=False)
            embed.set_footer(text=f'Rolled by {interaction.user.name}')

            await interaction.response.send_message(embed=embed)

        except ValueError:
            await interaction.response.send_message('❌ Invalid dice notation. Use format like: 1d20, 2d6, 3d10', ephemeral=True)

    @app_commands.command(name='choose', description='Let the bot choose for you')
    @app_commands.describe(options='Comma-separated options (e.g., pizza, tacos, burgers)')
    async def choose(self, interaction: discord.Interaction, options: str):
        """Pick a random choice from your options"""

        # Parse options
        choices = [option.strip() for option in options.split(',')]
        choices = [c for c in choices if c]  # Remove empty strings

        if len(choices) < 2:
            await interaction.response.send_message('❌ Please provide at least 2 options separated by commas.', ephemeral=True)
            return

        if len(choices) > 50:
            await interaction.response.send_message('❌ Please provide no more than 50 options.', ephemeral=True)
            return

        # Pick choice
        choice = random.choice(choices)

        embed = discord.Embed(
            title='🤔 Hmm, let me think...',
            description=f'**I choose: {choice}**',
            color=discord.Color.purple(),
            timestamp=datetime.now()
        )
        embed.add_field(name='Options', value=', '.join(choices), inline=False)
        embed.set_footer(text=f'Chosen for {interaction.user.name}')

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='rps', description='Play rock-paper-scissors')
    @app_commands.describe(choice='Your choice: rock, paper, or scissors')
    async def rps(self, interaction: discord.Interaction, choice: str):
        """Play rock-paper-scissors against the bot"""

        valid_choices = ['rock', 'paper', 'scissors']
        user_choice = choice.lower()

        if user_choice not in valid_choices:
            await interaction.response.send_message(f'❌ Invalid choice. Choose from: {", ".join(valid_choices)}', ephemeral=True)
            return

        bot_choice = random.choice(valid_choices)

        # Determine winner
        if user_choice == bot_choice:
            result = "It's a tie! 🤝"
            color = discord.Color.yellow()
        elif (user_choice == 'rock' and bot_choice == 'scissors') or \
             (user_choice == 'paper' and bot_choice == 'rock') or \
             (user_choice == 'scissors' and bot_choice == 'paper'):
            result = "You win! 🎉"
            color = discord.Color.green()
        else:
            result = "I win! 🤖"
            color = discord.Color.red()

        embed = discord.Embed(
            title='✋ Rock-Paper-Scissors',
            color=color,
            timestamp=datetime.now()
        )
        embed.add_field(name='Your Choice', value=f'**{user_choice.capitalize()}**', inline=True)
        embed.add_field(name='My Choice', value=f'**{bot_choice.capitalize()}**', inline=True)
        embed.add_field(name='Result', value=result, inline=False)
        embed.set_footer(text=f'Played by {interaction.user.name}')

        await interaction.response.send_message(embed=embed)

# Setup function to load the cog
async def setup(bot):
    await bot.add_cog(Fun(bot))
