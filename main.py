import os
import subprocess
import time
import discord
from discord.ext import commands
from discord import app_commands

# ==================== 設定エリア ====================
# Discord Botのトークン（環境変数または直接入力）
BOT_TOKEN = os.getenv("DISCORD_TOKEN", "ここにYOUR_DISCORD_TOKENを入れることも可")

# マイクラサーバーの設定
SERVER_DIR = "C:/path/to/peparserver"    # サーバーのフォルダパス
START_CMD = "start.cmd"                  # 起動バッチファイル名
# ====================================================

server_process = None

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

# UI Embed作成関数
def create_control_embed(status_text="❓ 未確認"):
    embed = discord.Embed(
        title="🎮 Minecraft Paper サーバー管理パネル",
        description="下のボタンを押してマイクラサーバーを直接操作できます。",
        color=discord.Color.blue()
    )
    embed.add_field(name="📡 サーバー状態", value=status_text, inline=False)
    embed.set_footer(text="Paper Server Direct Control")
    return embed

# コマンド送信入力フォーム (Modal)
class CommandModal(discord.ui.Modal, title="⚡ Minecraft コマンド実行"):
    command_input = discord.ui.TextInput(
        label="コマンド入力 (スラッシュ不要)",
        placeholder="例: say こんにちは / op username / time set day",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        global server_process
        await interaction.response.defer(ephemeral=True)

        if not server_process or server_process.poll() is not None:
            await interaction.followup.send("❌ サーバーが起動していません。", ephemeral=True)
            return

        try:
            cmd = self.command_input.value.strip()
            if cmd.startswith("/"):
                cmd = cmd[1:]
            
            server_process.stdin.write(f"{cmd}\n")
            server_process.stdin.flush()
            await interaction.followup.send(f"**実行:** `{cmd}`", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ エラー: {e}", ephemeral=True)

# 操作パネルボタン View
class ServerControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🚀 起動", style=discord.ButtonStyle.green, custom_id="btn_start")
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        global server_process
        await interaction.response.defer(ephemeral=True)

        if server_process and server_process.poll() is None:
            await interaction.followup.send("⚠️ サーバーは既に起動しています。", ephemeral=True)
            return

        try:
            server_process = subprocess.Popen(
                START_CMD,
                cwd=SERVER_DIR,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            await interaction.followup.send("🟢 サーバーの起動処理を開始しました。", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ 起動エラー: {e}", ephemeral=True)

    @discord.ui.button(label="🛑 停止", style=discord.ButtonStyle.red, custom_id="btn_stop")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        global server_process
        await interaction.response.defer(ephemeral=True)

        if not server_process or server_process.poll() is not None:
            await interaction.followup.send("⚠️ サーバーは起動していません。", ephemeral=True)
            return

        try:
            server_process.stdin.write("stop\n")
            server_process.stdin.flush()
            server_process = None
            await interaction.followup.send("🔴 `stop` を送信しました。安全にシャットダウンします。", ephemeral=True)
        except Exception as e:
            server_process.terminate()
            server_process = None
            await interaction.followup.send(f"⚠️ 強制停止しました: {e}", ephemeral=True)

    @discord.ui.button(label="🔄 再起動", style=discord.ButtonStyle.primary, custom_id="btn_restart")
    async def restart_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        global server_process
        await interaction.response.defer(ephemeral=True)

        if server_process and server_process.poll() is None:
            try:
                server_process.stdin.write("stop\n")
                server_process.stdin.flush()
            except:
                server_process.terminate()
            time.sleep(8)

        try:
            server_process = subprocess.Popen(
                START_CMD,
                cwd=SERVER_DIR,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            await interaction.followup.send("🔄 サーバーの再起動処理を実行しました。", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ 再起動エラー: {e}", ephemeral=True)

    @discord.ui.button(label="📊 状態更新", style=discord.ButtonStyle.secondary, custom_id="btn_status")
    async def status_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        global server_process
        await interaction.response.defer(ephemeral=True)

        is_running = server_process is not None and server_process.poll() is None
        status_str = "🟢 起動中 (Online)" if is_running else "🔴 停止中 (Offline)"

        new_embed = create_control_embed(status_str)
        await interaction.message.edit(embed=new_embed)
        await interaction.followup.send("最新状態に更新しました！", ephemeral=True)

    @discord.ui.button(label="⚡ コマンド送信", style=discord.ButtonStyle.secondary, custom_id="btn_cmd")
    async def cmd_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CommandModal())

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user.name}")

@bot.tree.command(name="setup-panel", description="マイクラサーバー管理パネルを設置します")
@app_commands.default_permissions(administrator=True)
async def setup_panel(interaction: discord.Interaction):
    embed = create_control_embed("❓ 未確認 (「状態更新」を押してください)")
    await interaction.channel.send(embed=embed, view=ServerControlView())
    await interaction.response.send_message("管理パネルを設置しました！", ephemeral=True)

bot.run(BOT_TOKEN)
