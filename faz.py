import discord
import os
from discord.ext import commands
from discord.ui import Button, View, Modal, InputText
from flask import Flask
from threading import Thread

# --- DUMMY WEB SERVER FOR RENDER FREE TIER ---
app = Flask('')
@app.route('/')
def home():
    return "Fazbear Bot is Online!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# --- BOT LOGIC ---
config = {"app_channel": None, "results_channel": None, "log_channel": None, "staff_role_id": None}
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(intents=intents)

class AppModal(Modal):
    def __init__(self) -> None:
        super().__init__(title="Lifesteal Fazbear Application")
        self.add_item(InputText(label="1. Whats your username", placeholder="Minecraft IGN"))
        self.add_item(InputText(label="2. Why do you want to join Fazbear", style=discord.InputTextStyle.paragraph))
        self.add_item(InputText(label="3. What are your skills", style=discord.InputTextStyle.paragraph))
        self.add_item(InputText(label="4. What can you offer", style=discord.InputTextStyle.paragraph))
        self.add_item(InputText(label="5. Why should we accept you", style=discord.InputTextStyle.paragraph))

    async def callback(self, interaction: discord.Interaction):
        if not config["results_channel"]:
            return await interaction.response.send_message("❌ Results channel not set.", ephemeral=True)
        results_chan = bot.get_channel(config["results_channel"])
        username_val = self.children[0].value
        embed = discord.Embed(title="New Application Submitted", color=0x2b2d31)
        embed.set_author(name=f"Applicant: {username_val}", icon_url=interaction.user.display_avatar.url)
        embed.description = f"**Discord Account:** {interaction.user.mention}\n**Account ID:** `{interaction.user.id}`"
        embed.add_field(name="**Why join?**", value=f"```\n{self.children[1].value}\n```", inline=False)
        embed.add_field(name="**Skills**", value=f"```\n{self.children[2].value}\n```", inline=False)
        embed.add_field(name="**Offer**", value=f"```\n{self.children[3].value}\n```", inline=True)
        embed.add_field(name="**Why accept?**", value=f"```\n{self.children[4].value}\n```", inline=True)
        view = AdminDecisionView(target_user=interaction.user, target_username=username_val)
        msg = await results_chan.send(embed=embed, view=view)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        await interaction.response.send_message("✅ Application sent.", ephemeral=True)

class AdminDecisionView(View):
    def __init__(self, target_user, target_username):
        super().__init__(timeout=None)
        self.target_user = target_user
        self.target_username = target_username

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, emoji="✔️", custom_id="acc_btn")
    async def accept(self, button: Button, interaction: discord.Interaction):
        await self.process_decision(interaction, "Accepted", 0x2ecc71)

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red, emoji="✖️", custom_id="deny_btn")
    async def deny(self, button: Button, interaction: discord.Interaction):
        await self.process_decision(interaction, "Denied", 0xe74c3c)

    async def process_decision(self, interaction, status, color):
        if config["staff_role_id"] not in [role.id for role in interaction.user.roles]:
            return await interaction.response.send_message("❌ No permission.", ephemeral=True)
        log_chan = bot.get_channel(config["log_channel"])
        log_embed = discord.Embed(description=f"**{self.target_username}** ({self.target_user.mention}) Has been {status.lower()}", color=color)
        await log_chan.send(embed=log_embed)
        for item in self.children: item.disabled = True
        await interaction.message.edit(view=self)
        await interaction.response.send_message(f"Status: {status}.", ephemeral=True)

class ApplyStartView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Apply", style=discord.ButtonStyle.blurple, emoji="📝", custom_id="main_apply")
    async def apply_btn(self, button: Button, interaction: discord.Interaction):
        await interaction.response.send_modal(AppModal())

setup = bot.create_group("setup", "Configure system", default_member_permissions=discord.Permissions(administrator=True))
@setup.command(name="role")
async def setup_role(ctx, role: discord.Role):
    config["staff_role_id"] = role.id
    await ctx.respond(f"✅ Role set: `{role.name}`")
@setup.command(name="channel")
async def setup_app_chan(ctx, channel: discord.TextChannel):
    config["app_channel"] = channel.id
    await ctx.respond(f"✅ App channel: {channel.mention}")
@setup.command(name="results")
async def setup_res_chan(ctx, channel: discord.TextChannel):
    config["results_channel"] = channel.id
    await ctx.respond(f"✅ Results channel: {channel.mention}")
@setup.command(name="logs")
async def setup_log_chan(ctx, channel: discord.TextChannel):
    config["log_channel"] = channel.id
    await ctx.respond(f"✅ Log channel: {channel.mention}")
@bot.slash_command(name="post")
async def post_msg(ctx):
    channel = bot.get_channel(config["app_channel"])
    embed = discord.Embed(title="Lifesteal Fazbear Applications", description="Click to apply.", color=0x992d22)
    await channel.send(embed=embed, view=ApplyStartView())
    await ctx.respond("🚀 Posted.")

if __name__ == "__main__":
    keep_alive() # Start the dummy web server
    token = os.getenv("BOT_TOKEN")
    bot.run(token)
