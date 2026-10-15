import os, re, socket
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import requests

# --- FIX RENDER WEB SERVICE ONLINE ---
app = Flask('')
@app.route('/')
def home():
    return "MaxIntel V2 Online - Legal OSINT"
def run_flask():
  app.run(host='0.0.0.0', port=8080)
Thread(target=run_flask).start()
# --- FINE FIX ---

TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

def is_admin(interaction):
    return interaction.user.guild_permissions.administrator

@bot.event
async def on_ready():
    print(f"Online come {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="/help | OSINT Legale"))
    await bot.tree.sync()

@bot.tree.command(name="help", description="Lista comandi MaxIntel")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="MaxIntel V2 - Comandi", color=0x00ff00)
    embed.add_field(name="/osint <username>", value="Cerca username pubblico su IG, TikTok, YouTube, GitHub ecc", inline=False)
    embed.add_field(name="/usersearch <nome>", value="Genera varianti simili di username per cercare sui social", inline=False)
    embed.add_field(name="/dominio <dominio>", value="Link WHOIS / DNS pubblici", inline=False)
    embed.add_field(name="/ip <ip>", value="Info su IP PUBBLICO di un server/sito (non di persone)", inline=False)
    embed.add_field(name="/emailcheck <email>", value="Controlla se formato email è valido (non cerca persone)", inline=False)
    embed.add_field(name="/ping", value="Stato bot", inline=False)
    embed.set_footer(text="Solo admin possono usare i comandi. Uso solo legale.")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ping", description="Stato bot")
async def ping(interaction: discord.Interaction):
    if not is_admin(interaction):
        await interaction.response.send_message("Solo admin.", ephemeral=True)
        return
    await interaction.response.send_message(f"Online! {round(bot.latency*1000)}ms")

@bot.tree.command(name="osint", description="Cerca username pubblico sui social")
async def osint(interaction: discord.Interaction, username: str):
    if not is_admin(interaction):
        await interaction.response.send_message("Devi avere il permesso Amministratore per usare questo comando.", ephemeral=True)
        return
    username = username.replace("@","").strip()
    embed = discord.Embed(title=f"Username: {username}", description="Profili pubblici - clicca e verifica manualmente", color=0x3498db)
    links = {
        "Instagram": f"https://instagram.com/{username}",
        "TikTok": f"https://tiktok.com/@{username}",
        "YouTube": f"https://youtube.com/@{username}",
        "GitHub": f"https://github.com/{username}",
        "X": f"https://x.com/{username}",
        "Twitch": f"https://twitch.tv/{username}",
        "Reddit": f"https://reddit.com/user/{username}"
    }
    for k,v in links.items():
        embed.add_field(name=k, value=f"[Apri]({v})", inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="usersearch", description="Genera varianti simili di uno username")
async def usersearch(interaction: discord.Interaction, nome: str):
    if not is_admin(interaction):
        await interaction.response.send_message("Solo admin.", ephemeral=True)
        return
    base = nome.lower().replace(" ", "")
    varianti = [base, f"{base}_", f"{base}.", f"{base}01", f"the{base}", f"{base}_official", f"{base}.real"]
    testo = "\n".join([f"`{v}` -> [IG](https://instagram.com/{v}) | [TikTok](https://tiktok.com/@{v})" for v in varianti[:7]])
    embed = discord.Embed(title=f"Varianti per: {nome}", description=testo, color=0x9b59b6)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="dominio", description="Info pubbliche dominio")
async def dominio(interaction: discord.Interaction, dominio: str):
    if not is_admin(interaction):
        await interaction.response.send_message("Solo admin.", ephemeral=True)
        return
    try:
        ip = socket.gethostbyname(dominio)
        embed = discord.Embed(title=f"Dominio: {dominio}", color=0x3498db)
        embed.add_field(name="IP Server", value=ip, inline=False)
        embed.add_field(name="WHOIS", value=f"https://who.is/whois/{dominio}", inline=False)
        embed.add_field(name="DNS", value=f"https://dnschecker.org/#A/{dominio}", inline=False)
        await interaction.response.send_message(embed=embed)
    except:
        await interaction.response.send_message("Dominio non valido.")

@bot.tree.command(name="ip", description="Info IP pubblico di server")
async def ipcheck(interaction: discord.Interaction, ip: str):
    if not is_admin(interaction):
        await interaction.response.send_message("Solo admin.", ephemeral=True)
        return
    await interaction.response.defer()
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}?fields=query,country,city,isp,org,as", timeout=10).json()
        if r.get('status') == 'fail' or not r.get('query'):
            await interaction.followup.send("IP privato o non valido. Solo IP pubblici di server.")
            return
        embed = discord.Embed(title=f"IP: {r['query']}", color=0xe67e22)
        embed.add_field(name="Paese/Città", value=f"{r.get('country')} - {r.get('city')}", inline=True)
        embed.add_field(name="ISP/Org", value=f"{r.get('isp')}", inline=True)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"Errore: {e}")

@bot.tree.command(name="emailcheck", description="Verifica formato email")
async def emailcheck(interaction: discord.Interaction, email: str):
    if not is_admin(interaction):
        await interaction.response.send_message("Solo admin.", ephemeral=True)
        return
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    valido = bool(re.match(pattern, email))
    if valido:
        await interaction.response.send_message(f"Email `{email}` -> Formato VALIDO (non verifica se esiste una persona).")
    else:
        await interaction.response.send_message(f"Email `{email}` -> Formato NON valido.")

bot.run(TOKEN)
