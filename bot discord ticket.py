import discord
from discord.ui import Button, View
import asyncio
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)

# IDs
ROLE_MEMBRE_ID = 1476712243138920448
ROLE_CUSTOMER_ID = 1476719917255360664
ROLE_VERIFIED2_ID = 1476889969493803164
RULES_CHANNEL_ID = 1476293487228882975
TERMS_CHANNEL_ID = 1476720732711948438
ROLE_STAFF = "Staff"

# Ticket counts
ticket_counts = {"report": 0, "purchase": 0, "support": 0, "giveaway": 0}

# Terms parts
TERMS_PARTS = [
    '📋 **TERMS OF USE**\n─────────────────────────\n\nBy accessing, joining, remaining within, interacting with, browsing, observing, participating in, purchasing from, transacting with, communicating through, or otherwise engaging in any manner whatsoever with this Discord server, any of its channels, sections, categories, systems, automated processes, bots, digital services, digital goods, content structures, community features, transactional mechanisms, or administrative functions, you hereby acknowledge, declare, affirm, represent, warrant, and irrevocably agree that you have read, understood, comprehended, analyzed, and fully accepted these Terms of Use in their entirety without limitation, qualification, objection, contestation, or reservation of any nature whatsoever, and you further acknowledge that your decision to access or remain within the server is voluntary, informed, intentional, and undertaken at your own sole initiative and risk.',
    'You further recognize and accept that these Terms may be modified, updated, amended, supplemented, rewritten, expanded, reduced, replaced, or otherwise altered at any time, for any reason, with or without justification, explanation, notice, warning, announcement, or individualized communication, at the sole, absolute, exclusive, discretionary, and unilateral authority of the server administration, and that it is entirely your responsibility to review these Terms periodically and proactively, and that continued presence within the server or completion of any transaction shall constitute automatic, binding, enforceable, and irrevocable acceptance of any such modification. This server operates as an independent digital entity and is neither affiliated with, endorsed by, sponsored by, nor officially connected to Discord. All services are delivered strictly on an "as is" and "as available" basis without warranties of any kind.',
    'Payment for any and all services must be made in full, in advance, and must be successfully confirmed prior to the initiation or delivery of any service under any circumstance, without exception. Any attempt to reverse a completed transaction, initiate a chargeback, open a dispute, or otherwise undermine the integrity of a completed and delivered transaction shall result in immediate, irreversible, and permanent termination of access to the server and all associated services, without warning or compensation, and may additionally be reported to the relevant payment processor or authority. All sales are final and non-refundable except exclusively in the singular case of a demonstrable duplicate billing caused solely by a confirmed payment processor error.',
    'Access to this server constitutes a revocable privilege granted at the sole discretion of the administration and does not create any ownership interest, partnership, employment relationship, or legally enforceable entitlement beyond the limited scope of the specific digital service purchased. Under no circumstances shall the server owner, administrators, moderators, or any individual associated with the operation of this server be held liable for any direct, indirect, incidental, consequential, punitive, or special damages arising out of or in connection with the use of any service, including but not limited to loss of profits, account suspensions by Discord, loss of data, reputational harm, or any circumstance beyond the reasonable control of the administration.',
    'All content, structures, branding elements, digital assets, and conceptual frameworks associated with this server constitute the exclusive intellectual property of the administration, and any unauthorized reproduction, redistribution, resale, or exploitation of such materials is strictly prohibited. Prices may be modified at any time without notice, and previous transactions do not create entitlement to retroactive adjustments or compensation. You are solely responsible for ensuring your participation complies with all laws applicable within your jurisdiction.',
    'Communication with staff must remain respectful at all times and no response time is guaranteed. The administration reserves the exclusive and final authority to interpret and enforce these Terms. If any provision is determined to be invalid or unenforceable, the remaining provisions shall continue in full force and effect. These Terms constitute the entire agreement between you and the administration and supersede any prior communications or informal understandings.\n\nBy remaining in the server, completing any payment, or otherwise engaging with the community, you irrevocably confirm that you have voluntarily chosen to participate under these conditions, accept all associated risks and limitations, and waive the administration from any claim or dispute inconsistent with these Terms, to the fullest extent permitted by law.\n─────────────────────────'
]

# ── VIEWS ──────────────────────────────────────────────

class RulesView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='✅ Accept the rules', style=discord.ButtonStyle.green, custom_id='accept_rules')
    async def accept(self, interaction: discord.Interaction, button: Button):
        role = interaction.guild.get_role(ROLE_MEMBRE_ID)
        if role in interaction.user.roles:
            await interaction.response.send_message('You have already accepted the rules.', ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message('✅ Rules accepted! You now have access to the server.', ephemeral=True)

class TermsView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='✅ Accept the Terms of Use', style=discord.ButtonStyle.green, custom_id='accept_terms')
    async def accept(self, interaction: discord.Interaction, button: Button):
        role_customer = interaction.guild.get_role(ROLE_CUSTOMER_ID)
        role_verified = interaction.guild.get_role(ROLE_MEMBRE_ID)
        role_verified2 = interaction.guild.get_role(ROLE_VERIFIED2_ID)
        if role_customer in interaction.user.roles:
            await interaction.response.send_message('You have already accepted the Terms of Use.', ephemeral=True)
        else:
            await interaction.user.add_roles(role_customer)
            await interaction.user.add_roles(role_verified2)
            await interaction.user.remove_roles(role_verified)
            await interaction.response.send_message('✅ Terms accepted! You now have access to our Nitro services.', ephemeral=True)

class CloseButton(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.red, custom_id='close_ticket')
    async def close(self, interaction: discord.Interaction, button: Button):
        if not any(role.name == ROLE_STAFF for role in interaction.user.roles):
            await interaction.response.send_message("❌ You don't have permission to close this ticket.", ephemeral=True)
            return
        await interaction.response.send_message("Ticket closed, channel will be deleted in 5 seconds...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Report", emoji="📞", style=discord.ButtonStyle.blurple, custom_id='ticket_report')
    async def report(self, interaction: discord.Interaction, button: Button):
        await create_ticket(interaction, "report", "Report")

    @discord.ui.button(label="Purchase", emoji="💰", style=discord.ButtonStyle.green, custom_id='ticket_purchase')
    async def purchase(self, interaction: discord.Interaction, button: Button):
        await create_ticket(interaction, "purchase", "Purchase")

    @discord.ui.button(label="Support", emoji="❓", style=discord.ButtonStyle.blurple, custom_id='ticket_support')
    async def support(self, interaction: discord.Interaction, button: Button):
        await create_ticket(interaction, "support", "Support")

    @discord.ui.button(label="Giveaway", emoji="🎁", style=discord.ButtonStyle.green, custom_id='ticket_giveaway')
    async def giveaway(self, interaction: discord.Interaction, button: Button):
        await create_ticket(interaction, "giveaway", "Giveaway")

# ── TICKET FUNCTION ────────────────────────────────────

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

# ── EVENTS ─────────────────────────────────────────────

@client.event
async def on_ready():
    client.add_view(RulesView())
    client.add_view(TermsView())
    client.add_view(CloseButton())
    client.add_view(TicketView())
    print(f'Connecté en tant que {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content == '!CUBrules':
        await message.delete()
        await message.channel.send('📜 **DISCORD SERVER RULES**\n─────────────────────────')
        await message.channel.send('─────────────────────────\n**Respect & Behavior**\n─────────────────────────\nRespect all members at all times.\n❌ No insults, harassment, threats, or discrimination.\n❌ No toxic behavior or intentional drama.\n✅ Be polite and respectful.')
        await message.channel.send('─────────────────────────\n**Strictly Prohibited**\n─────────────────────────\n❌ Scamming or any kind of fraud.\n❌ NSFW / 18+ content.\n❌ Spamming (messages, emojis, reactions, mentions).\n❌ Advertising without permission (servers, links, DMs, etc.).\n❌ Sharing personal information (doxxing).')
        await message.channel.send('─────────────────────────\n**Content & Discussions**\n─────────────────────────\nStay on topic in the appropriate channels.\nNo illegal, violent, or shocking content.\nDebates are allowed, but keep them respectful.')
        await message.channel.send('─────────────────────────\n**Username & Profile**\n─────────────────────────\nNo offensive or inappropriate usernames.\nNo NSFW or shocking profile pictures.\nNo impersonation of staff or other members.')
        await message.channel.send('─────────────────────────\n**Voice Channels**\n─────────────────────────\nNo screaming, loud noises, or disruptive behavior.\nNo toxic behavior in voice chat.\nMusic bots only in designated channels (if applicable).')
        await message.channel.send('─────────────────────────\n**Punishments**\n─────────────────────────\nBreaking the rules may result in:\n⚠️ Warning\n🔇 Mute\n🚫 Kick\n🔨 Ban\nModerators reserve the right to decide the appropriate punishment.')
        await message.channel.send('─────────────────────────\n**Staff**\n─────────────────────────\nStaff decisions must be respected.\nDo not argue publicly about punishments.\nIf you have an issue, contact a moderator privately or open a ticket.\n─────────────────────────')
        await message.channel.send(view=RulesView())

    if message.content == '!CUBterms':
        await message.delete()
        for part in TERMS_PARTS:
            await message.channel.send(part)
        await message.channel.send(view=TermsView())

    if message.content == '!CUBticket':
        await message.delete()
        embed = discord.Embed(
            title="Tickets",
            description="Click a button to create a ticket and contact the staff",
            color=0x5865F2
        )
        await message.channel.send(embed=embed, view=TicketView())

client.run(os.environ.get('TOKEN'))
