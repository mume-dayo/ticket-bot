import os
import discord
from discord.ext import commands
from flask import Flask
from discord import app_commands
import threading
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

class TicketModal(discord.ui.Modal, title="チケット項目を追加"):
    def __init__(self, normal_category: str, priority_category: str, is_priority: bool = False):
        super().__init__()
        self.normal_category = normal_category
        self.priority_category = priority_category
        self.is_priority = is_priority

    title_input = discord.ui.TextInput(label="Label", placeholder="チケットのタイトルを入力してください", required=True)
    desc_input = discord.ui.TextInput(label="Description", placeholder="詳細な説明を入力してください", required=False, style=discord.TextStyle.paragraph, max_length=1000)
    emoji_input = discord.ui.TextInput(label="Emoji", placeholder="絵文字を入力してください（任意）", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user

        category_name = self.priority_category if self.is_priority else self.normal_category

        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(category_name)

        support_role = discord.utils.get(guild.roles, name="サポート")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        emoji = self.emoji_input.value.strip() if self.emoji_input.value else "🎫"
        label = self.title_input.value.strip().replace(" ", "-").lower()
        channel_name = f"{emoji}-{label}-{user.name}".lower()

        channel = await guild.create_text_channel(channel_name[:100], category=category, overwrites=overwrites)

        embed = discord.Embed(
            title=f"{emoji} {self.title_input.value}",
            description=self.desc_input.value or "(説明なし)",
            color=discord.Color.gold() if self.is_priority else discord.Color.blue()
        )
        embed.set_footer(text=f"作成者: {user.name}", icon_url=user.display_avatar.url)
        await channel.send(content=f"{user.mention} さんがチケットを作成しました。", embed=embed)

        await interaction.response.send_message(f"{channel.mention} にチケットを作成しました！", ephemeral=True)

class TicketButtonView(discord.ui.View):
    def __init__(self, normal_category: str, priority_category: str):
        super().__init__(timeout=None)
        self.normal_category = normal_category
        self.priority_category = priority_category

    @discord.ui.button(label="🎫 通常チケットを作成", style=discord.ButtonStyle.primary, custom_id="open_normal_ticket_modal")
    async def normal_ticket_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = TicketModal(self.normal_category, self.priority_category, is_priority=False)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="⚠️ 優先チケットを作成", style=discord.ButtonStyle.danger, custom_id="open_priority_ticket_modal")
    async def priority_ticket_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = TicketModal(self.normal_category, self.priority_category, is_priority=True)
        await interaction.response.send_modal(modal)

@bot.tree.command(name="ticket", description="チケットボタンを表示します")
@app_commands.describe(
    normal="通常チケット用カテゴリ名",
    priority="優先チケット用カテゴリ名",
    description="チケット作成ボタン上の案内文（任意）"
)
async def ticket(
    interaction: discord.Interaction,
    normal: str,
    priority: str,
    description: str = "以下のボタンからチケットを作成してください："
):
    view = TicketButtonView(normal_category=normal, priority_category=priority)
    await interaction.response.send_message(description, view=view, ephemeral=False)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"{bot.user} が起動しました。")

app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_flask).start()
bot.run(TOKEN)
