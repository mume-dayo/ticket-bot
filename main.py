import os
import discord
from discord.ext import commands
from flask import Flask
import threading
from dotenv import load_dotenv
import asyncio

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

TICKET_CATEGORY_NAME = "チケット"
SUPPORT_ROLE_NAME = "サポート"

@bot.event
async def on_ready():
    print(f'{bot.user} がログインしました！')
    try:
        synced = await bot.tree.sync()
        print(f'{len(synced)} 個のスラッシュコマンドを同期しました')
    except Exception as e:
        print(f'コマンドの同期に失敗しました: {e}')

class TicketCreateView(discord.ui.View):
    def __init__(self, category_name=None):
        super().__init__(timeout=None)
        self.category_name = category_name or TICKET_CATEGORY_NAME

    @discord.ui.button(label='🎫 チケットを作成', style=discord.ButtonStyle.primary, custom_id='create_ticket')
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user

        category = discord.utils.get(guild.categories, name=self.category_name)
        if not category:
            category = await guild.create_category(self.category_name)

        channel_name = f"ticket-{user.name}".replace(" ", "-").lower()
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        support_role = discord.utils.get(guild.roles, name=SUPPORT_ROLE_NAME)
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
        await interaction.response.send_message(f"{channel.mention} にチケットを作成しました！", ephemeral=True)

@bot.tree.command(name="ticket", description="チケット作成ボタンを送信します")
async def ticket(interaction: discord.Interaction):
    view = TicketCreateView()
    await interaction.response.send_message("チケットを作成するには以下のボタンを押してください：", view=view)

app = Flask(__name__)

@app.route('/')
def home():
    return "Discord bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

threading.Thread(target=run_flask).start()

bot.run(TOKEN)
