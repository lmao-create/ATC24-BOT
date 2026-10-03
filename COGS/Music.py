import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import yt_dlp
from collections import deque
import re

class Music(commands.Cog):
    """Music player cog for Discord bot"""

    def __init__(self, bot):
        self.bot = bot
        self.queues = {}  # Guild ID -> deque of songs
        self.currently_playing = {}  # Guild ID -> current song info
        self.vc = {}  # Guild ID -> voice client

    def get_queue(self, guild_id):
        """Get or create queue for a guild"""
        if guild_id not in self.queues:
            self.queues[guild_id] = deque()
        return self.queues[guild_id]

    async def search_youtube(self, query: str):
        """Search YouTube for a video"""
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch',
            'noplaylist': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                loop = asyncio.get_event_loop()
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(f"ytsearch1:{query}", download=False))
                if info and 'entries' in info:
                    video = info['entries'][0]
                    return {
                        'title': video.get('title', 'Unknown'),
                        'url': video.get('url', ''),
                        'duration': video.get('duration', 0),
                        'thumbnail': video.get('thumbnail', ''),
                        'webpage_url': video.get('webpage_url', '')
                    }
        except Exception as e:
            print(f"Error searching YouTube: {e}")
        return None

    def format_duration(self, seconds):
        """Format duration in seconds to MM:SS"""
        if not seconds or seconds < 0:
            return "0:00"
        return f"{seconds//60}:{seconds%60:02d}"

    async def play_next(self, guild_id, channel):
        """Play the next song in queue"""
        queue = self.get_queue(guild_id)

        if not queue:
            self.currently_playing[guild_id] = None
            # Clear channel topic when queue is empty
            if isinstance(channel, discord.TextChannel):
                try:
                    await channel.edit(topic="")
                except Exception as e:
                    print(f"Error clearing channel topic: {e}")
            return

        song = queue.popleft()
        self.currently_playing[guild_id] = song

        vc = self.bot.get_guild(guild_id).voice_client if self.bot.get_guild(guild_id) else None
        if not vc or not vc.is_connected():
            return

        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
                'socket_timeout': 30,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                loop = asyncio.get_event_loop()
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(song['webpage_url'], download=False))

                # Get the best audio URL
                url = info.get('url') or info.get('formats', [{}])[0].get('url')
                if not url:
                    print(f"Could not extract URL for {song['title']}")
                    await self.play_next(guild_id, channel)
                    return

            audio_source = discord.FFmpegPCMAudio(url, options="-vn -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5")

            # Create a callback for when the song finishes
            def after_song(error):
                if error:
                    print(f"Playback error: {error}")
                # Schedule the next song to play
                asyncio.run_coroutine_threadsafe(self.play_next(guild_id, channel), self.bot.loop)

            vc.play(audio_source, after=after_song)

            embed = discord.Embed(
                title='▶️ Now Playing',
                description=song['title'],
                color=discord.Color.purple(),
            )
            embed.add_field(name='Duration', value=self.format_duration(song['duration']), inline=True)
            embed.set_thumbnail(url=song['thumbnail'])
            embed.set_footer(text=f"Queue: {len(queue)} songs")

            if isinstance(channel, discord.TextChannel):
                try:
                    await channel.send(embed=embed)
                except Exception as e:
                    print(f"Error sending queue message: {e}")

                # Update channel topic asynchronously without blocking
                try:
                    topic = f"🎵 Now Playing: {song['title'][:80]}"
                    asyncio.create_task(channel.edit(topic=topic))
                except Exception as e:
                    print(f"Error updating channel topic: {e}")
        except Exception as e:
            print(f"Error playing audio: {e}")
            await self.play_next(guild_id, channel)

    @app_commands.command(name='play', description='Play a song from YouTube')
    @app_commands.describe(query='Song name or YouTube URL')
    async def play(self, interaction: discord.Interaction, query: str):
        """Play a song"""
        await interaction.response.defer()

        # Check if user is in a voice channel
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send('❌ You must be in a voice channel to play music.', ephemeral=True)
            return

        # Connect to voice channel if not already connected
        guild_id = interaction.guild.id
        vc = interaction.guild.voice_client

        if not vc or not vc.is_connected():
            try:
                vc = await interaction.user.voice.channel.connect()
                self.vc[guild_id] = vc
            except Exception as e:
                await interaction.followup.send(f'❌ Failed to connect to voice channel: {e}', ephemeral=True)
                return

        # Check if it's a URL or search query
        is_url = query.startswith(('http://', 'https://', 'www.'))

        if is_url:
            # Direct URL
            await interaction.followup.send('🔄 Loading URL...', ephemeral=True)
            song_info = await self.get_video_info(query)
        else:
            # Search for the song
            await interaction.followup.send('🔍 Searching...', ephemeral=True)
            song_info = await self.search_youtube(query)

        if not song_info:
            await interaction.followup.send('❌ No results found.', ephemeral=True)
            return

        # Add to queue
        queue = self.get_queue(guild_id)
        queue.append(song_info)

        embed = discord.Embed(
            title='✅ Added to Queue',
            description=song_info['title'],
            color=discord.Color.green(),
        )
        embed.add_field(name='Position', value=f"#{len(queue)}", inline=True)
        embed.add_field(name='Duration', value=self.format_duration(song_info['duration']), inline=True)
        embed.set_thumbnail(url=song_info['thumbnail'])

        await interaction.followup.send(embed=embed)

        # Play if nothing is currently playing
        if not vc.is_playing() and not self.currently_playing.get(guild_id):
            await self.play_next(guild_id, interaction.channel)

    async def get_video_info(self, url: str):
        """Get info from a direct YouTube URL"""
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                loop = asyncio.get_event_loop()
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
                return {
                    'title': info.get('title', 'Unknown'),
                    'url': info.get('url', ''),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'webpage_url': info.get('webpage_url', url)
                }
        except Exception as e:
            print(f"Error getting video info: {e}")
        return None

    @app_commands.command(name='skip', description='Skip the current song')
    async def skip(self, interaction: discord.Interaction):
        """Skip current song"""
        # Check if user is in a voice channel
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message('❌ You must be in a voice channel.', ephemeral=True)
            return

        vc = interaction.guild.voice_client
        if not vc or not vc.is_playing():
            await interaction.response.send_message('❌ No song is currently playing.', ephemeral=True)
            return

        vc.stop()
        await interaction.response.send_message('⏭️ Skipped to next song.')
        await self.play_next(interaction.guild.id, interaction.channel)

    @app_commands.command(name='stop', description='Stop playing music')
    async def stop(self, interaction: discord.Interaction):
        """Stop playing music"""
        # Check if user is in a voice channel
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message('❌ You must be in a voice channel.', ephemeral=True)
            return

        vc = interaction.guild.voice_client
        if not vc or not vc.is_connected():
            await interaction.response.send_message('❌ Bot is not in a voice channel.', ephemeral=True)
            return

        vc.stop()
        guild_id = interaction.guild.id
        self.queues[guild_id] = deque()
        self.currently_playing[guild_id] = None

        await interaction.response.send_message('⏹️ Music stopped and queue cleared.')

    @app_commands.command(name='pause', description='Pause the current song')
    async def pause(self, interaction: discord.Interaction):
        """Pause current song"""
        vc = interaction.guild.voice_client
        if not vc or not vc.is_playing():
            await interaction.response.send_message('❌ No song is currently playing.', ephemeral=True)
            return

        vc.pause()
        await interaction.response.send_message('⏸️ Music paused.')

    @app_commands.command(name='resume', description='Resume the paused song')
    async def resume(self, interaction: discord.Interaction):
        """Resume paused song"""
        vc = interaction.guild.voice_client
        if not vc or not vc.is_paused():
            await interaction.response.send_message('❌ No paused song to resume.', ephemeral=True)
            return

        vc.resume()
        await interaction.response.send_message('▶️ Music resumed.')

    @app_commands.command(name='queue', description='View the current queue')
    async def queue(self, interaction: discord.Interaction):
        """View current queue"""
        guild_id = interaction.guild.id
        queue = self.get_queue(guild_id)

        if not queue:
            await interaction.response.send_message('❌ Queue is empty.', ephemeral=True)
            return

        embed = discord.Embed(
            title='🎵 Music Queue',
            color=discord.Color.purple(),
        )

        current = self.currently_playing.get(guild_id)
        if current:
            embed.add_field(
                name='Now Playing',
                value=f"**{current['title']}**\n{self.format_duration(current['duration'])}",
                inline=False
            )

        queue_text = ''
        for idx, song in enumerate(list(queue)[:10], 1):
            queue_text += f"{idx}. **{song['title']}** - {self.format_duration(song['duration'])}\n"

        if queue_text:
            embed.add_field(name='Upcoming', value=queue_text, inline=False)

        if len(queue) > 10:
            embed.set_footer(text=f"... and {len(queue) - 10} more songs")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='leave', description='Disconnect bot from voice channel')
    async def leave(self, interaction: discord.Interaction):
        """Disconnect from voice channel"""
        vc = interaction.guild.voice_client
        if not vc or not vc.is_connected():
            await interaction.response.send_message('❌ Bot is not in a voice channel.', ephemeral=True)
            return

        guild_id = interaction.guild.id
        self.queues[guild_id] = deque()
        self.currently_playing[guild_id] = None

        await vc.disconnect()
        await interaction.response.send_message('👋 Disconnected from voice channel.')

# Setup function to load the cog
async def setup(bot):
    await bot.add_cog(Music(bot))
