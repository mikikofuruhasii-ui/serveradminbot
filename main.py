import os
import requests
import discord
from discord.ext import commands
from discord import app_commands

# ==================== 設定エリア ====================
# Render.com の環境変数からは DISCORD_TOKEN のみを取得
BOT_TOKEN = os.getenv("DISCORD_TOKEN")

# コード内に直接記述する設定値
API_URL = "http://cynthia-kz.tun.ply.gg:25565"  # playit.ggで公開したFastAPIのURL
API_KEY = "0827"                # api.py で設定した認証用キー
SERVER_IP = "cynthia-kz.tun.ply.gg"            # UIパネルに表示するサーバーIP
# ====================================================

HEADERS = {"Authorization": f"Bearer {API_KEY}"}

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# UI Embed作成関数（PORTの項目は削除済み）
def create_control_embed(status_text="❓ 未確認"):
    embed = discord.Embed(
        title="🎮 Minecraft Paper サーバー管理パネル",
        description="下のボタンを押してマイクラサーバーを操作できます。",
        color=discord.Color.blue()
    )
    embed.add_field(name="🌐 サーバーIP", value=f"`{SERVER_IP}`", inline=False)
    embed.add_field(name="📡 サーバー状態", value=status_text, inline=False)
    embed.set_footer(text="Paper Server Management System")
    return embed

# コマンド送信入力フォーム (Modal)
class CommandModal(discord.ui.Modal, title="⚡ Minecraft コマンド実行"):
    command_input = discord.ui.TextInput(
        label="コマンド入力 (スラッシュ不要)",
        placeholder="例: say こんにちは / op username / time set day",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            res = requests.post(
                f"{API_URL}/command",
                json={"command": self.command_input.value},
                headers=HEADERS,
                timeout=8
            )
            data = res.json()
            if res.status_code == 200:
                await interaction.followup.send(f"**実行:** `{self.command_input.value}`\n```{data.get('result')}```", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ エラー: {data.get('detail')}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ 通信エラー: {e}", ephemeral=True)

# 操作パネルボタン View
class ServerControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🚀 起動", style=discord.ButtonStyle.green, custom_id="btn_start")
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        try:
            res = requests.post(f"{API_URL}/start", headers=HEADERS, timeout=8)
            await interaction.followup.send(res.json().get("message", "完了"), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ 通信エラー: {e}", ephemeral=True)

    @discord.ui.button(label="🛑 停止", style=discord.ButtonStyle.red, custom_id="btn_stop")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        try:
            res = requests.post(f"{API_URL}/stop", headers=HEADERS, timeout=8)
            await interaction.followup.send(res.json().get("message", "完了"), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ 通信エラー: {e}", ephemeral=True)

    @discord.ui.button(label="🔄 再起動", style=discord.ButtonStyle.primary, custom_id="btn_restart")
    async def restart_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        try:
            res = requests.post(f"{API_URL}/restart", headers=HEADERS, timeout=8)
            await interaction.followup.send(res.json().get("message", "完了"), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ 通信エラー: {e}", ephemeral=True)

    @discord.ui.button(label="📊 状態更新", style=discord.ButtonStyle.secondary, custom_id="btn_status")
    async def status_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        try:
            res = requests.get(f"{API_URL}/status", headers=HEADERS, timeout=5)
            data = res.json()
            status_str = "🟢 起動中 (Online)" if data.get("status") == "online" else "🔴 停止中 (Offline)"
            
            new_embed = create_control_embed(status_str)
            await interaction.message.edit(embed=new_embed)
            await interaction.followup.send("画面の表示を最新情報に更新しました！", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ API通信エラー: {e}", ephemeral=True)

    @discord.ui.button(label="⚡ コマンド送信", style=discord.ButtonStyle.secondary, custom_id="btn_cmd")
    async def cmd_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CommandModal())

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user.name}")

@bot.tree.command(name="setup-panel", description="マイクラサーバー管理パネルをチャンネルに設置します")
@app_commands.default_permissions(administrator=True)
async def setup_panel(interaction: discord.Interaction):
    embed = create_control_embed("❓ 未確認 (「状態更新」を押してください)")
    await interaction.channel.send(embed=embed, view=ServerControlView())
    await interaction.response.send_message("管理パネルを設置しました！", ephemeral=True)

bot.run(BOT_TOKEN)
