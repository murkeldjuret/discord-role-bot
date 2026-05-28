import discord
import os

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

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

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
