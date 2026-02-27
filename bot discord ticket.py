import discord
from discord.ui import Button, View, Select
import asyncio
import os
from datetime import datetime, timezone

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.bans = True
client = discord.Client(intents=intents)

# IDs
ROLE_MEMBRE_ID = 1476712243138920448
ROLE_CUSTOMER_ID = 1476719917255360664
ROLE_VERIFIED2_ID = 1476889969493803164
RULES_CHANNEL_ID = 1476293487228882975
TERMS_CHANNEL_ID = 1476720732711948438
ALERT_CHANNEL_ID = 1476925461480083489
ROLE_STAFF_ID = 1476667346386026749
ROLE_STAFF = "Staff"

# Whitelist
whitelist = set()

# Ticket counts
ticket_counts = {"report": 0, "purchase": 0, "support": 0, "giveaway": 0}

# Terms parts
TERMS_PARTS = [
    '📋 **TERMS OF SERVICE**\n─────────────────────────\n\nBy accessing, joining, browsing, observing, interacting with, participating in, communicating through, purchasing from, transacting with, or otherwise engaging in any manner whatsoever with this Discord server, including but not limited to its text channels, voice channels, ticket systems, automated bots, moderation systems, digital services, custom services, informational materials, structural components, operational frameworks, transactional mechanisms, and any associated digital environment operated directly or indirectly by the administration, you hereby acknowledge, represent, warrant, affirm, and irrevocably agree that you have carefully read, fully understood, consciously reviewed, and voluntarily accepted these Terms of Service in their entirety without limitation, condition, reservation, modification, exception, qualification, protest, or objection of any kind.',

    'These Terms may be updated, amended, revised, expanded, reduced, clarified, reformulated, replaced, or otherwise modified at any time, for any reason or no reason at all, at the sole, exclusive, unilateral, and discretionary authority of the administration, without prior notice, warning, explanation, individualized communication, or public announcement, and it shall remain solely your responsibility to review these Terms periodically and proactively. This server operates independently and is not affiliated with, endorsed by, sponsored by, officially connected to, legally partnered with, or otherwise associated with Discord. All services are offered strictly on an "as is," "as available," and "with all faults" basis without warranties of any kind.',

    'Payment for any service, digital product, access privilege, custom order, or transactional engagement must be made in full, in advance, and successfully confirmed prior to initiation, scheduling, preparation, allocation, reservation, processing, or delivery, without exception. All payments are final due to the digital, intangible, irreversible, and non-returnable nature of the services provided, and refunds shall be strictly limited to demonstrable, objectively verifiable technical malfunctions occurring directly during the payment processing stage itself. Any attempt to initiate a fraudulent chargeback, payment dispute, reversal request, or abuse of payment protection systems shall result in immediate and permanent termination of access.',

    'Access to this server constitutes a revocable, conditional, limited privilege rather than a right, ownership interest, or contractual guarantee of permanence. The administration reserves the absolute and unrestricted authority to suspend, restrict, limit, or permanently revoke access at any time, with or without explanation, justification, prior warning, or compensation. Under no circumstances shall the server owner, founders, administrators, moderators, assistants, affiliates, contractors, or any individual associated with the server be held liable for any direct, indirect, incidental, consequential, punitive, or exemplary damages arising out of or in connection with the use of any service.',

    'You acknowledge that the administration retains the unrestricted right to implement monitoring systems, logging mechanisms, ticket archiving procedures, automated moderation bots, anti-fraud detection tools, and transactional verification protocols. Any data, communication, ticket transcript, transaction record, or interaction history generated within the server may be retained for an indefinite duration where deemed reasonably necessary. You further acknowledge that force majeure events, including acts of God, natural disasters, governmental restrictions, cybersecurity attacks, infrastructure failures, or any event beyond the reasonable control of the administration, shall not give rise to liability, compensation, or refund obligation.',

    'You expressly waive any claim based on alleged reliance, expectation interest, promissory estoppel, implied continuity, informal assurance, or subjective interpretation of staff communications that contradict these explicit written Terms. You irrevocably waive any right to participate in class actions, collective arbitration, mass claims, or representative litigation of any kind. Any dispute shall be resolved individually and exclusively through binding arbitration in a jurisdiction determined solely by the administration, with any claim required to be brought within one year from the date it arises.',

    'You agree to indemnify, defend, and hold harmless the administration from and against any and all claims, liabilities, damages, losses, costs, expenses, penalties, or legal fees arising from your breach of these Terms, misuse of services, violation of applicable laws, infringement of intellectual property rights, fraudulent activity, or abusive conduct. These Terms constitute the entire agreement between you and the administration and supersede all prior communications, representations, or agreements, whether oral or written.\n\nBy remaining in the server or completing any transaction, you irrevocably acknowledge that you voluntarily assume all associated risks and agree to be bound fully and completely by these Terms to the maximum extent permitted by law.\n─────────────────────────'
]

# ── ALT DETECTION ──────────────────────────────────────

def get_suspicion_score(member):
    score = 0
    reasons = []

    account_age = (datetime.now(timezone.utc) - member.created_at).days
    if account_age < 7:
        score += 4
        reasons.append(f'Account created **{account_age}** day(s) ago')
    elif account_age < 30:
        score += 2
        reasons.append(f'Account created **{account_age}** days ago')

    if member.avatar is None:
        score += 2
        reasons.append('No profile picture')

    username = member.name.lower()
    digit_ratio = sum(c.isdigit() for c in username) / max(len(username), 1)
    if digit_ratio > 0.4:
        score += 2
        reasons.append(f'Suspicious username (`{member.name}`)')

    if len(member.name) < 4:
        score += 1
        reasons.append('Very short username')

    return score, reasons

# ── WHITELIST SELECT ────────────────────────────────────

class WhitelistSelect(Select):
    def __init__(self, banned_users):
        options = [
            discord.SelectOption(label=f'{user.user.name}', value=str(user.user.id), description=f'ID: {user.user.id}')
            for user in banned_users[:25]
        ]
        super().__init__(placeholder='Select a user to unban and whitelist...', options=options)

    async def callback(self, interaction: discord.Interaction):
        user_id = int(self.values[0])
        whitelist.add(user_id)
        await interaction.guild.unban(discord.Object(id=user_id), reason='Whitelisted by staff')
        await interaction.response.send_message(f'✅ User has been unbanned and whitelisted.', ephemeral=True)

class WhitelistView(View):
    def __init__(self, banned_users):
        super().__init__(timeout=60)
        self.add_item(WhitelistSelect(banned_users))

# ── VIEWS ──────────────────────────────────────────────

class RulesView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='✅ Accept the rules', style=discord.ButtonStyle.green, custom_id='accept_rules')
    async def accept(self, interaction: discord.Interaction, button: Button):
        member = interaction.user
        role = interaction.guild.get_role(ROLE_MEMBRE_ID)

        if role in member.roles:
            await interaction.response.send_message('You have already accepted the rules.', ephemeral=True)
            return

        if member.id not in whitelist:
            score, reasons = get_suspicion_score(member)
            if score >= 4:
                channel = client.get_channel(ALERT_CHANNEL_ID)
                staff_role = interaction.guild.get_role(ROLE_STAFF_ID)
                embed = discord.Embed(
                    title='『🔍』𝗗𝗼𝘂𝗯𝗹𝗲 𝗮𝗰𝗰𝗼𝘂𝗻𝘁 𝗗𝗲𝘁𝗲𝗰𝘁𝗲𝗱',
                    color=0xFF0000
                )
                embed.add_field(name='User', value=f'{member.mention} (`{member.name}` | `{member.id}`)', inline=False)
                embed.add_field(name='Suspicion Score', value=f'**{score}/9**', inline=False)
                embed.add_field(name='Reasons', value='\n'.join(f'• {r}' for r in reasons), inline=False)
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.timestamp = datetime.now(timezone.utc)
                await channel.send(content=f'{staff_role.mention}', embed=embed)

                try:
                    await member.send(
                        '❌ You have been banned from the server.\n\n'
                        '**Reason:** Your account has been detected as a potential alt/double account.\n'
                        'Using alternate accounts to bypass rules, bans, or restrictions is strictly prohibited.\n\n'
                        'If you believe this is a mistake, please contact the staff.'
                    )
                except:
                    pass

                await interaction.response.send_message('❌ Your account has been flagged as an alt account and you have been banned.', ephemeral=True)
                await member.ban(reason=f'Suspected alt account (score: {score}/9) — Accepted rules')
                return

        await member.add_roles(role)
        await interaction.response.send_message('✅ Rules accepted! You now have access to the server.', ephemeral=True)

class TermsView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='✅ Accept the Terms of Service', style=discord.ButtonStyle.green, custom_id='accept_terms')
    async def accept(self, interaction: discord.Interaction, button: Button):
        role_customer = interaction.guild.get_role(ROLE_CUSTOMER_ID)
        role_verified = interaction.guild.get_role(ROLE_MEMBRE_ID)
        role_verified2 = interaction.guild.get_role(ROLE_VERIFIED2_ID)
        if role_customer in interaction.user.roles:
            await interaction.response.send_message('You have already accepted the Terms of Service.', ephemeral=True)
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

    if message.content == '!CUBclear':
        if not any(role.name == ROLE_STAFF for role in message.author.roles):
            await message.channel.send('❌ You do not have permission to use this command.', delete_after=5)
            return
        await message.channel.purge()

    if message.content == '!CUBwhitelist':
        if not any(role.name == ROLE_STAFF for role in message.author.roles):
            await message.channel.send('❌ You do not have permission to use this command.', delete_after=5)
            return
        await message.delete()
        banned_users = [entry async for entry in message.guild.bans()]
        if not banned_users:
            await message.channel.send('No banned users found.', delete_after=5)
            return
        await message.channel.send('Select a user to unban and whitelist :', view=WhitelistView(banned_users), delete_after=60)

    if message.content == '!CUBrules':
        await message.delete()
        await message.channel.send('📜 **DISCORD SERVER RULES**\n─────────────────────────')
        await message.channel.send('─────────────────────────\n**Respect & Behavior**\n─────────────────────────\nRespect all members at all times.\n❌ No insults, harassment, threats, or discrimination.\n❌ No toxic behavior or intentional drama.\n✅ Be polite and respectful.')
        await message.channel.send('─────────────────────────\n**Strictly Prohibited**\n─────────────────────────\n❌ Scamming or any kind of fraud.\n❌ NSFW / 18+ content.\n❌ Spamming (messages, emojis, reactions, mentions).\n❌ Advertising without permission (servers, links, DMs, etc.).\n❌ Sharing personal information (doxxing).\n❌ Using alternate accounts (alt accounts) to bypass rules, bans, or restrictions.')
        await message.channel.send('─────────────────────────\n**Content & Discussions**\n─────────────────────────\nStay on topic in the appropriate channels.\nNo illegal, violent, or shocking content.\nDebates are allowed, but keep them respectful.')
        await message.channel.send('─────────────────────────\n**Username & Profile**\n─────────────────────────\nNo offensive or inappropriate usernames.\nNo NSFW or shocking profile pictures.\nNo impersonation of staff or other members.')
        await message.channel.send('─────────────────────────\n**Voice Channels**\n─────────────────────────\nNo screaming, loud noises, or disruptive behavior.\nNo toxic behavior in voice chat.\nMusic bots only in designated channels (if applicable).')
        await message.channel.send('─────────────────────────\n**Punishments**\n─────────────────────────\nBreaking the rules may result in:\n⚠️ Warning\n🔇 Mute\n🚫 Kick\n🔨 Ban\n\nModerators reserve the right to decide the appropriate punishment.')
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
