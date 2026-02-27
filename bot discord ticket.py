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

# Blacklist
blacklist = set()

# Ticket counts
ticket_counts = {"report": 0, "purchase": 0, "support": 0, "giveaway": 0}

# Giveaways actifs : {message_id: {...}}
active_giveaways = {}

def parse_duration(duration_str):
    import re
    duration_str = duration_str.strip().lower()
    pattern = re.findall(r'(\d+)\s*([smhd])', duration_str)
    if not pattern:
        return None
    seconds = 0
    units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
    for value, unit in pattern:
        seconds += int(value) * units[unit]
    return seconds if seconds > 0 else None

# Terms parts (all under 2000 characters for Discord)
TERMS_PARTS = [
    # Part 1 — Acceptance (1508 chars ✅)
    '📋 **TERMS OF SERVICE**\n─────────────────────────\n\n'
    'By accessing, joining, browsing, observing, interacting with, participating in, communicating through, purchasing from, transacting with, or otherwise engaging in any manner whatsoever with this Discord server, including but not limited to its text channels, voice channels, ticket systems, automated bots, moderation systems, digital services, custom services, informational materials, structural components, operational frameworks, transactional mechanisms, and any associated digital environment operated directly or indirectly by the administration, you hereby acknowledge, represent, warrant, affirm, and irrevocably agree that you have carefully read, fully understood, consciously reviewed, and voluntarily accepted these Terms of Service in their entirety without limitation, condition, reservation, modification, exception, qualification, protest, or objection of any kind, and you further acknowledge that your decision to access or remain within this server is undertaken freely, knowingly, intentionally, and at your own sole risk and discretion. You expressly agree that these Terms constitute a legally binding agreement between you and the administration governing your access to and use of the server and all related services, and that your continued presence within the server environment, whether active or passive, visible or invisible, logged in or idle, shall constitute automatic, binding, enforceable, and irrevocable acceptance of these Terms and any subsequent modifications thereto.',

    # Part 2a — Modifications (split from original part 2)
    'These Terms may be updated, amended, revised, expanded, reduced, clarified, reformulated, replaced, or otherwise modified at any time, for any reason or no reason at all, at the sole, exclusive, unilateral, and discretionary authority of the administration, without prior notice, warning, explanation, individualized communication, or public announcement, and it shall remain solely your responsibility to review these Terms periodically and proactively; your continued access to or use of the server following any such modification shall constitute conclusive evidence of your acceptance of the revised Terms regardless of whether you have actually reviewed the updated version. You acknowledge that ignorance of the Terms, partial reading, misunderstanding, or failure to review updates does not exempt you from compliance and shall not be accepted as a defense under any circumstance.',

    # Part 2b — No warranty (split from original part 2)
    'This server operates independently and is not affiliated with, endorsed by, sponsored by, officially connected to, legally partnered with, or otherwise associated with Discord, and any belief, implication, or representation suggesting otherwise is expressly denied and disclaimed. All services, digital goods, access privileges, informational content, automation processes, structural systems, and transactional features provided through this server are offered strictly on an "as is," "as available," and "with all faults" basis without warranties, guarantees, assurances, commitments, or representations of any kind, whether express, implied, statutory, customary, oral, written, inferred, assumed, or otherwise constructed, including but not limited to implied warranties of merchantability, fitness for a particular purpose, non-infringement, reliability, uninterrupted availability, error-free operation, compatibility with third-party platforms, legality in your jurisdiction, financial profitability, technical stability, security integrity, or specific outcomes.',

    # Part 3 — Payments (1876 chars ✅)
    'Payment for any service, digital product, access privilege, custom order, or transactional engagement must be made in full, in advance, and successfully confirmed prior to initiation, scheduling, preparation, allocation, reservation, processing, or delivery, without exception, installment arrangement, deferred agreement, partial understanding, verbal commitment, informal message, private conversation, or implied promise overriding this requirement. No staff member, moderator, automated system, or representative shall be deemed to have waived this condition unless such waiver is explicitly and formally documented in a publicly issued written amendment to these Terms. All payments are final due to the digital, intangible, irreversible, and non-returnable nature of the services provided, and refunds shall be strictly limited to demonstrable, objectively verifiable technical malfunctions occurring directly during the payment processing stage itself. Dissatisfaction, misunderstanding, incorrect expectations, personal financial hardship, failure to read descriptions, misinterpretation of service scope, perceived delay, external platform interference, third-party misconduct, bans resulting from rule violations, pricing adjustments, or any reason not directly attributable to a confirmed transactional malfunction shall not constitute valid grounds for refund. Any attempt to initiate a fraudulent chargeback, payment dispute, reversal request, false non-delivery claim, or abuse of payment protection systems shall result in immediate and permanent termination of access.',

    # Part 4a — Revocable access (split from original part 4)
    'Access to this server constitutes a revocable, conditional, limited privilege rather than a right, ownership interest, contractual guarantee of permanence, employment relationship, partnership, joint venture, agency agreement, fiduciary duty, franchise, or entitlement of any form. The administration reserves the absolute and unrestricted authority to suspend, restrict, limit, or permanently revoke access at any time, with or without explanation, justification, prior warning, or compensation, if deemed necessary for operational integrity, community protection, reputational safeguarding, fraud prevention, regulatory compliance, security maintenance, risk mitigation, or any other reason considered sufficient by the administration in its sole discretion.',

    # Part 4b — Liability limitation (split from original part 4)
    'Under no circumstances shall the server owner, founders, administrators, moderators, assistants, affiliates, contractors, successors, assigns, representatives, collaborators, or any individual or entity associated directly or indirectly with the server be held liable for any direct, indirect, incidental, consequential, punitive, exemplary, financial, reputational, digital, virtual, physical, material, or immaterial damages arising out of or in connection with the use of, inability to use, interruption of, suspension of, modification of, or termination of any service or feature, including but not limited to loss of profits, revenue, business opportunity, data, digital assets, account standing, community reputation, algorithmic visibility, platform access, or third-party relationships, regardless of the legal theory invoked and to the maximum extent permitted by applicable law.',

    # Part 5a — Monitoring & data retention (split from original part 5)
    'You acknowledge that the administration retains the unrestricted right to implement monitoring systems, logging mechanisms, ticket archiving procedures, automated moderation bots, anti-fraud detection tools, behavioral analysis systems, and transactional verification protocols for the purposes of security, operational integrity, fraud prevention, dispute resolution, quality control, and regulatory compliance. Any data, communication, ticket transcript, transaction record, message log, payment confirmation, or interaction history generated within the server may be retained for an indefinite duration where deemed reasonably necessary for administrative, evidentiary, protective, or compliance-related purposes. You agree that such retention does not constitute surveillance beyond reasonable operational necessity and does not create liability for the administration.',

    # Part 5b — Service changes & force majeure (split from original part 5)
    'The administration may, at its sole discretion, modify service structures, pricing models, access tiers, benefit allocations, feature availability, automation logic, or community privileges without incurring liability for perceived loss of value, expectation misalignment, or comparative disadvantage relative to prior conditions. No historical configuration of services shall create an ongoing obligation to maintain identical structures in the future. Force majeure events shall include, without limitation, acts of God, natural disasters, earthquakes, floods, fires, pandemics, epidemics, governmental restrictions, regulatory changes, sanctions, embargoes, civil unrest, riots, war, terrorism, labor disputes, infrastructure failures, internet backbone outages, DNS failures, hosting provider disruptions, data center incidents, cybersecurity attacks, ransomware incidents, distributed denial-of-service attacks, third-party API shutdowns, payment processor suspensions, platform-wide moderation sweeps, or any event beyond the reasonable control of the administration, and no such event shall give rise to liability, compensation, refund obligation, or damages claim.',

    # Part 6 — Waiver & liability cap (1631 chars ✅)
    'You expressly waive any claim based on alleged reliance, expectation interest, promissory estoppel, implied continuity, informal assurance, community assumption, or subjective interpretation of staff communications that contradict the explicit written Terms contained herein. Only formally published written provisions shall be considered authoritative and binding. Any informal statement, casual message, estimated timeframe, preliminary discussion, or speculative comment made by any staff member shall not constitute a legally enforceable guarantee, representation, or contractual commitment.\n\n'
    'To the maximum extent permitted by applicable law, the total cumulative liability of the administration shall not exceed the total amount actually paid by you, if any, for the specific service directly giving rise to the claim. You irrevocably waive any right to participate in class actions, collective arbitration, mass claims, or representative litigation of any kind. You further acknowledge that electronic acceptance of these Terms through continued server presence constitutes valid and binding agreement equivalent to a handwritten signature.',

    # Part 7 — Indemnification & final agreement (1630 chars ✅)
    'You agree to indemnify, defend, and hold harmless the administration from and against any and all claims, liabilities, damages, losses, costs, expenses, penalties, fines, proceedings, investigations, or legal fees arising from your breach of these Terms, misuse of services, violation of applicable laws, infringement of intellectual property rights, fraudulent activity, abusive conduct, or unauthorized exploitation of server materials.\n\n'
    'Any dispute shall be resolved exclusively through confidential binding arbitration in a jurisdiction determined solely by the administration. You waive any right to trial by jury or participation in class actions. Any claim must be brought within one (1) year from the date it arises, after which it shall be permanently barred. If any provision is deemed invalid or unenforceable, the remaining provisions shall remain in full force and effect.\n\n'
    'These Terms constitute the entire agreement between you and the administration and supersede all prior communications, representations, or agreements, whether oral or written. By remaining in the server or completing any transaction, you irrevocably acknowledge that you voluntarily assume all associated risks and agree to be bound fully and completely by these Terms to the maximum extent permitted by law.\n─────────────────────────'
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

# ── BLACKLIST SELECT ────────────────────────────────────

class BlacklistSelect(Select):
    def __init__(self, members, search_query=''):
        filtered = [m for m in members if search_query.lower() in m.name.lower()] if search_query else members
        filtered = filtered[:25]

        if filtered:
            options = [
                discord.SelectOption(
                    label=f'{m.name}'[:100],
                    value=str(m.id),
                    description=(('🔴 Blacklisted' if m.id in blacklist else '') + (' ⚪ Whitelisted' if m.id in whitelist else '') + f' | ID: {m.id}')[:100]
                )
                for m in filtered
            ]
        else:
            options = [discord.SelectOption(label='No results found', value='none')]

        super().__init__(placeholder='Select a member to blacklist/unblacklist...', options=options)
        self.members = members

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == 'none':
            await interaction.response.send_message('❌ No member found.', ephemeral=True)
            return

        user_id = int(self.values[0])

        if user_id in blacklist:
            blacklist.discard(user_id)
            await interaction.response.send_message('✅ User has been **removed from the blacklist**.', ephemeral=True)
        else:
            blacklist.add(user_id)
            whitelist.discard(user_id)
            try:
                await interaction.guild.ban(discord.Object(id=user_id), reason='Added to blacklist by staff')
                await interaction.response.send_message('🔨 User has been **blacklisted and banned**.', ephemeral=True)
            except discord.NotFound:
                await interaction.response.send_message('🔨 User **added to blacklist** (not currently in server).', ephemeral=True)
            except discord.Forbidden:
                await interaction.response.send_message('❌ Could not ban the user (missing permissions).', ephemeral=True)

class BlacklistSearchModal(discord.ui.Modal, title='Search Member'):
    search = discord.ui.TextInput(label='Username (partial or full)', placeholder='e.g. John', required=True, max_length=32)

    def __init__(self, members):
        super().__init__()
        self.members = members

    async def on_submit(self, interaction: discord.Interaction):
        query = self.search.value
        view = BlacklistView(self.members, search_query=query)
        await interaction.response.send_message(
            f'🔍 Results for **"{query}"** — select a member:',
            view=view,
            ephemeral=True
        )

class BlacklistView(View):
    def __init__(self, members, search_query=''):
        super().__init__(timeout=60)
        self.members = members
        self.search_query = search_query
        self.add_item(BlacklistSelect(members, search_query))

    @discord.ui.button(label='🔍 Search by name', style=discord.ButtonStyle.blurple)
    async def search_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(BlacklistSearchModal(self.members))

# ── GIVEAWAY ───────────────────────────────────────────

class GiveawayModal(discord.ui.Modal, title='🎉 Create a Giveaway'):
    g_title    = discord.ui.TextInput(label='Title', placeholder='Ex: Nitro Giveaway', max_length=100)
    g_prize    = discord.ui.TextInput(label='Prize / Description', placeholder='Ex: 1 Month Discord Nitro', max_length=200)
    g_winners  = discord.ui.TextInput(label='Number of winners', placeholder='Ex: 1', max_length=2)
    g_duration = discord.ui.TextInput(label='Duration (leave empty = manual end)', placeholder='Ex: 1h, 30m, 2d — or leave blank', required=False, max_length=20)
    g_conditions = discord.ui.TextInput(label='Conditions (optional)', placeholder='Ex: role:Customer, messages:10 — or leave blank', required=False, max_length=200)

    async def on_submit(self, interaction: discord.Interaction):
        # Validation nb gagnants
        try:
            winners_count = int(self.g_winners.value.strip())
            if winners_count < 1:
                raise ValueError
        except ValueError:
            await interaction.response.send_message('❌ Number of winners must be a valid integer ≥ 1.', ephemeral=True)
            return

        # Validation durée
        duration_raw = self.g_duration.value.strip()
        duration_seconds = None
        end_time = None
        if duration_raw:
            duration_seconds = parse_duration(duration_raw)
            if duration_seconds is None:
                await interaction.response.send_message('❌ Invalid duration format. Use: `1h`, `30m`, `2d`, `1h30m`, or leave blank for manual end.', ephemeral=True)
                return
            end_time = datetime.now(timezone.utc).timestamp() + duration_seconds

        # Parse conditions
        conditions = {}
        conditions_raw = self.g_conditions.value.strip()
        if conditions_raw:
            for part in conditions_raw.split(','):
                part = part.strip()
                if ':' in part:
                    key, val = part.split(':', 1)
                    conditions[key.strip().lower()] = val.strip()

        # Build embed
        embed = discord.Embed(
            title=f'🎉 {self.g_title.value}',
            color=0xF1C40F
        )
        embed.add_field(name='🏆 Prize', value=self.g_prize.value, inline=False)
        embed.add_field(name='👥 Winners', value=str(winners_count), inline=True)
        if end_time:
            embed.add_field(name='⏰ Ends', value=f'<t:{int(end_time)}:R>', inline=True)
        else:
            embed.add_field(name='⏰ Duration', value='Manual end by staff', inline=True)

        if conditions:
            cond_display = []
            for k, v in conditions.items():
                if k == 'role':
                    cond_display.append(f'• Required role: **{v}**')
                elif k == 'messages':
                    cond_display.append(f'• Minimum messages: **{v}**')
                else:
                    cond_display.append(f'• {k}: **{v}**')
            embed.add_field(name='📋 Conditions', value='\n'.join(cond_display), inline=False)

        embed.set_footer(text='React with 🎉 to participate!')
        embed.timestamp = datetime.now(timezone.utc)

        await interaction.response.send_message('✅ Giveaway created!', ephemeral=True)
        giveaway_msg = await interaction.channel.send(embed=embed)
        await giveaway_msg.add_reaction('🎉')

        # Stocker le giveaway
        active_giveaways[giveaway_msg.id] = {
            'channel_id': interaction.channel.id,
            'title': self.g_title.value,
            'prize': self.g_prize.value,
            'winners_count': winners_count,
            'end_time': end_time,
            'conditions': conditions,
            'host_id': interaction.user.id,
            'ended': False
        }

        # Timer automatique si durée définie
        if duration_seconds:
            asyncio.create_task(auto_end_giveaway(giveaway_msg.id, duration_seconds))

async def auto_end_giveaway(message_id, delay):
    await asyncio.sleep(delay)
    if message_id in active_giveaways and not active_giveaways[message_id]['ended']:
        await end_giveaway(message_id)

async def end_giveaway(message_id):
    data = active_giveaways.get(message_id)
    if not data or data['ended']:
        return
    data['ended'] = True

    channel = client.get_channel(data['channel_id'])
    if not channel:
        return

    try:
        message = await channel.fetch_message(message_id)
    except:
        return

    # Récupérer les participants (réaction 🎉)
    participants = []
    for reaction in message.reactions:
        if str(reaction.emoji) == '🎉':
            async for user in reaction.users():
                if not user.bot:
                    # Vérifier conditions
                    guild = channel.guild
                    member = guild.get_member(user.id)
                    if member is None:
                        continue

                    conditions = data.get('conditions', {})
                    eligible = True

                    # Condition role
                    if 'role' in conditions:
                        required_role_name = conditions['role'].lower()
                        if not any(r.name.lower() == required_role_name for r in member.roles):
                            eligible = False

                    # Condition messages (approximation via joined_at — Discord ne donne pas le vrai count sans DB)
                    if 'messages' in conditions:
                        pass  # Nécessite une DB pour tracker les messages, ignoré ici

                    if eligible:
                        participants.append(user)

    # Notifier le staff en DM avec la liste des participants (secret)
    host = guild.get_member(data['host_id'])
    winners_count = data['winners_count']

    if not participants:
        await channel.send(f'🎉 **{data["title"]}** — No eligible participants. Giveaway cancelled.')
        if host:
            await host.send(f'🎉 Giveaway **{data["title"]}** ended with no eligible participants.')
        return

    # Envoyer la liste des participants au staff en DM (secret)
    participants_list = '\n'.join([f'• {u.name} (`{u.id}`)' for u in participants])
    if host:
        try:
            dm_embed = discord.Embed(
                title=f'🎉 Giveaway — {data["title"]}',
                description=f'**{len(participants)}** eligible participant(s):\n\n{participants_list[:3000]}',
                color=0xF1C40F
            )
            dm_embed.add_field(name='Winners to pick', value=str(winners_count), inline=True)
            dm_embed.add_field(
                name='How to pick',
                value=f'Use `!CUBgwpick {message_id} @user1 @user2...` to manually announce the winner(s).',
                inline=False
            )
            await host.send(embed=dm_embed)
        except:
            pass

    # Mettre à jour l'embed principal
    embed = message.embeds[0] if message.embeds else discord.Embed(title=data['title'])
    embed.color = 0x95A5A6
    embed.set_footer(text='Giveaway ended — Winner selection in progress...')
    await message.edit(embed=embed)
    await channel.send(f'🎉 **{data["title"]}** has ended! The winner will be announced shortly.')

class GiveawayStartView(View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label='🎉 Open Giveaway Form', style=discord.ButtonStyle.green)
    async def open_form(self, interaction: discord.Interaction, button: Button):
        if not any(role.name == ROLE_STAFF for role in interaction.user.roles):
            await interaction.response.send_message('❌ No permission.', ephemeral=True)
            return
        await interaction.response.send_modal(GiveawayModal())

class GiveawayEndView(View):
    def __init__(self, message_id):
        super().__init__(timeout=None)
        self.message_id = message_id

    @discord.ui.button(label='🛑 End Giveaway', style=discord.ButtonStyle.red)
    async def end_btn(self, interaction: discord.Interaction, button: Button):
        if not any(role.name == ROLE_STAFF for role in interaction.user.roles):
            await interaction.response.send_message('❌ No permission.', ephemeral=True)
            return
        data = active_giveaways.get(self.message_id)
        if not data or data['ended']:
            await interaction.response.send_message('❌ This giveaway is already ended or does not exist.', ephemeral=True)
            return
        await interaction.response.send_message('✅ Ending giveaway...', ephemeral=True)
        await end_giveaway(self.message_id)

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
async def on_member_join(member):
    if member.id in blacklist:
        try:
            await member.send(
                '❌ You have been banned from this server.\n\n'
                '**Reason:** You are blacklisted and cannot join this server.\n'
                'If you believe this is a mistake, please contact the administration.'
            )
        except:
            pass
        await member.ban(reason='Blacklisted user — automatic ban on join')

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

    if message.content == '!CUBblacklist':
        if not any(role.name == ROLE_STAFF for role in message.author.roles):
            await message.channel.send('❌ You do not have permission to use this command.', delete_after=5)
            return
        await message.delete()
        members = [m for m in message.guild.members if not m.bot]
        if not members:
            await message.channel.send('No members found.', delete_after=5)
            return
        blacklisted_count = len(blacklist)
        await message.channel.send(
            f'🔴 **Blacklist** — {blacklisted_count} user(s) currently blacklisted.\nSelect a member to blacklist or unblacklist:',
            view=BlacklistView(members),
            delete_after=60
        )

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

    if message.content == '!CUBgiveaway':
        if not any(role.name == ROLE_STAFF for role in message.author.roles):
            await message.channel.send('❌ You do not have permission to use this command.', delete_after=5)
            return
        await message.delete()
        await message.channel.send(
            '🎉 **Giveaway Setup** — Fill in the form below.\n'
            '**Conditions format:** `role:NomDuRole, messages:10` — leave blank for no conditions.',
            delete_after=30
        )
        # Ouvre le modal via un bouton intermédiaire
        view = GiveawayStartView()
        await message.channel.send('👇 Click to open the giveaway form:', view=view, delete_after=60)

    # !CUBgwend <message_id>
    if message.content.startswith('!CUBgwend'):
        if not any(role.name == ROLE_STAFF for role in message.author.roles):
            await message.channel.send('❌ You do not have permission.', delete_after=5)
            return
        parts = message.content.split()
        if len(parts) < 2:
            await message.channel.send('❌ Usage: `!CUBgwend <message_id>`', delete_after=5)
            return
        try:
            msg_id = int(parts[1])
        except ValueError:
            await message.channel.send('❌ Invalid message ID.', delete_after=5)
            return
        if msg_id not in active_giveaways:
            await message.channel.send('❌ No active giveaway with this ID.', delete_after=5)
            return
        await message.delete()
        await end_giveaway(msg_id)

    # !CUBgwpick <message_id> @winner1 @winner2...
    if message.content.startswith('!CUBgwpick'):
        if not any(role.name == ROLE_STAFF for role in message.author.roles):
            await message.channel.send('❌ You do not have permission.', delete_after=5)
            return
        parts = message.content.split()
        if len(parts) < 3:
            await message.channel.send('❌ Usage: `!CUBgwpick <message_id> @winner1 @winner2...`', delete_after=5)
            return
        try:
            msg_id = int(parts[1])
        except ValueError:
            await message.channel.send('❌ Invalid message ID.', delete_after=5)
            return

        data = active_giveaways.get(msg_id)
        if not data:
            await message.channel.send('❌ Giveaway not found.', delete_after=5)
            return

        winners = message.mentions
        if not winners:
            await message.channel.send('❌ Please mention the winner(s).', delete_after=5)
            return

        await message.delete()

        winners_mentions = ' '.join([w.mention for w in winners])
        embed = discord.Embed(
            title=f'🎉 Giveaway Results — {data["title"]}',
            description=f'**Prize:** {data["prize"]}\n\n🏆 **Winner(s):** {winners_mentions}',
            color=0x2ECC71
        )
        embed.set_footer(text='Congratulations!')
        embed.timestamp = datetime.now(timezone.utc)
        await message.channel.send(content=winners_mentions, embed=embed)

        # Notifier chaque gagnant en DM
        for winner in winners:
            try:
                await winner.send(
                    f'🎉 Congratulations! You won the **{data["title"]}** giveaway!\n'
                    f'**Prize:** {data["prize"]}\n'
                    f'Please contact the staff to claim your prize.'
                )
            except:
                pass

client.run(os.environ.get('TOKEN'))
