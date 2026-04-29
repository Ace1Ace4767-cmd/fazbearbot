import discord
import os
from discord.ext import commands
from discord.ui import Button, View, Modal, InputText

# Configuration Storage
config = {
    "app_channel": None,
    "results_channel": None,
    "log_channel": None,
    "staff_role_id": None
}

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(intents=intents)

# --- APPLICATION MODAL ---
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
            return await interaction.response.send_message("❌ Results channel is not configured.", ephemeral=True)

        results_chan = bot.get_channel(config["results_channel"])
        username_val = self.children[0].value
        
        # Professional Clean Embed for Staff
        embed = discord.Embed(title="New Application Submitted", color=0x2b2d31)
        embed.set_author(name=f"Applicant: {username_val}", icon_url=interaction.user.display_avatar.url)
        
        # Added the User Mention here
        embed.description = f"**Discord Account:** {interaction.user.mention}\n**Account ID:** `{interaction.user.id}`"
        
        embed.add_field(name="**Why join Fazbear?**", value=f"```\n{self.children[1].value}\n```", inline=False)
        embed.add_field(name="**Skills**", value=f"```\n{self.children[2].value}\n```", inline=False)
        embed.add_field(name="**What can they offer?**", value=f"```\n{self.children[3].value}\n```", inline=True)
        embed.add_field(name="**Why accept?**", value=f"```\n{self.children[4].value}\n```", inline=True)
        
        embed.set_footer(text="Lifesteal Fazbear • Voting in Progress")

        view = AdminDecisionView(target_user=interaction.user, target_username=username_val)
        msg = await results_chan.send(embed=embed, view=view)
        
        # Staff voting reactions
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

        await interaction.response.send_message("✅ Your application has been sent to the staff team.", ephemeral=True)

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
            return await interaction.response.send_message("❌ You do not have the required staff role.", ephemeral=True)

        if not config["log_channel"]:
            return await interaction.response.send_message("❌ Log channel is not configured.", ephemeral=True)
        
        log_chan = bot.get_channel(config["log_channel"])
        
        # Log formatting: (username) Has been accepted/denied + mention
        log_embed = discord.Embed(
            description=f"**{self.target_username}** ({self.target_user.mention}) Has been {status.lower()}", 
            color=color
        )
        log_embed.set_footer(text=f"Decision by: {interaction.user.display_name}")
        
        await log_chan.send(embed=log_embed)
        
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)
        await interaction.response.send_message(f"Application {status}.", ephemeral=True)

class ApplyStartView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Apply", style=discord.ButtonStyle.blurple, emoji="📝", custom_id="main_apply")
    async def apply_btn(self, button: Button, interaction: discord.Interaction):
        await interaction.response.send_modal(AppModal())

# --- COMMANDS ---

setup = bot.create_group("setup", "Configure the application system", default_member_permissions=discord.Permissions(administrator=True))

@setup.command(name="role", description="Set the staff role allowed to accept or deny applications.")
async def setup_role(ctx, role: discord.Role):
    config["staff_role_id"] = role.id
    await ctx.respond(f"✅ Staff role set to: `{role.name}`")

@setup.command(name="channel", description="Set the channel where the apply button will be posted.")
async def setup_app_chan(ctx, channel: discord.TextChannel):
    config["app_channel"] = channel.id
    await ctx.respond(f"✅ Application channel set to {channel.mention}")

@setup.command(name="results", description="Set the staff channel where applications are sent for review.")
async def setup_res_chan(ctx, channel: discord.TextChannel):
    config["results_channel"] = channel.id
    await ctx.respond(f"✅ Staff results channel set to {channel.mention}")

@setup.command(name="logs", description="Set the channel where the final accept/deny logs are posted.")
async def setup_log_chan(ctx, channel: discord.TextChannel):
    config["log_channel"] = channel.id
    await ctx.respond(f"✅ Log channel set to {channel.mention}")

@bot.slash_command(name="post", description="Sends the recruitment message to the configured channel.", default_member_permissions=discord.Permissions(administrator=True))
async def post_msg(ctx):
    if not config["app_channel"]:
        return await ctx.respond("❌ Set the application channel first using `/setup channel`.")
    
    channel = bot.get_channel(config["app_channel"])
    embed = discord.Embed(
        title="Lifesteal Fazbear Applications",
        description="Click the button below to start your application process.",
        color=0x992d22
    )
    await channel.send(embed=embed, view=ApplyStartView())
    await ctx.respond("🚀 Recruitment message posted.")

# Render environment variable
token = os.getenv("BOT_TOKEN")
if token:
    bot.run(token)
else:
    print("TOKEN NOT FOUND")
