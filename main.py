#https://discord.com/api/oauth2/authorize?client_id=1396161419434655855&permissions=8&scope=bot%20applications.commands

import discord
import os
from dotenv import load_dotenv
from datetime import timedelta
from typing import Optional

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = discord.Bot(command_prefix="!", intents=intents)

AUTHORIZED_ROLE_ID = 1388945259018588323 # Moderator

PROTECTED_ROLE_IDS = [
    1381390158187856086, # Acrylic
    1382024030814470174, # Salami
    1388608520395690004, # Art Panel
    1388945259018588323  # Moderator
]

SYSTEM_CHANNEL_ID = 1381386621533945997 # System text chat

RESTRICTED_MESSAGE_IDS = [
    1381732115401670807, # Rules embed
    1388940505521590334, # Role Info embed
    1382458512260599840  # Video Progress embed
]

def parse_duration(duration_str: str) -> Optional[timedelta]:
    """Parses duration strings like '10m', '2h', '1d' into timedelta."""
    try:
        unit = duration_str[-1]
        value = int(duration_str[:-1])
        if unit == "s":
            return timedelta(seconds=value)
        elif unit == "m":
            return timedelta(minutes=value)
        elif unit == "h":
            return timedelta(hours=value)
        elif unit == "d":
            return timedelta(days=value)
        else:
            return None
    except:
        return None


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.sync_commands()
    print("Commands synced!")


@bot.slash_command(name="ban", description="Ban a member from the server.")
async def ban(ctx: discord.ApplicationContext, member: discord.Member, reason: str = "No reason provided"):
    author_roles = [role.id for role in ctx.author.roles]

    # Check if the user has the authorized role
    if AUTHORIZED_ROLE_ID not in author_roles:
        await ctx.respond("❌ You don't have permission to use this command.", ephemeral=True)
        return

    # Prevent banning users with protected roles
    try:
        target_roles = [role.id for role in member.roles]
        if any(role_id in PROTECTED_ROLE_IDS for role_id in target_roles):
            await ctx.respond("❌ You cannot ban this user because they have a protected role.", ephemeral=True)
            return
    except:
        pass

    # Try banning the user
    try:
        await member.ban(reason=reason)
        
        # Create embed
        embed = discord.Embed(
            title="🔨 User Banned",
            description=f"**User:** {member.mention}\n**Reason:** {reason}\n**Moderator:** {ctx.author.mention}",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.timestamp = discord.utils.utcnow()

        await ctx.respond(embed=embed)

        # Send to system channel
        log_channel = bot.get_channel(SYSTEM_CHANNEL_ID)
        if log_channel:
            await log_channel.send(embed=embed)
        else:
            print(f"⚠️ Could not find System channel with ID {SYSTEM_CHANNEL_ID}")
    except discord.Forbidden:
        await ctx.respond("❌ I don't have permission to ban this user.", ephemeral=True)
    except Exception as e:
        await ctx.respond(f"❌ An unexpected error occurred: {str(e)}", ephemeral=True)


@bot.slash_command(name="pardon", description="Unban a user from the server.")
async def pardon(ctx: discord.ApplicationContext, user: discord.User):
    author_roles = [role.id for role in ctx.author.roles]

    # Check if the user has the authorized role
    if AUTHORIZED_ROLE_ID not in author_roles:
        await ctx.respond("❌ You don't have permission to use this command.", ephemeral=True)
        return

    try:
        # Check if user is banned
        banned_user = None
        async for ban in ctx.guild.bans():
            if ban.user.id == user.id:
                banned_user = ban
                break

        if banned_user is None:
            await ctx.respond("⚠️ This user is not banned.", ephemeral=True)
            return

        # Unban the user
        await ctx.guild.unban(user)

        # Create the embed
        embed = discord.Embed(
            title="🕊️ User Unbanned",
            description=f"**User:** {user.mention}\n**Moderator:** {ctx.author.mention}",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        embed.timestamp = discord.utils.utcnow()

        await ctx.respond(embed=embed)

        # Send embed to system channel
        log_channel = bot.get_channel(SYSTEM_CHANNEL_ID)
        if log_channel:
            await log_channel.send(embed=embed)
        else:
            print(f"⚠️ System channel with ID {SYSTEM_CHANNEL_ID} not found.")

    except discord.Forbidden:
        await ctx.respond("❌ I don't have permission to unban this user.", ephemeral=True)
    except Exception as e:
        await ctx.respond(f"❌ An unexpected error occurred: {str(e)}", ephemeral=True)


@bot.slash_command(name="timeout", description="Temporarily timeout a member.")
async def timeout(ctx: discord.ApplicationContext, member: discord.Member, duration: str, reason: str = "No reason provided"):
    author_roles = [role.id for role in ctx.author.roles]

    # Permission check
    if AUTHORIZED_ROLE_ID not in author_roles:
        await ctx.respond("❌ You don't have permission to use this command.", ephemeral=True)
        return

    # Prevent timing out users with protected roles
    try:
        target_roles = [role.id for role in member.roles]
        if any(role_id in PROTECTED_ROLE_IDS for role_id in target_roles):
            await ctx.respond("❌ You cannot timeout this user because they have a protected role.", ephemeral=True)
            return
    except:
        pass

    # Parse the duration string
    timeout_duration = parse_duration(duration)
    if not timeout_duration:
        await ctx.respond("❌ Invalid duration format. Use something like `10m`, `2h`, `1d`.", ephemeral=True)
        return

    try:
        until = discord.utils.utcnow() + timeout_duration
        await member.timeout(until, reason=reason)

        # Create the embed
        embed = discord.Embed(
            title="⏳ User Timed Out",
            description=f"**User:** {member.mention}\n**Duration:** {duration}\n**Reason:** {reason}\n**Moderator:** {ctx.author.mention}",
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.timestamp = discord.utils.utcnow()

        # Respond in command channel
        await ctx.respond(embed=embed)

        # Send to system channel
        log_channel = bot.get_channel(SYSTEM_CHANNEL_ID)
        if log_channel:
            await log_channel.send(embed=embed)
        else:
            print(f"⚠️ System channel with ID {SYSTEM_CHANNEL_ID} not found.")

    except discord.Forbidden:
        await ctx.respond("❌ I don't have permission to timeout this user.", ephemeral=True)
    except Exception as e:
        await ctx.respond(f"❌ An unexpected error occurred: {str(e)}", ephemeral=True)


@bot.slash_command(name="delete_message", description="Delete a message by its ID.")
async def delete_message(ctx: discord.ApplicationContext, message_id: str, reason: str = "No reason provided"):
    author_roles = [role.id for role in ctx.author.roles]

    # Check permission role
    if AUTHORIZED_ROLE_ID not in author_roles:
        await ctx.respond("❌ You don't have permission to use this command.", ephemeral=True)
        return

    try:
        # Prevent deletion of protected message IDs
        message_id_int = int(message_id)
        if message_id_int in RESTRICTED_MESSAGE_IDS:
            await ctx.respond("🚫 This message is restricted and cannot be deleted.", ephemeral=True)
            return

        # Search all text channels for the message
        target_message = None
        for channel in ctx.guild.text_channels:
            try:
                msg = await channel.fetch_message(message_id_int)
                if msg:
                    target_message = msg
                    break
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                continue

        if not target_message:
            await ctx.respond("❌ Message not found in any accessible text channel.", ephemeral=True)
            return

        # Check if message author has protected roles
        if isinstance(target_message.author, discord.Member):
            target_roles = [role.id for role in target_message.author.roles]
            if any(rid in PROTECTED_ROLE_IDS for rid in target_roles):
                await ctx.respond("🚫 Cannot delete messages from protected users.", ephemeral=True)
                return

        await target_message.delete()

        # Create response embed
        embed = discord.Embed(
            title="🗑️ Message Deleted",
            description=f"**Message ID:** `{message_id}`\n**Channel:** {target_message.channel.mention}\n**Author:** {target_message.author.mention}\n**Reason:** {reason}\n**Moderator:** {ctx.author.mention}",
            color=discord.Color.red()
        )
        embed.timestamp = discord.utils.utcnow()

        await ctx.respond(embed=embed)

        # Send to system channel
        log_channel = bot.get_channel(SYSTEM_CHANNEL_ID)
        if log_channel:
            await log_channel.send(embed=embed)
        else:
            print(f"⚠️ System channel with ID {SYSTEM_CHANNEL_ID} not found.")

    except Exception as e:
        await ctx.respond(f"❌ An unexpected error occurred: {str(e)}", ephemeral=True)


token = os.getenv('bot_token')
bot.run(token)