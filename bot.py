import discord
import os

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)

MEMBER_ROLE_NAME = "Member | Gucci Goobers"
UNVERIFIED_ROLE_NAME = "Unverified"

@client.event
async def on_ready():
    print(f"Inloggad som {client.user}")

@client.event
async def on_member_update(before, after):
    before_roles = [r.name for r in before.roles]
    after_roles = [r.name for r in after.roles]
    
    if MEMBER_ROLE_NAME not in before_roles and MEMBER_ROLE_NAME in after_roles:
        unverified = discord.utils.get(after.guild.roles, name=UNVERIFIED_ROLE_NAME)
        if unverified and unverified in after.roles:
            await after.remove_roles(unverified)
            print(f"Tog bort Unverified från {after.name}")

client.run(os.environ["DISCORD_TOKEN"])
