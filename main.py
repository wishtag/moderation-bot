#https://discord.com/api/oauth2/authorize?client_id=1396161419434655855&permissions=8&scope=bot%20applications.commands

import discord
from discord import option
import os
from dotenv import load_dotenv
from datetime import timedelta, datetime, timezone
from typing import Optional

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = discord.Bot(command_prefix="!", intents=intents)

AUTHORIZED_ROLE_ID = 1388945259018588323 # Moderator

GOOOBER_ROLE_ID = 1396544467221348533 # Goober... like duh its the name of the variable
ARTIST_ROLE_ID = 1398408631552053458  # Artist... do i need to say it again?

PROTECTED_ROLE_IDS = [
    1381390158187856086, # Acrylic
    1382024030814470174, # Salami
    1388608520395690004, # Art Panel
    1388945259018588323, # Moderator
    1396183199985696831  # Jira
]

LOG_CHANNEL_ID = 1398414939101728968     # jira-log text chat
APPLY_CHANNEL_ID = 1398415716243214447   # artist-applications text chat
REPORTS_CHANNEL_ID = 1398447401945141268 # reports text chat

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


@bot.slash_command(name="report", description="Report a user or bug to staff.")
@option("reason", str, description="Reason for report")
@option("file", description="Evidence", input_type=discord.Attachment, required=False)
@option("member", discord.Member, description="If this is a user report, provide the user", required=False)
async def report(ctx: discord.ApplicationContext, reason: str, file: discord.Attachment = None, member: discord.Member = None):
    await ctx.defer(ephemeral=True)

    if member:
        reported_user = member.mention
    else:
        reported_user = "None provided"

    embed = discord.Embed(
        title="⛔ New Report",
        description=f"**Reported By:** {ctx.user.mention}\n**Reported User:** {reported_user}\n**Reason:** {reason}",
        color=discord.Color.red()
    )

    if file:
        if not file.content_type or not file.content_type.startswith("image/"):
            await ctx.respond("Please upload a valid image file (PNG, JPEG, etc.)", ephemeral=True)
            return
        else:
            embed.set_image(url=file.url)
    
    embed.timestamp = discord.utils.utcnow()

    # Send to log channel
    report_channel = bot.get_channel(REPORTS_CHANNEL_ID)
    if report_channel:
        await report_channel.send(embed=embed)
    else:
        print(f"⚠️ Log channel with ID {REPORTS_CHANNEL_ID} not found.")

    embed = discord.Embed(
        title="⛔ New Report",
        description=f"**Reported By:** {ctx.user.mention}",
        color=discord.Color.red()
    )
    embed.set_thumbnail(url=ctx.user.avatar.url if ctx.user.avatar else ctx.user.default_avatar.url)
    embed.timestamp = discord.utils.utcnow()

    # Send to log channel
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(embed=embed)
    else:
        print(f"⚠️ Log channel with ID {LOG_CHANNEL_ID} not found.")

    await ctx.respond("✅ Your report has been sent to staff.", ephemeral=True)


@bot.slash_command(name="goober", description="Check if you are eligble for Goober role.")
async def goober(ctx: discord.ApplicationContext):
    await ctx.defer(ephemeral=True)

    now = datetime.now(timezone.utc)
    joined_at = ctx.user.joined_at

    if not joined_at:
        await ctx.respond("⚠️ Couldn't determine when you joined, please try again. If this continues to happen, please report this to staff via `/report`.", ephemeral=True)
        return

    tenure = now - joined_at
    required_tenure = timedelta(days=3)

    if tenure >= required_tenure:
        role = ctx.guild.get_role(GOOOBER_ROLE_ID)
        if not role:
            await ctx.respond("⚠️ Role not found. Check the GOOOBER_ROLE_ID. If you are seeing this, please report this to staff via `/report`.", ephemeral=True)
            return

        if role in ctx.user.roles:
            await ctx.respond("❌ You already have Goober role.", ephemeral=True)
            return

        try:
            await ctx.user.add_roles(role, reason="Met 3-day server tenure requirement")
            await ctx.respond(f"✅ You have been in the server for {tenure.days} days and as such have been promoted to Goober role.", ephemeral=True)

            embed = discord.Embed(
                title="<:Goober:1398408007070777425> User Promoted to Goober",
                description=f"**User:** {ctx.user.mention}",
                color=discord.Color.dark_orange()
            )
            embed.set_thumbnail(url=ctx.user.avatar.url if ctx.user.avatar else ctx.user.default_avatar.url)
            embed.timestamp = discord.utils.utcnow()

            # Send to log channel
            log_channel = bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                await log_channel.send(embed=embed)
            else:
                print(f"⚠️ Log channel with ID {LOG_CHANNEL_ID} not found.")

        except discord.Forbidden:
            await ctx.respond(f"Failed to assign role to {ctx.user.mention}. Check my permissions. If you are seeing this, please report this to staff via `/report`.", ephemeral=True)
    else:
        remaining = required_tenure - tenure
        hours_left = int(remaining.total_seconds() // 3600)
        await ctx.respond(f"❌ You have only been in the server for {tenure.days} days.\nYou need **{hours_left} more hours** to qualify.", ephemeral=True)


@bot.slash_command(name="artist", description="Apply for Artist role.")
@option("file", description="Upload a file", input_type=discord.Attachment)
async def uploadfile(ctx: discord.ApplicationContext, file: discord.Attachment):
    await ctx.defer(ephemeral=True)

    author_roles = [role.id for role in ctx.author.roles]

    if GOOOBER_ROLE_ID not in author_roles:
        await ctx.respond("❌ You must have Goober role to use this command.", ephemeral=True)
        return
    
    if ARTIST_ROLE_ID in author_roles:
        await ctx.respond("❌ You already have Artist role.", ephemeral=True)
        return

    # Check for image content type
    if not file.content_type or not file.content_type.startswith("image/"):
        await ctx.respond("Please upload a valid image file (PNG, JPEG, etc.)", ephemeral=True)
        return

    # Get the target channel
    apply_channel = bot.get_channel(APPLY_CHANNEL_ID)
    if not apply_channel:
        print(f"⚠️ Apply channel with ID {APPLY_CHANNEL_ID} not found.")
        return

    # Create an embed with the image
    embed = discord.Embed(
        title="🖌️ New Application",
        description=f"Uploaded by {ctx.user.mention}",
        color=discord.Color.blue()
    )
    embed.set_image(url=file.url)

    # Send the embed to the target channel
    await apply_channel.send(embed=embed)

    embed = discord.Embed(
        title="🖌️ New Artist Application",
        description=f"**User:** {ctx.user.mention}",
        color=discord.Color.purple()
    )
    embed.set_thumbnail(url=ctx.user.avatar.url if ctx.user.avatar else ctx.user.default_avatar.url)
    embed.timestamp = discord.utils.utcnow()

    # Send to log channel
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(embed=embed)
    else:
        print(f"⚠️ Log channel with ID {LOG_CHANNEL_ID} not found.")

    # Confirm to user
    await ctx.respond("✅ Your application for Artist role has been sent.", ephemeral=True)


@bot.slash_command(name="review_applicant", description="Accept or deny an applicant.")
@option("accepted", bool, description="Accept or deny the applicant")
@option("member", discord.Member, description="The applicant to process")
@option("message_id", str, description="Message ID of the application to delete")
@option("reason", str, description="Optional reason", required=False)
async def review_applicant(ctx: discord.ApplicationContext, accepted: bool, member: discord.Member, message_id: str, reason: str = "No reason provided."):
    await ctx.defer(ephemeral=True)
    
    author_roles = [role.id for role in ctx.author.roles]

    # Check if the user has the authorized role
    if AUTHORIZED_ROLE_ID not in author_roles:
        await ctx.respond("❌ You don't have permission to use this command.", ephemeral=True)
        return
    
    try:
        message_id_int = int(message_id)
    except ValueError:
        await ctx.respond("Invalid message ID format.", ephemeral=True)
        return
    
    apply_channel = bot.get_channel(APPLY_CHANNEL_ID)
    if not apply_channel:
        print(f"⚠️ Apply channel with ID {APPLY_CHANNEL_ID} not found.")
        return
    
    try:
        message = await apply_channel.fetch_message(message_id_int)
        await message.delete()
    except discord.NotFound:
        await ctx.respond("Message not found in the application channel.", ephemeral=True)
        return
    except discord.Forbidden:
        await ctx.respond("I don't have permission to delete that message.", ephemeral=True)
        return
    
    title = "✅ Artist Application Accepted" if accepted else "❌ Artist Application Denied"
    color = discord.Color.green() if accepted else discord.Color.red()

    embed = discord.Embed(
        title=title,
        description=f"**User:** {member.mention}\n**Reason:** {reason}\n**Moderator:** {ctx.author.mention}",
        color=color
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.timestamp = discord.utils.utcnow()

    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(embed=embed)
    else:
        print(f"⚠️ Log channel with ID {LOG_CHANNEL_ID} not found.")

    # Try to DM the user
    try:
        await member.send(embed=embed)
    except discord.Forbidden:
        await ctx.respond(f"Couldn't DM {member.mention}. They might have DMs disabled.", ephemeral=True)
        #return

    # If accepted, assign the role
    if accepted:
        role = ctx.guild.get_role(ARTIST_ROLE_ID)
        if not role:
            await ctx.respond("Role not found. Check the ARTIST_ROLE_ID. If you are seeing this, please report this to staff via `/report`.", ephemeral=True)
            return
        try:
            await member.add_roles(role, reason=f"Accepted by {ctx.user} - {reason}")
        except discord.Forbidden:
            await ctx.respond(f"Couldn't assign role to {member.mention}. Check my permissions. If you are seeing this, please report this to staff via `/report`.", ephemeral=True)
            return

    # Respond to the reviewer
    action = "accepted and given the role" if accepted else "denied"
    await ctx.respond(f"{member.mention} has been {action} and notified via DM (If possible).", ephemeral=True)


@bot.slash_command(name="ban", description="Ban a member from the server.")
@option("member", discord.Member, description="The user to ban")
@option("reason", str, description="Optional reason", required=False)
@option("silent", bool, description="Whether or not to broadcast the ban to the channel the command was executed in", required=False)
async def ban(ctx: discord.ApplicationContext, member: discord.Member, reason: str = "No reason provided", silent: bool = True):
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

        if silent:
            await ctx.respond(embed=embed, ephemeral=True)
        else:
            await ctx.respond(embed=embed)

        # Send to log channel
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(embed=embed)
        else:
            print(f"⚠️ Log channel with ID {LOG_CHANNEL_ID} not found.")

    except discord.Forbidden:
        await ctx.respond("❌ I don't have permission to ban this user.", ephemeral=True)
    except Exception as e:
        await ctx.respond(f"❌ An unexpected error occurred: {str(e)}", ephemeral=True)


@bot.slash_command(name="pardon", description="Unban a user from the server.")
@option("member", discord.Member, description="The user to unban")
@option("silent", bool, description="Whether or not to broadcast the unban to the channel the command was executed in", required=False)
async def pardon(ctx: discord.ApplicationContext, user: discord.User, silent: bool = True):
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

        if silent:
            await ctx.respond(embed=embed, ephemeral=True)
        else:
            await ctx.respond(embed=embed)

        # Send embed to log channel
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(embed=embed)
        else:
            print(f"⚠️ Log channel with ID {LOG_CHANNEL_ID} not found.")

    except discord.Forbidden:
        await ctx.respond("❌ I don't have permission to unban this user.", ephemeral=True)
    except Exception as e:
        await ctx.respond(f"❌ An unexpected error occurred: {str(e)}", ephemeral=True)


@bot.slash_command(name="timeout", description="Temporarily timeout a member.")
@option("member", discord.Member, description="The user to timeout")
@option("duration", str, description="The amount of time to timeout the user. Example formatting: `10m`, `2h`, `1d`")
@option("reason", str, description="Optional reason", required=False)
@option("silent", bool, description="Whether or not to broadcast the timeout to the channel the command was executed in", required=False)
async def timeout(ctx: discord.ApplicationContext, member: discord.Member, duration: str, reason: str = "No reason provided", silent: bool = True):
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
        if silent:
            await ctx.respond(embed=embed, ephemeral=True)
        else:
            await ctx.respond(embed=embed)

        # Send to log channel
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(embed=embed)
        else:
            print(f"⚠️ Log channel with ID {LOG_CHANNEL_ID} not found.")

    except discord.Forbidden:
        await ctx.respond("❌ I don't have permission to timeout this user.", ephemeral=True)
    except Exception as e:
        await ctx.respond(f"❌ An unexpected error occurred: {str(e)}", ephemeral=True)


@bot.slash_command(name="untimeout", description="Remove timeout from a member.")
@option("member", discord.Member, description="The user to untimeout")
@option("reason", str, description="Optional reason", required=False)
@option("silent", bool, description="Whether or not to broadcast the untimeout to the channel the command was executed in", required=False)
async def timeout(ctx: discord.ApplicationContext, member: discord.Member, reason: str = "No reason provided", silent: bool = True):
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


    try:
        await member.timeout(discord.utils.utcnow() + parse_duration('0s'), reason=reason)

        # Create the embed
        embed = discord.Embed(
            title="⏳ User Untimed Out",
            description=f"**User:** {member.mention}\n**Reason:** {reason}\n**Moderator:** {ctx.author.mention}",
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.timestamp = discord.utils.utcnow()

        # Respond in command channel
        if silent:
            await ctx.respond(embed=embed, ephemeral=True)
        else:
            await ctx.respond(embed=embed)

        # Send to log channel
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(embed=embed)
        else:
            print(f"⚠️ Log channel with ID {LOG_CHANNEL_ID} not found.")

    except discord.Forbidden:
        await ctx.respond("❌ I don't have permission to timeout this user.", ephemeral=True)
    except Exception as e:
        await ctx.respond(f"❌ An unexpected error occurred: {str(e)}", ephemeral=True)

@bot.slash_command(name="delete_message", description="Delete a message by its ID.")
@option("message_id", str, description="The ID of the message to delete")
@option("file", description="A screenshot of the message you are deleting", input_type=discord.Attachment)
@option("reason", str, description="Optional reason", required=False)
@option("silent", bool, description="Whether or not to broadcast the timeout to the channel the command was executed in", required=False)
async def delete_message(ctx: discord.ApplicationContext, file: discord.Attachment, message_id: str, reason: str = "No reason provided", silent: bool = True):
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

        if not file.content_type or not file.content_type.startswith("image/"):
            await ctx.respond("Please upload a valid image file (PNG, JPEG, etc.)", ephemeral=True)
            return
        else:
            embed.set_image(url=file.url)

        embed.timestamp = discord.utils.utcnow()

        if silent:
            await ctx.respond(embed=embed, ephemeral=True)
        else:
            await ctx.respond(embed=embed)

        # Send to log channel
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(embed=embed)
        else:
            print(f"⚠️ Log channel with ID {LOG_CHANNEL_ID} not found.")

    except Exception as e:
        await ctx.respond(f"❌ An unexpected error occurred: {str(e)}", ephemeral=True)


token = os.getenv('bot_token')
bot.run(token)