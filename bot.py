import discord
import os
import asyncio
from datetime import datetime, timezone, timedelta
 
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
 
client = discord.Client(intents=intents)
 
REMOVE_UNVERIFIED_WHEN = ["Member | Gucci Goobers", "Applicant"]
UNVERIFIED_ROLE_NAME = "Unverified"
APPLICANT_ROLE_NAME = "Applicant"
MEMBER_ROLE_NAME = "Member | Gucci Goobers"
GUEST_ROLE_NAME = "Guest"
TICKET_PREFIX = "ticket-"
CLOSED_PREFIX = "closed-"
GUEST_CATEGORY = "📋 Guest Applications"
MEMBER_CATEGORY = "📋 Applications"
 
# --- CoC Event Countdown Config ---
COUNTDOWN_CATEGORY_NAME = "📅 Events"  # Category where countdown channels will live
 
def get_next_coc_events():
    """Returns upcoming CoC events with their next occurrence datetimes (UTC)."""
    now = datetime.now(timezone.utc)
    events = []
 
    # --- Raid Weekend: starts every Friday 07:00 UTC ---
    days_until_friday = (4 - now.weekday()) % 7
    raid = now.replace(hour=7, minute=0, second=0, microsecond=0) + timedelta(days=days_until_friday)
    if raid <= now:
        raid += timedelta(weeks=1)
    events.append(("Raid Weekend", raid))
 
    # --- Clan Games: starts 22nd every month 08:00 UTC ---
    clan_games = now.replace(day=22, hour=8, minute=0, second=0, microsecond=0)
    if clan_games <= now:
        # Move to next month
        if now.month == 12:
            clan_games = clan_games.replace(year=now.year + 1, month=1)
        else:
            clan_games = clan_games.replace(month=now.month + 1)
    events.append(("Clan Games", clan_games))
 
    # --- CWL: starts 1st every month 08:00 UTC ---
    cwl = now.replace(day=1, hour=8, minute=0, second=0, microsecond=0)
    if cwl <= now:
        if now.month == 12:
            cwl = cwl.replace(year=now.year + 1, month=1)
        else:
            cwl = cwl.replace(month=now.month + 1)
    events.append(("CWL", cwl))
 
    # --- EOS / League Reset: starts 15th every month 05:00 UTC ---
    eos = now.replace(day=15, hour=5, minute=0, second=0, microsecond=0)
    if eos <= now:
        if now.month == 12:
            eos = eos.replace(year=now.year + 1, month=1)
        else:
            eos = eos.replace(month=now.month + 1)
    events.append(("EOS", eos))
 
    return events
 
def format_countdown(event_name, event_time):
    """Format: 'CWL: 3D 15H'"""
    now = datetime.now(timezone.utc)
    diff = event_time - now
    total_seconds = int(diff.total_seconds())
    if total_seconds <= 0:
        return f"{event_name}: NOW"
    days = diff.days
    hours = diff.seconds // 3600
    if days > 0:
        return f"{event_name}: {days}D {hours}H"
    else:
        minutes = (diff.seconds % 3600) // 60
        return f"{event_name}: {hours}H {minutes}M"
 
async def update_countdown_channels(guild):
    """Creates or updates voice channels with CoC event countdowns."""
    # Find or create the countdown category
    category = discord.utils.get(guild.categories, name=COUNTDOWN_CATEGORY_NAME)
    if category is None:
        category = await guild.create_category(COUNTDOWN_CATEGORY_NAME)
        # Make it read-only for everyone
        await category.set_permissions(guild.default_role, connect=False, view_channel=True)
 
    events = get_next_coc_events()
 
    for event_name, event_time in events:
        channel_name = format_countdown(event_name, event_time)
        # Find existing channel for this event
        existing = discord.utils.find(
            lambda c: c.name.startswith(event_name) and c.category_id == category.id,
            guild.voice_channels
        )
        if existing:
            if existing.name != channel_name:
                await existing.edit(name=channel_name)
                print(f"Updated: {channel_name}")
        else:
            vc = await guild.create_voice_channel(channel_name, category=category)
            await vc.set_permissions(guild.default_role, connect=False, view_channel=True)
            print(f"Created: {channel_name}")
 
async def countdown_loop():
    """Updates countdown channels every hour."""
    await client.wait_until_ready()
    while not client.is_closed():
        for guild in client.guilds:
            try:
                await update_countdown_channels(guild)
            except Exception as e:
                print(f"Error updating countdowns for {guild.name}: {e}")
        await asyncio.sleep(3600)  # Update every hour
 
# --- Approval Views ---
 
class ApproveView(discord.ui.View):
    def __init__(self, applicant):
        super().__init__(timeout=None)
        self.applicant = applicant
 
    @discord.ui.button(label="✅ Approve as Member", style=discord.ButtonStyle.green)
    async def approve_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member_role = discord.utils.get(guild.roles, name=MEMBER_ROLE_NAME)
        applicant_role = discord.utils.get(guild.roles, name=APPLICANT_ROLE_NAME)
        if member_role:
            await self.applicant.add_roles(member_role)
        if applicant_role and applicant_role in self.applicant.roles:
            await self.applicant.remove_roles(applicant_role)
        await interaction.response.send_message(f"✅ {self.applicant.mention} is now a Member! Closing ticket...")
        await interaction.channel.delete()
        self.stop()
 
    @discord.ui.button(label="✅ Approve as Guest", style=discord.ButtonStyle.blurple)
    async def approve_guest(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        guest_role = discord.utils.get(guild.roles, name=GUEST_ROLE_NAME)
        applicant_role = discord.utils.get(guild.roles, name=APPLICANT_ROLE_NAME)
        if guest_role:
            await self.applicant.add_roles(guest_role)
        if applicant_role and applicant_role in self.applicant.roles:
            await self.applicant.remove_roles(applicant_role)
        await interaction.response.send_message(f"✅ {self.applicant.mention} is now a Guest! Closing ticket...")
        await interaction.channel.delete()
        self.stop()
 
class MemberApproveView(ApproveView):
    def __init__(self, applicant):
        super().__init__(applicant)
        self.remove_item(self.approve_guest)
 
class GuestApproveView(ApproveView):
    def __init__(self, applicant):
        super().__init__(applicant)
        self.remove_item(self.approve_member)
 
# --- Events ---
 
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    client.loop.create_task(countdown_loop())
 
@client.event
async def on_guild_channel_create(channel):
    if not channel.name.startswith(TICKET_PREFIX):
        return
 
    guild = channel.guild
    applicant_role = discord.utils.get(guild.roles, name=APPLICANT_ROLE_NAME)
    unverified_role = discord.utils.get(guild.roles, name=UNVERIFIED_ROLE_NAME)
 
    applicant = None
    for member in channel.members:
        if member.bot:
            continue
        if applicant_role and applicant_role not in member.roles:
            await member.add_roles(applicant_role)
        if unverified_role and unverified_role in member.roles:
            await member.remove_roles(unverified_role)
        applicant = member
 
    if applicant is None:
        return
 
    category_name = channel.category.name if channel.category else ""
    print(f"Ticket created in category: {category_name}")
 
    if category_name == MEMBER_CATEGORY:
        view = MemberApproveView(applicant)
        await channel.send("**🎟️ Application Controls**", view=view)
    elif category_name == GUEST_CATEGORY:
        view = GuestApproveView(applicant)
        await channel.send("**🎟️ Application Controls**", view=view)
 
@client.event
async def on_guild_channel_delete(channel):
    if channel.name.startswith(CLOSED_PREFIX):
        guild = channel.guild
        applicant_role = discord.utils.get(guild.roles, name=APPLICANT_ROLE_NAME)
 
        for member in guild.members:
            if member.bot:
                continue
            if applicant_role and applicant_role in member.roles:
                try:
                    await member.kick(reason="Application closed without approval")
                    print(f"Kicked {member.name}")
                except Exception as e:
                    print(f"Could not kick {member.name}: {e}")
 
@client.event
async def on_member_update(before, after):
    before_roles = [r.name for r in before.roles]
    after_roles = [r.name for r in after.roles]
 
    for role_name in REMOVE_UNVERIFIED_WHEN:
        if role_name not in before_roles and role_name in after_roles:
            unverified = discord.utils.get(after.guild.roles, name=UNVERIFIED_ROLE_NAME)
            if unverified and unverified in after.roles:
                await after.remove_roles(unverified)
                print(f"Removed Unverified from {after.name}")
            break
 
client.run(os.environ["DISCORD_TOKEN"])
