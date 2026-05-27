import discord
import os

intents = discord.Intents.default()
intents.members = True
intents.guilds = True

client = discord.Client(intents=intents)

REMOVE_UNVERIFIED_WHEN = ["Member | Gucci Goobers", "Applicant"]
UNVERIFIED_ROLE_NAME = "Unverified"
APPLICANT_ROLE_NAME = "Applicant"
TICKET_PREFIX = "ticket-"

@client.event
async def on_ready():
    print(f"Inloggad som {client.user}")

@client.event
async def on_guild_channel_create(channel):
    if channel.name.startswith(TICKET_PREFIX):
        guild = channel.guild
        applicant_role = discord.utils.get(guild.roles, name=APPLICANT_ROLE_NAME)
        unverified_role = discord.utils.get(guild.roles, name=UNVERIFIED_ROLE_NAME)
        
        for member in channel.members:
            if member.bot:
                continue
            if applicant_role and applicant_role not in member.roles:
                await member.add_roles(applicant_role)
            if unverified_role and unverified_role in member.roles:
                await member.remove_roles(unverified_role)
            print(f"Gav Applicant och tog bort Unverified från {member.name}")

@client.event
async def on_member_update(before, after):
    before_roles = [r.name for r in before.roles]
    after_roles = [r.name for r in after.roles]
    
    for role_name in REMOVE_UNVERIFIED_WHEN:
        if role_name not in before_roles and role_name in after_roles:
            unverified = discord.utils.get(after.guild.roles, name=UNVERIFIED_ROLE_NAME)
            if unverified and unverified in after.roles:
                await after.remove_roles(unverified)
                print(f"Tog bort Unverified från {after.name}")
            break

client.run(os.environ["DISCORD_TOKEN"])
