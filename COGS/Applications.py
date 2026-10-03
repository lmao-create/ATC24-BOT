import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime
from typing import Optional


class ApplicationModal(discord.ui.Modal, title="Submit Your Application"):
    """Modal for submitting applications"""

    name = discord.ui.TextInput(
        label="Full Name",
        placeholder="Enter your full name",
        required=True,
        max_length=100
    )

    email = discord.ui.TextInput(
        label="Email Address",
        placeholder="your.email@example.com",
        required=True,
        max_length=100
    )

    reason = discord.ui.TextInput(
        label="Why do you want to join?",
        placeholder="Tell us why you're interested...",
        required=True,
        max_length=1000,
        style=discord.TextStyle.paragraph
    )

    experience = discord.ui.TextInput(
        label="Relevant Experience",
        placeholder="Tell us about your experience...",
        required=True,
        max_length=1000,
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission"""
        cog = interaction.client.get_cog("Applications")
        await cog.save_application(
            interaction.user.id,
            interaction.user.name,
            self.name.value,
            self.email.value,
            self.reason.value,
            self.experience.value,
            interaction.guild_id,
            interaction
        )


class Applications(commands.Cog):
    """Application management system for unlimited applications"""

    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'applications_data.json'
        self.config_file = 'applications_config.json'
        self.load_applications()
        self.load_config()

    def load_applications(self):
        """Load applications from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.applications = json.load(f)
            except:
                self.applications = {}
        else:
            self.applications = {}

    def save_applications(self):
        """Save applications to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.applications, f, indent=2)

    def load_config(self):
        """Load configuration from JSON file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            except:
                self.config = {}
        else:
            self.config = {}

    def save_config(self):
        """Save configuration to JSON file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def get_results_channel(self, guild_id: int) -> Optional[int]:
        """Get the results channel ID for a guild"""
        guild_key = str(guild_id)
        return self.config.get(guild_key, {}).get('results_channel')

    def set_results_channel(self, guild_id: int, channel_id: int):
        """Set the results channel for a guild"""
        guild_key = str(guild_id)
        if guild_key not in self.config:
            self.config[guild_key] = {}
        self.config[guild_key]['results_channel'] = channel_id
        self.save_config()

    async def save_application(self, user_id: int, username: str, name: str,
                               email: str, reason: str, experience: str,
                               guild_id: Optional[int], interaction: discord.Interaction):
        """Save application data"""
        app_id = f"{user_id}_{datetime.now().timestamp()}"

        application_data = {
            'id': app_id,
            'user_id': user_id,
            'username': username,
            'full_name': name,
            'email': email,
            'reason': reason,
            'experience': experience,
            'guild_id': guild_id,
            'status': 'pending',
            'submitted_at': datetime.now().isoformat(),
            'reviewed_at': None,
            'reviewer_id': None
        }

        self.applications[app_id] = application_data
        self.save_applications()

        # Send confirmation embed
        embed = discord.Embed(
            title='✅ Application Submitted',
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name='Application ID',
                        value=f'`{app_id}`', inline=False)
        embed.add_field(name='Status', value='**Pending Review**', inline=True)
        embed.add_field(
            name='Submitted At', value=f'<t:{int(datetime.now().timestamp())}:F>', inline=True)
        embed.add_field(name='Name', value=name, inline=True)
        embed.add_field(name='Email', value=email, inline=True)
        embed.set_footer(
            text='You will be notified when your application is reviewed.')

        await interaction.response.send_message(embed=embed, ephemeral=True)

        # Send DM to user with application ID
        try:
            user = await self.bot.fetch_user(user_id)
            dm_embed = discord.Embed(
                title='📨 Application Submitted',
                description=f'Thank you for submitting your application!',
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            dm_embed.add_field(name='Your Application ID',
                               value=f'```{app_id}```', inline=False)
            dm_embed.add_field(name='Full Name', value=name, inline=True)
            dm_embed.add_field(name='Email', value=email, inline=True)
            dm_embed.add_field(
                name='Status', value='**⏳ Pending Review**', inline=False)
            dm_embed.add_field(
                name='📌 Note', value='Keep this application ID safe. You can use `/viewapplication` command to check your application status.', inline=False)
            dm_embed.set_footer(
                text='You will be notified when your application is reviewed.')

            await user.send(embed=dm_embed)
        except discord.Forbidden:
            print(
                f'Could not send DM to user {user_id} - they may have DMs disabled')
        except Exception as e:
            print(f'Error sending DM to user {user_id}: {e}')

    @app_commands.command(name='apply', description='Submit an application')
    async def apply(self, interaction: discord.Interaction):
        """Open the application form modal"""
        await interaction.response.send_modal(ApplicationModal())

    @app_commands.command(name='myapplications', description='View your submitted applications')
    async def my_applications(self, interaction: discord.Interaction):
        """Show user's applications"""
        user_apps = [app for app in self.applications.values(
        ) if app['user_id'] == interaction.user.id]

        if not user_apps:
            embed = discord.Embed(
                title='📋 My Applications',
                description='You have not submitted any applications yet.',
                color=discord.Color.blurple(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title='📋 My Applications',
            color=discord.Color.blurple(),
            timestamp=datetime.now()
        )

        for app in user_apps:
            status_emoji = '⏳' if app['status'] == 'pending' else '✅' if app['status'] == 'approved' else '❌'
            embed.add_field(
                name=f'{status_emoji} {app["id"][:20]}...',
                value=f"**Status:** {app['status'].capitalize()}\n**Submitted:** <t:{int(datetime.fromisoformat(app['submitted_at']).timestamp())}:R>",
                inline=False
            )

        embed.set_footer(text=f'Total Applications: {len(user_apps)}')
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name='viewapplication', description='View a specific application')
    @app_commands.describe(application_id='The application ID to view')
    async def view_application(self, interaction: discord.Interaction, application_id: str):
        """View detailed application information"""
        if application_id not in self.applications:
            embed = discord.Embed(
                title='❌ Application Not Found',
                description=f'No application found with ID: `{application_id}`',
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        app = self.applications[application_id]

        # Check if user is owner or has permission to view
        if app['user_id'] != interaction.user.id and not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title='❌ Permission Denied',
                description='You do not have permission to view this application.',
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        status_color = discord.Color.yellow() if app['status'] == 'pending' else discord.Color.green(
        ) if app['status'] == 'approved' else discord.Color.red()

        embed = discord.Embed(
            title='📄 Application Details',
            color=status_color,
            timestamp=datetime.now()
        )
        embed.add_field(name='Application ID',
                        value=f'`{app["id"]}`', inline=False)
        embed.add_field(name='Full Name', value=app['full_name'], inline=True)
        embed.add_field(name='Email', value=app['email'], inline=True)
        embed.add_field(
            name='Status', value=app['status'].capitalize(), inline=True)
        embed.add_field(name='Reason for Joining',
                        value=app['reason'], inline=False)
        embed.add_field(name='Experience',
                        value=app['experience'], inline=False)
        embed.add_field(
            name='Submitted At', value=f"<t:{int(datetime.fromisoformat(app['submitted_at']).timestamp())}:F>", inline=True)

        if app['reviewed_at']:
            embed.add_field(
                name='Reviewed At', value=f"<t:{int(datetime.fromisoformat(app['reviewed_at']).timestamp())}:F>", inline=True)

        embed.set_footer(text=f'Submitted by {app["username"]}')

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name='allapplications', description='View all applications (Admin only)')
    async def all_applications(self, interaction: discord.Interaction):
        """Show all applications (admin only)"""
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title='❌ Permission Denied',
                description='Only administrators can view all applications.',
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not self.applications:
            embed = discord.Embed(
                title='📋 All Applications',
                description='No applications have been submitted yet.',
                color=discord.Color.blurple(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title='📋 All Applications',
            color=discord.Color.blurple(),
            timestamp=datetime.now()
        )

        pending = sum(1 for app in self.applications.values()
                      if app['status'] == 'pending')
        approved = sum(1 for app in self.applications.values()
                       if app['status'] == 'approved')
        rejected = sum(1 for app in self.applications.values()
                       if app['status'] == 'rejected')

        embed.add_field(
            name='📊 Summary', value=f'**Pending:** {pending}\n**Approved:** {approved}\n**Rejected:** {rejected}', inline=False)

        # Show recent applications
        recent = sorted(self.applications.values(),
                        key=lambda x: x['submitted_at'], reverse=True)[:10]

        for app in recent:
            status_emoji = '⏳' if app['status'] == 'pending' else '✅' if app['status'] == 'approved' else '❌'
            embed.add_field(
                name=f'{status_emoji} {app["full_name"]} ({app["username"]})',
                value=f"**ID:** `{app['id']}`\n**Email:** {app['email']}\n**Submitted:** <t:{int(datetime.fromisoformat(app['submitted_at']).timestamp())}:R>",
                inline=False
            )

        embed.set_footer(
            text=f'Total Applications: {len(self.applications)} | Showing 10 most recent')

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name='reviewapplication', description='Review an application (Admin only)')
    @app_commands.describe(
        application_id='The application ID to review',
        decision='Approve or reject the application'
    )
    @app_commands.choices(decision=[
        app_commands.Choice(name='Approve', value='approved'),
        app_commands.Choice(name='Reject', value='rejected')
    ])
    async def review_application(self, interaction: discord.Interaction, application_id: str, decision: str):
        """Review and approve/reject an application"""
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title='❌ Permission Denied',
                description='Only administrators can review applications.',
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if application_id not in self.applications:
            embed = discord.Embed(
                title='❌ Application Not Found',
                description=f'No application found with ID: `{application_id}`',
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        app = self.applications[application_id]
        app['status'] = decision
        app['reviewed_at'] = datetime.now().isoformat()
        app['reviewer_id'] = interaction.user.id

        self.save_applications()

        status_emoji = '✅' if decision == 'approved' else '❌'
        embed = discord.Embed(
            title=f'{status_emoji} Application {decision.capitalize()}',
            color=discord.Color.green() if decision == 'approved' else discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name='Application ID',
                        value=f'`{application_id}`', inline=False)
        embed.add_field(
            name='Applicant', value=f'{app["full_name"]} (@{app["username"]})', inline=True)
        embed.add_field(name='Email', value=app['email'], inline=True)
        embed.add_field(name='Decision',
                        value=decision.capitalize(), inline=True)
        embed.set_footer(text=f'Reviewed by {interaction.user.name}')

        await interaction.response.send_message(embed=embed, ephemeral=True)

        # Post result to results channel if configured
        results_channel_id = self.get_results_channel(interaction.guild_id)
        if results_channel_id:
            try:
                channel = await self.bot.fetch_channel(results_channel_id)
                result_embed = discord.Embed(
                    title=f'{status_emoji} Application {decision.capitalize()}',
                    color=discord.Color.green() if decision == 'approved' else discord.Color.red(),
                    timestamp=datetime.now()
                )
                result_embed.add_field(
                    name='Applicant', value=f'{app["full_name"]}', inline=True)
                result_embed.add_field(
                    name='Decision', value=decision.capitalize(), inline=True)
                result_embed.set_footer(
                    text=f'Reviewed by {interaction.user.name}')

                # Create mention string for the user
                mention = f'<@{app["user_id"]}>'
                await channel.send(f'{mention}', embed=result_embed)
            except Exception as e:
                print(f'Error posting result to channel: {e}')

    @app_commands.command(name='deleteapplication', description='Delete an application')
    @app_commands.describe(application_id='The application ID to delete')
    async def delete_application(self, interaction: discord.Interaction, application_id: str):
        """Delete an application (user or admin only)"""
        if application_id not in self.applications:
            embed = discord.Embed(
                title='❌ Application Not Found',
                description=f'No application found with ID: `{application_id}`',
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        app = self.applications[application_id]

        # Check permissions
        if app['user_id'] != interaction.user.id and not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title='❌ Permission Denied',
                description='You can only delete your own applications.',
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        del self.applications[application_id]
        self.save_applications()

        embed = discord.Embed(
            title='🗑️ Application Deleted',
            description=f'Application `{application_id}` has been deleted.',
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name='clearapplications', description='Clear all applications (Owner only)')
    async def clear_applications(self, interaction: discord.Interaction):
        """Clear all applications (owner/admin only)"""
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title='❌ Permission Denied',
                description='Only administrators can clear applications.',
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        count = len(self.applications)
        self.applications = {}
        self.save_applications()

        embed = discord.Embed(
            title='🗑️ Applications Cleared',
            description=f'Deleted {count} applications.',
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name='setresultschannel', description='Set the channel where application results are posted (Admin only)')
    @app_commands.describe(channel='The channel to post application results')
    async def set_results_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Set the results channel for application decisions"""
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title='❌ Permission Denied',
                description='Only administrators can set the results channel.',
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        self.set_results_channel(interaction.guild_id, channel.id)

        embed = discord.Embed(
            title='✅ Results Channel Set',
            description=f'Application results will now be posted to {channel.mention}',
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name='Channel', value=channel.mention, inline=True)
        embed.add_field(name='Channel ID',
                        value=f'`{channel.id}`', inline=True)
        embed.set_footer(
            text='Users will be pinged with their application decisions.')

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name='viewresultschannel', description='View the current results channel (Admin only)')
    async def view_results_channel(self, interaction: discord.Interaction):
        """View the configured results channel"""
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title='❌ Permission Denied',
                description='Only administrators can view the results channel.',
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        channel_id = self.get_results_channel(interaction.guild_id)

        if not channel_id:
            embed = discord.Embed(
                title='📭 No Results Channel Set',
                description='Use `/setresultschannel` to configure where application results will be posted.',
                color=discord.Color.yellow(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        try:
            channel = await self.bot.fetch_channel(channel_id)
            embed = discord.Embed(
                title='📬 Results Channel',
                description=f'Application results are posted to this channel.',
                color=discord.Color.blurple(),
                timestamp=datetime.now()
            )
            embed.add_field(name='Channel', value=channel.mention, inline=True)
            embed.add_field(name='Channel ID',
                            value=f'`{channel.id}`', inline=True)
            embed.set_footer(
                text='Users will be pinged with their application decisions.')
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.NotFound:
            embed = discord.Embed(
                title='⚠️ Channel Not Found',
                description='The configured results channel no longer exists. Use `/setresultschannel` to set a new one.',
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name='clearresultschannel', description='Clear the results channel setting (Admin only)')
    async def clear_results_channel(self, interaction: discord.Interaction):
        """Clear the results channel configuration"""
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title='❌ Permission Denied',
                description='Only administrators can clear the results channel.',
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        guild_key = str(interaction.guild_id)
        if guild_key in self.config and 'results_channel' in self.config[guild_key]:
            del self.config[guild_key]['results_channel']
            self.save_config()

        embed = discord.Embed(
            title='🗑️ Results Channel Cleared',
            description='Application results will no longer be posted to a specific channel.',
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


# Setup function to load the cog
async def setup(bot):
    await bot.add_cog(Applications(bot))
