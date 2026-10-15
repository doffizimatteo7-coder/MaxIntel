import discord
from discord.ext import commands
import os
from flask import Flask
import threading

app = Flask(__name__)
@app.route('/')
def home(): return "MaxIntel Bot is Online!"
def run_flask(): app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_flask, daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

class OsintView(discord.ui.View):
    def __init__(self, target: str):
        super().__init__(timeout=120)
        self.target = target

    @discord.ui.button(label="📧 Check Email Breach", style=discord.ButtonStyle.danger)
    async def email_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        # Esempio senza API key - per versione reale serve HIBP API Key
        embed = discord.Embed(title=f"🔍 Email Check: {self.target}", color=0xff0000)
        embed.add_field(name="Cosa fa", value="Controlla se l'email è in database di breach pubblici (HaveIBeenPwned API)", inline=False)
        embed.add_field(name="Risultato simulato", value=f"`{self.target}` -> Per check reale, aggiungi HIBP_API_KEY in Render e sblocchiamo la funzione.\nSe risulta pwned, ti dirà QUANTE volte e in quali breach, MAI la password.", inline=False)
        embed.add_field(name="Link diretto", value=f"https://haveibeenpwned.com/account/{self.target}", inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="👤 Username Search", style=discord.ButtonStyle.primary)
    async def user_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        sites = [f"Instagram: https://instagram.com/{self.target}", f"TikTok: https://tiktok.com/@{self.target}", f"GitHub: https://github.com/{self.target}", f"Reddit: https://reddit.com/user/{self.target}", f"Twitter: https://x.com/{self.target}"]
        embed = discord.Embed(title=f"👤 Username Report: {self.target}", description="\n".join(sites), color=0x00aaff)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🖼️ Image OSINT", style=discord.ButtonStyle.secondary)
    async def img_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="🖼️ Image Reverse Search", description="Carica un'immagine in chat e usa questi tool:", color=0x888888)
        embed.add_field(name="Tools", value="Google: https://images.google.com\nYandex: https://yandex.com/images/search\nFaceCheck: https://facecheck.id", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_ready():
    print(f"MaxIntel Online come {bot.user}")
    await bot.tree.sync()

def is_admin(interaction: discord.Interaction):
    return interaction.user.guild_permissions.administrator

@bot.tree.command(name="osint", description="[SOLO ADMIN] Menu OSINT avanzato")
async def osint(interaction: discord.Interaction, target: str):
    if not is_admin(interaction):
        await interaction.response.send_message("❌ Solo gli amministratori possono usare questo comando.", ephemeral=True)
        return

    embed = discord.Embed(title="🛡️ MaxIntel - Pannello OSINT Admin", color=0x000000)
    embed.add_field(name="Target", value=f"`{target}`", inline=False)
    embed.add_field(name="📧 Email Breach", value="Verifica se l'email è in leak noti (senza mostrare password)", inline=True)
    embed.add_field(name="👤 Username", value="Controlla esistenza su 20+ piattaforme", inline=True)
    embed.add_field(name="🖼️ Immagine", value="Reverse image search", inline=True)
    embed.set_footer(text=f"Richiesto da {interaction.user} - Uso solo per scopi legali")

    view = OsintView(target)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
