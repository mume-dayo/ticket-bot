import os
import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask
import threading
from dotenv import load_dotenv


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")


intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

TICKET_CATEGORY_NAME = "チケット"
SUPPORT_ROLE_NAME = "サポート"
class TicketModal(discord.ui.Modal, title="チケット項目を追加"):
    title_input = discord.ui.TextInput(label="Label", placeholder="チケットのタイトルを入力してください", required=True)
    desc_input = discord.ui.TextInput(label="Description", placeholder="詳細な説明を入力してください", required=False, style=discord.TextStyle.paragraph, max_length=1000)
    emoji_input = discord.ui.TextInput(label="Emoji", placeholder="絵文字を入力してください（任意）", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user
        category = discord.utils.get(guild.categories, name=TICKET_CATEGORY_NAME)
        if not category:
            category = await guild.create_category(TICKET_CATEGORY_NAME)

        support_role = discord.utils.get(guild.roles, name=SUPPORT_ROLE_NAME)
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
        embed = discord.Embed(title=f"📝 {self.title_input.value}", description=self.desc_input.value or "(説明なし)", color=discord.Color.blue())
        embed.set_footer(text=f"作成者: {user.name}", icon_url=user.display_avatar.url)
        await channel.send(content=f"{user.mention} さんがチケットを作成しました。", embed=embed)

        await interaction.response.send_message(f"{channel.mention} にチケットを作成しました！", ephemeral=True)

class TicketButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 チケットを作成", style=discord.ButtonStyle.primary, custom_id="open_ticket_modal")
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketModal())

@bot.tree.command(name="ticket", description="チケット作成ボタンを表示します")
async def ticket(interaction: discord.Interaction):
    view = TicketButtonView()
    await interaction.response.send_message("チケットを作成するには以下のボタンを押してください：", view=view, ephemeral=True)

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
