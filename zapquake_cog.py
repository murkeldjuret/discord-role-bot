import discord
from discord import app_commands
from discord.ext import commands
import math
 
# ─────────────────────────────────────────────
#  ZapQuake damage formulas (matches clashify)
# ─────────────────────────────────────────────
 
LIGHTNING_DMG = {
    1:300, 2:320, 3:340, 4:360, 5:380,
    6:400, 7:420, 8:450, 9:480, 10:510,
    11:540, 12:570, 13:600,
}
 
def earthquake_pct(level: int) -> float:
    """First EQ destroys this % of remaining HP."""
    base = {1:0.14, 2:0.17, 3:0.21, 4:0.25, 5:0.30, 6:0.35, 7:0.40, 8:0.45}
    return base.get(level, 0.14)
 
def subsequent_eq_pct(level: int) -> float:
    return earthquake_pct(level) / 3.0
 
# Equipment one-shot damage
EQUIPMENT_DMG = {
    "spiky_ball":    {1:50,3:100,6:150,9:200,12:250,15:300,18:350,21:400,24:450,27:500},
    "giant_arrow":   {1:100,3:150,6:200,9:250,12:300,15:350,18:400},
    "seeking_shield":{1:80,3:120,6:160,9:200,12:240,15:280,18:320},
    "fireball":      {1:150,3:200,6:250,9:300,12:350,15:400,18:450,21:500,24:550,27:600},
    "flame_blower":  {1:50,3:80,6:120,9:160,12:200,15:240,18:280},
    "rocket_backpack":{1:100,3:150,6:200,9:250,12:300,15:350,18:400,21:450,24:500,27:550},
}
 
EQUIPMENT_MAX = {
    "spiky_ball": 27, "giant_arrow": 18, "seeking_shield": 18,
    "fireball": 27, "flame_blower": 18, "rocket_backpack": 27,
}
 
EQUIPMENT_LABELS = {
    "spiky_ball": "Spiky Ball",
    "giant_arrow": "Giant Arrow",
    "seeking_shield": "Seeking Shield",
    "fireball": "Fireball",
    "flame_blower": "Flame Blower",
    "rocket_backpack": "Rocket Backpack",
}
 
EQUIPMENT_EMOJI = {
    "spiky_ball": "⚡",
    "giant_arrow": "🏹",
    "seeking_shield": "🛡️",
    "fireball": "🔥",
    "flame_blower": "💨",
    "rocket_backpack": "🚀",
}
 
def get_equipment_dmg(key: str, level: int) -> int:
    table = EQUIPMENT_DMG.get(key, {})
    best = 0
    for lvl, dmg in table.items():
        if lvl <= level:
            best = dmg
    return best
 
# ─────────────────────────────────────────────
#  Defense HP tables (max TH18 values)
#  Format: {defense: [(level_label, hp), ...]}
# ─────────────────────────────────────────────
 
DEFENSES = {
    "Eagle Artillery":   [(1,5000),(2,5500),(3,6000),(4,6500),(5,7000),(6,7500),(7,8000)],
    "Inferno Tower":     [(1,1500),(2,1700),(3,1900),(4,2100),(5,2300),(6,2500),(7,2700),(8,2900),(9,3100),(10,3300),(11,3500),(12,3700)],
    "X-Bow":             [(1,1500),(2,1700),(3,1900),(4,2100),(5,2300),(6,2500),(7,2700),(8,2900),(9,3100),(10,3300),(11,3500),(12,3700),(13,3900)],
    "Scattershot":       [(1,4000),(2,4500),(3,5000),(4,5500),(5,6000),(6,6500),(7,7000)],
    "Monolith":          [(1,5000),(2,5500),(3,6000),(4,6500)],
    "Wizard Tower":      [(1,620),(2,680),(3,730),(4,840),(5,960),(6,1080),(7,1200),(8,1380),(9,1560),(10,1740),(11,1920),(12,2100),(13,2280),(14,2460),(15,2640),(16,2820),(17,3000)],
    "Mortar":            [(1,400),(2,450),(3,500),(4,550),(5,600),(6,650),(7,700),(8,800),(9,900),(10,1000),(11,1100),(12,1200),(13,1300),(14,1400),(15,1500),(16,1600),(17,1700),(18,1800)],
    "Air Defense":       [(1,800),(2,850),(3,900),(4,950),(5,1000),(6,1100),(7,1200),(8,1300),(9,1400),(10,1500),(11,1600),(12,1700),(13,1800),(14,1900),(15,2000),(16,2100)],
    "Archer Tower":      [(1,380),(2,420),(3,460),(4,500),(5,540),(6,580),(7,620),(8,660),(9,700),(10,740),(11,780),(12,820),(13,900),(14,1000),(15,1100),(16,1200),(17,1300),(18,1400),(19,1500),(20,1600),(21,1700)],
    "Cannon":            [(1,400),(2,450),(3,500),(4,550),(5,600),(6,700),(7,800),(8,900),(9,1000),(10,1100),(11,1200),(12,1300),(13,1400),(14,1500),(15,1600),(16,1700),(17,1800),(18,1900),(19,2000),(20,2100),(21,2200)],
    "Bomb Tower":        [(1,650),(2,700),(3,800),(4,900),(5,1000),(6,1100),(7,1200),(8,1300),(9,1400),(10,1500),(11,1600),(12,1700),(13,1800)],
    "Air Sweeper":       [(1,250),(2,300),(3,350),(4,400),(5,450),(6,500),(7,550)],
    "Spell Tower":       [(1,1200),(2,1400),(3,1600),(4,1800)],
    "Firespitter":       [(1,3000),(2,3500),(3,4000)],
    "Ricochet Cannon":   [(1,3000),(2,3500),(3,4000),(4,4500)],
    "Multi Archer Tower":[(1,2500),(2,3000),(3,3500),(4,4000)],
    "Revenge Tower":     [(1,3500),(2,4000)],
    "Super Wizard Tower":[(1,3000),(2,3500)],
    "Multi Gear Tower":  [(1,2000),(2,2500),(3,3000)],
    "Lava Launcher":     [(1,3000),(2,3500),(3,4000)],
}
 
def calc_total_dmg(lightning_lvl, lightning_count, eq_lvl, eq_count, equipment_selections):
    """Returns total damage dealt by spell combo + equipment."""
    l_dmg = LIGHTNING_DMG.get(lightning_lvl, 600) * lightning_count
 
    # EQ damage is applied to remaining HP, so it's percentage-based
    # We return eq_pct info separately for display
    eq_pct_first = earthquake_pct(eq_lvl) if eq_count >= 1 else 0
    eq_pct_sub = subsequent_eq_pct(eq_lvl) * (eq_count - 1) if eq_count > 1 else 0
 
    eq_dmg_fn = lambda hp_remaining: hp_remaining * (eq_pct_first + eq_pct_sub)
 
    equip_dmg = sum(get_equipment_dmg(k, lvl) for k, lvl in equipment_selections.items())
 
    return l_dmg, eq_dmg_fn, equip_dmg
 
def can_destroy(hp, lightning_lvl, lightning_count, eq_lvl, eq_count, equipment_selections):
    """Returns True if the combo destroys a defense with given hp."""
    equip_dmg = sum(get_equipment_dmg(k, lvl) for k, lvl in equipment_selections.items())
    l_dmg = LIGHTNING_DMG.get(lightning_lvl, 600) * lightning_count
    
    remaining = hp - l_dmg - equip_dmg
    if remaining <= 0:
        return True
    
    if eq_count >= 1:
        remaining -= remaining * earthquake_pct(eq_lvl)
    for _ in range(eq_count - 1):
        remaining -= remaining * subsequent_eq_pct(eq_lvl)
    
    return remaining <= 0
 
# ─────────────────────────────────────────────
#  Per-user state
# ─────────────────────────────────────────────
 
class UserState:
    def __init__(self):
        self.lightning_lvl = 13
        self.lightning_count = 5
        self.eq_lvl = 8
        self.eq_count = 1
        self.equipment: dict[str, int] = {}  # key -> level
        self.def_level_overrides: dict[str, int] = {}  # defense name -> index into levels list
        self.battle_modifier = "Normal"  # Normal / CWL / Friendly
 
    def spell_slots_used(self):
        return self.lightning_count + self.eq_count
 
    def get_eq_label(self):
        return f"+{self.eq_count}x EQ lv{self.eq_lvl}" if self.eq_count > 0 else "Inga EQ"
 
# ─────────────────────────────────────────────
#  Persistent per-user store (in-memory, per session)
#  For persistence across restarts, use a JSON file or DB
# ─────────────────────────────────────────────
 
_user_states: dict[int, UserState] = {}
 
def get_state(user_id: int) -> UserState:
    if user_id not in _user_states:
        _user_states[user_id] = UserState()
    return _user_states[user_id]
 
# ─────────────────────────────────────────────
#  Build the embed + view
# ─────────────────────────────────────────────
 
def build_results_text(state: UserState) -> str:
    lines = []
    modifier = state.battle_modifier
    modifier_mult = 1.0 if modifier == "Normal" else (0.85 if modifier == "CWL" else 0.6)
 
    for defense_name, level_list in DEFENSES.items():
        # Which level to use for this defense
        idx = state.def_level_overrides.get(defense_name, len(level_list) - 1)
        idx = max(0, min(idx, len(level_list) - 1))
        lvl_label, base_hp = level_list[idx]
        hp = int(base_hp * modifier_mult)
 
        destroyed = can_destroy(
            hp,
            state.lightning_lvl,
            state.lightning_count,
            state.eq_lvl,
            state.eq_count,
            state.equipment,
        )
 
        icon = "✅" if destroyed else "❌"
        lines.append(f"{icon} **{defense_name}** lv{lvl_label} ({hp:,} HP)")
 
    return "\n".join(lines)
 
 
def build_combo_summary(state: UserState) -> str:
    parts = [f"⚡ {state.lightning_count}x Lightning lv{state.lightning_lvl}"]
    if state.eq_count > 0:
        parts.append(f"🌍 {state.eq_count}x Earthquake lv{state.eq_lvl}")
    for key, lvl in state.equipment.items():
        emoji = EQUIPMENT_EMOJI.get(key, "🔧")
        label = EQUIPMENT_LABELS.get(key, key)
        parts.append(f"{emoji} {label} lv{lvl}")
    return "  +  ".join(parts)
 
 
def build_embed(state: UserState) -> discord.Embed:
    embed = discord.Embed(
        title="⚡ ZapQuake Kalkylator",
        color=0xFFD700,
    )
    embed.add_field(
        name="🎯 Kombination",
        value=build_combo_summary(state),
        inline=False,
    )
    embed.add_field(
        name=f"🗡️ Resultat [{state.battle_modifier}]",
        value=build_results_text(state) or "Inga resultat",
        inline=False,
    )
    spell_slots = state.spell_slots_used()
    embed.set_footer(text=f"Spell slots använda: {spell_slots} | Justera med knapparna nedan")
    return embed
 
 
# ─────────────────────────────────────────────
#  View with buttons
# ─────────────────────────────────────────────
 
class ZapQuakeView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=600)
        self.user_id = user_id
 
    async def refresh(self, interaction: discord.Interaction):
        state = get_state(self.user_id)
        embed = build_embed(state)
        await interaction.response.edit_message(embed=embed, view=self)
 
    # ── Lightning level ──
    @discord.ui.button(label="⚡ Lightning lv−", style=discord.ButtonStyle.grey, row=0)
    async def lightning_lvl_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.defer()
        s = get_state(self.user_id)
        s.lightning_lvl = max(1, s.lightning_lvl - 1)
        await self.refresh(interaction)
 
    @discord.ui.button(label="⚡ Lightning lv+", style=discord.ButtonStyle.grey, row=0)
    async def lightning_lvl_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.defer()
        s = get_state(self.user_id)
        s.lightning_lvl = min(13, s.lightning_lvl + 1)
        await self.refresh(interaction)
 
    @discord.ui.button(label="⚡ Antal−", style=discord.ButtonStyle.blurple, row=0)
    async def lightning_count_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.defer()
        s = get_state(self.user_id)
        s.lightning_count = max(1, s.lightning_count - 1)
        await self.refresh(interaction)
 
    @discord.ui.button(label="⚡ Antal+", style=discord.ButtonStyle.blurple, row=0)
    async def lightning_count_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.defer()
        s = get_state(self.user_id)
        s.lightning_count = min(18, s.lightning_count + 1)
        await self.refresh(interaction)
 
    # ── Earthquake ──
    @discord.ui.button(label="🌍 EQ lv−", style=discord.ButtonStyle.grey, row=1)
    async def eq_lvl_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.defer()
        s = get_state(self.user_id)
        s.eq_lvl = max(1, s.eq_lvl - 1)
        await self.refresh(interaction)
 
    @discord.ui.button(label="🌍 EQ lv+", style=discord.ButtonStyle.grey, row=1)
    async def eq_lvl_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.defer()
        s = get_state(self.user_id)
        s.eq_lvl = min(8, s.eq_lvl + 1)
        await self.refresh(interaction)
 
    @discord.ui.button(label="🌍 EQ antal−", style=discord.ButtonStyle.blurple, row=1)
    async def eq_count_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.defer()
        s = get_state(self.user_id)
        s.eq_count = max(0, s.eq_count - 1)
        await self.refresh(interaction)
 
    @discord.ui.button(label="🌍 EQ antal+", style=discord.ButtonStyle.blurple, row=1)
    async def eq_count_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.defer()
        s = get_state(self.user_id)
        s.eq_count = min(10, s.eq_count + 1)
        await self.refresh(interaction)
 
    # ── Equipment select ──
    @discord.ui.select(
        placeholder="➕ Lägg till / ta bort Equipment",
        min_values=0,
        max_values=6,
        options=[
            discord.SelectOption(label="Spiky Ball", value="spiky_ball", emoji="⚡"),
            discord.SelectOption(label="Giant Arrow", value="giant_arrow", emoji="🏹"),
            discord.SelectOption(label="Seeking Shield", value="seeking_shield", emoji="🛡️"),
            discord.SelectOption(label="Fireball", value="fireball", emoji="🔥"),
            discord.SelectOption(label="Flame Blower", value="flame_blower", emoji="💨"),
            discord.SelectOption(label="Rocket Backpack", value="rocket_backpack", emoji="🚀"),
        ],
        row=2,
    )
    async def equipment_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.user_id:
            return await interaction.response.defer()
        s = get_state(self.user_id)
        # Keep existing levels for already-selected equipment
        new_equip = {}
        for key in select.values:
            new_equip[key] = s.equipment.get(key, EQUIPMENT_MAX[key])
        s.equipment = new_equip
        await self.refresh(interaction)
 
    # ── Equipment level buttons (shown as separate message via modal) ──
    @discord.ui.button(label="🔧 Ändra Equipment-nivåer", style=discord.ButtonStyle.green, row=3)
    async def equipment_levels(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.defer()
        s = get_state(self.user_id)
        if not s.equipment:
            await interaction.response.send_message("Du har inga equipment valda ännu!", ephemeral=True)
            return
        modal = EquipmentLevelModal(self.user_id, s.equipment.copy())
        await interaction.response.send_modal(modal)
 
    # ── Battle modifier ──
    @discord.ui.select(
        placeholder="⚔️ Battle Modifier",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="Normal", value="Normal", emoji="⚔️"),
            discord.SelectOption(label="CWL (−15% HP)", value="CWL", emoji="🏆"),
            discord.SelectOption(label="Friendly (−40% HP)", value="Friendly", emoji="🤝"),
        ],
        row=4,
    )
    async def battle_modifier(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.user_id:
            return await interaction.response.defer()
        s = get_state(self.user_id)
        s.battle_modifier = select.values[0]
        await self.refresh(interaction)
 
 
# ─────────────────────────────────────────────
#  Modal for equipment levels
# ─────────────────────────────────────────────
 
class EquipmentLevelModal(discord.ui.Modal, title="Ändra Equipment-nivåer"):
    def __init__(self, user_id: int, current_equipment: dict):
        super().__init__()
        self.user_id = user_id
        self.keys = list(current_equipment.keys())
 
        for key in self.keys[:5]:  # Discord modal max 5 fields
            label = EQUIPMENT_LABELS.get(key, key)
            max_lvl = EQUIPMENT_MAX.get(key, 27)
            current = current_equipment.get(key, max_lvl)
            self.add_item(discord.ui.TextInput(
                label=f"{label} (1–{max_lvl})",
                custom_id=key,
                default=str(current),
                min_length=1,
                max_length=2,
                required=True,
            ))
 
    async def on_submit(self, interaction: discord.Interaction):
        s = get_state(self.user_id)
        for child in self.children:
            key = child.custom_id
            max_lvl = EQUIPMENT_MAX.get(key, 27)
            try:
                lvl = int(child.value)
                lvl = max(1, min(max_lvl, lvl))
                s.equipment[key] = lvl
            except ValueError:
                pass
 
        embed = build_embed(s)
        view = ZapQuakeView(self.user_id)
        await interaction.response.edit_message(embed=embed, view=view)
 
 
# ─────────────────────────────────────────────
#  Cog
# ─────────────────────────────────────────────
 
class ZapQuakeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
 
    @app_commands.command(name="zapquake", description="Öppna ZapQuake-kalkylatorn (privat)")
    async def zapquake(self, interaction: discord.Interaction):
        state = get_state(interaction.user.id)
        embed = build_embed(state)
        view = ZapQuakeView(interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
 
 
async def setup(bot: commands.Bot):
    await bot.add_cog(ZapQuakeCog(bot))
