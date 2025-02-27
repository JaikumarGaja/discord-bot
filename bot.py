import os
import discord
import asyncio
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = commands.Bot(command_prefix="!", intents=intents)

# Replace with your actual IDs
CLASH_PERK_BOT_ID = 526971716711350273
LINK_CHANNEL_ID = 1344369306347110431
VERIFIED_ROLE_ID = 1343887228161622028

class VerificationSystem:
    def __init__(self):
        self.pending_verifications = {}
        self.cleanup_tasks = []

    async def delayed_verification(self, member, channel):
        """Handle verification with delays and cleanup"""
        try:
            # First delay and role assignment
            await asyncio.sleep(5)
            verified_role = channel.guild.get_role(VERIFIED_ROLE_ID)
            await member.add_roles(verified_role)
            
            # Send confirmation
            confirm_msg = await channel.send(
                f"{member.mention} ✅ Verification complete! Guest access granted."
            )
            
            # Second delay and cleanup (preserve pinned messages)
            await asyncio.sleep(5)
            await channel.purge(
                limit=20,
                check=lambda m: not m.pinned and m.id != confirm_msg.id
            )
            await confirm_msg.delete()
            
        except Exception as e:
            print(f"[VERIFICATION ERROR] {type(e).__name__}: {e}")
            await channel.send(
                f"{member.mention} ❗ Verification process failed. Please contact staff.",
                delete_after=10
            )

ver_system = VerificationSystem()

@bot.event
async def on_ready():
    print(f"Bot ready: {bot.user}")

@bot.command()
async def link(ctx):
    """Start verification process"""
    try:
        await ctx.message.delete()
    except discord.NotFound:
        pass
    
    ver_system.pending_verifications[ctx.channel.id] = ctx.author.id
    msg = await ctx.send(
        "✅ **Next Step:** Use Clash Perk's command:\n"
        "`/link create player_tag:YOUR_PLAYER_TAG`\n"
        "Processing will begin automatically!",
        delete_after=15
    )

@bot.event
async def on_message(message):
    await bot.process_commands(message)

    # Handle non-command messages (preserve pinned messages)
    if message.channel.id == LINK_CHANNEL_ID and not message.author.bot and not message.pinned:
        try:
            await message.delete()
        except:
            pass

    # Handle Clash Perk responses
    if message.author.id == CLASH_PERK_BOT_ID and message.channel.id == LINK_CHANNEL_ID:
        user_id = ver_system.pending_verifications.get(message.channel.id)
        if not user_id:
            return

        try:
            member = await message.guild.fetch_member(user_id)
            temp_msg = await message.channel.send(
                f"{member.mention} ✅ Verification complete! Guest access granted. You can now chat in the #Guest-Space "
            )
            
            # Start verification task
            task = bot.loop.create_task(
                ver_system.delayed_verification(member, message.channel)
            )
            ver_system.cleanup_tasks.append(task)
            
            # Delete temporary message after delay
            await asyncio.sleep(3)
            await temp_msg.delete()
            
        except discord.NotFound:
            await message.channel.send("❌ User not found!", delete_after=5)
        finally:
            del ver_system.pending_verifications[message.channel.id]

bot.run(BOT_TOKEN)