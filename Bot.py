import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import glob
import ssl
import aiohttp

# Load environment variables from .env file
load_dotenv()

# Get the token from environment variable
TOKEN = os.getenv('TOKEN')

# Create bot with command prefix
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    """Called when the bot is ready"""
    print(f'{bot.user} has connected to Discord!')

    # Set bot status/activity
    activity = discord.Activity(type=discord.ActivityType.custom, name='Helping PTC')
    await bot.change_presence(activity=activity)

    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Error syncing commands: {e}')

@bot.command(name='ping')
async def ping(ctx):
    """Respond with pong and bot latency"""
    latency = round(bot.latency * 1000)
    await ctx.send(f'Pong! {latency}ms')

@bot.tree.command(name='ping', description='Check bot latency and status')
async def ping_slash(interaction: discord.Interaction):
    """Slash command version with enhanced info"""
    latency = round(bot.latency * 1000)

    embed = discord.Embed(
        title='🏓 Pong!',
        color=discord.Color.blurple()
    )
    embed.add_field(name='Bot Latency', value=f'**{latency}ms**', inline=True)
    embed.add_field(name='Status', value='✅ Helping PTC', inline=True)
    embed.add_field(name='Guilds', value=f'**{len(bot.guilds)}**', inline=True)
    embed.set_footer(text=f'Responded in ~{round(bot.latency * 1000)}ms')

    await interaction.response.send_message(embed=embed)

async def load_cogs():
    """Load all cogs from the COGS folder"""
    cogs_folder = 'COGS'

    if not os.path.exists(cogs_folder):
        print(f'COGS folder not found!')
        return

    # Load all Python files from COGS folder
    cog_files = glob.glob(os.path.join(cogs_folder, '*.py'))

    for cog_file in cog_files:
        cog_name = os.path.basename(cog_file)[:-3]  # Remove .py extension
        try:
            await bot.load_extension(f'COGS.{cog_name}')
            print(f'[OK] Loaded {cog_name} cog')
        except Exception as e:
            print(f'[ERROR] Error loading {cog_name} cog: {e}')

async def main():
    """Main startup function"""
    # Create SSL context that bypasses certificate verification
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    # Create connector and session with SSL context
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    session = aiohttp.ClientSession(connector=connector)

    # Manually set the bot's HTTP client session
    bot.http.session = session

    async with bot:
        await load_cogs()

        try:
            await bot.start(TOKEN, reconnect=True)
        except Exception as e:
            print(f'Error starting bot: {e}')
        finally:
            await session.close()

# Run the bot
if __name__ == '__main__':
    asyncio.run(main())
