import discord
from discord.ui import View, Button
import asyncio
import os

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

ticket_counts = {"report": 0, "purchase": 0, "support": 0, "giveaway": 0}

ROLE_STAFF = "Staff"

class CloseButton(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.red)
    async def close(self, interaction: discord.Interaction, button: Button):
        if not any(role.name == ROLE_STAFF for role in interaction.user.roles):
            await interaction.response.send_message("❌ You don't have permission to close this ticket.", ephemeral=True)
            return
        await interaction.response.send_message("Ticket closed, channel will be deleted in 5 seconds...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

async def create_ticket(interaction, ticket_type, label):
    guild = interaction.guild
    category = discord.utils.get(guild.categories, name="╰┈➤ 𝗧𝗶𝗰𝗸𝗲𝘁")

    ticket_counts[ticket_type] += 1
    number = ticket_counts[ticket_type]

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
    }

    channel = await guild.create_text_channel(
        name=f"{ticket_type}-{number}",
        category=category,
        overwrites=overwrites
    )

    await channel.send(
        f"👋 Welcome {interaction.user.mention} !\n\nCategory : **{label}**\n\nA staff member will reply soon.",
        view=CloseButton()
    )

    await interaction.response.send_message(f"✅ Your ticket has been created : {channel.mention}", ephemeral=True)

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Report", emoji="📞", style=discord.ButtonStyle.blurple)
    async def report(self, interaction: discord.Interaction, button: Button):
        await create_ticket(interaction, "report", "Report")

    @discord.ui.button(label="Purchase", emoji="💰", style=discord.ButtonStyle.green)
    async def purchase(self, interaction: discord.Interaction, button: Button):
        await create_ticket(interaction, "purchase", "Purchase")

    @discord.ui.button(label="Support", emoji="❓", style=discord.ButtonStyle.blurple)
    async def support(self, interaction: discord.Interaction, button: Button):
        await create_ticket(interaction, "support", "Support")

    @discord.ui.button(label="Giveaway", emoji="🎁", style=discord.ButtonStyle.green)
    async def giveaway(self, interaction: discord.Interaction, button: Button):
        await create_ticket(interaction, "giveaway", "Giveaway")

@client.event
async def on_ready():
    print(f'Connecté en tant que {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content == '!ticket':
        await message.delete()

        embed = discord.Embed(
            title="Tickets",
            description="Click a button to create a ticket and contact the staff",
            color=0x5865F2
        )

        await message.channel.send(embed=embed, view=TicketView())

client.run(os.environ.get('TOKEN'))