import os, re, socket, json
import discord
from discord.ext import commands
from discord import app_commands
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

# --- SISTEMA PERMESSI ---
PERM_FILE = "permessi.json"

def carica_permessi():
    if not os.path.exists(PERM_FILE):
        return {}
    try:
        with open(PERM_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def salva_permessi(data):
    with open(PERM_FILE, "w") as f:
        json.dump(data, f, indent=4)

def ha_permesso(user_id, tipo_richiesto):
    permessi = carica_permessi()
    uid = str(user_id)
    if uid not in permessi:
        return False
    # se ha 'all' può tutto
    if "all" in permessi[uid] or "infinito" in permessi[uid]:
        return True
    return tipo_richiesto in permessi[uid]

def is_admin(interaction):
    return interaction.user.guild_permissions.administrator

@bot.event
async def on_ready():
    print(f"Online come {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="/help | OSINT Legale"))
    await bot.tree.sync()

# --- COMANDO /permesso ---

@bot.tree.command(name="permesso", description="Gestisci permessi utente (Solo Admin)")
@app_commands.describe(
    azione="aggiungi o rimuovi",
    user="Utente a cui dare/togliere permesso",
    tipo="Tipo: social, email, ip, all"
)
@app_commands.choices(
    azione=[
        app_commands.Choice(name="aggiungi", value="aggiungi"),
        app_commands.Choice(name="rimuovi", value="rimuovi"),
    ],
    tipo=[
        app_commands.Choice(name="social - /osint /usersearch /dominio", value="social"),
        app_commands.Choice(name="email - /emailcheck", value="email"),
        app_commands.Choice(name="ip - /ip", value="ip"),
        app_commands.Choice(name="all - Tutto illimitato", value="all"),
    ]
)
async def permesso(interaction: discord.Interaction, azione: str, user: discord.Member, tipo: str):
    if not is_admin(interaction):
        await interaction.response.send_message("Solo admin.", ephemeral=True)
        return

    permessi = carica_permessi()
    uid = str(user.id)

    if uid not in permessi:
        permessi[uid] = []

    if azione == "aggiungi":
        if tipo not in permessi[uid]:
            permessi[uid].append(tipo)
        salva_permessi(permessi)
        await interaction.response.send_message(f"✅ Aggiunto permesso `{tipo}` a {user.mention}", ephemeral=True)
    else: # rimuovi
        if tipo in permessi[uid]:
            permessi[uid].remove(tipo)
        salva_permessi(permessi)
        await interaction.response.send_message(f"❌ Rimosso permesso `{tipo}` da {user.mention}", ephemeral=True)

# --- COMANDI OSINT CON CONTROLLO PERMESSI ---

@bot.tree.command(name="help", description="Lista comandi MaxIntel")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="MaxIntel V2 - Comandi", color=0x00ff00)
    embed.add_field(name="/osint <username> [social]", value="Cerca username pubblico", inline=False)
    embed.add_field(name="/usersearch <nome> [social]", value="Genera varianti", inline=False)
    embed.add_field(name="/dominio <dominio> [social]", value="Link WHOIS / DNS", inline=False)
    embed.add_field(name="/ip <ip> [ip]", value="Info su IP pubblico", inline=False)
    embed.add_field(name="/emailcheck <email> [email]", value="Controlla formato email", inline=False)
    embed.add_field(name="/permesso [ADMIN]", value="/permesso aggiungi @user social/email/ip/all", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="osint", description="Cerca username pubblico sui social")
async def osint(interaction: discord.Interaction, username: str):
    if not ha_permesso(interaction.user.id, "social") and not is_admin(interaction):
        await interaction.response.send_message("Non hai il permesso `social`. Chiedi a un admin: /permesso", ephemeral=True)
        return
    username = username.replace("@","").strip()
    embed = discord.Embed(title=f"Username: {username}", description="Profili pubblici", color=0x3498db)
    links = {
        "Instagram": f"https://instagram.com/{username}",
        "TikTok": f"https://tiktok.com/@{username}",
        "YouTube": f"https://youtube.com/@{username}",
        "GitHub": f"https://github.com/{username}",
        "X": f"https://x.com/{username}",
    }
    for k,v in links.items():
        embed.add_field(name=k, value=f"[Apri]({v})", inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="usersearch", description="Genera varianti simili di uno username")
async def usersearch(interaction: discord.Interaction, nome: str):
    if not ha_permesso(interaction.user.id, "social") and not is_admin(interaction):
        await interaction.response.send_message("Non hai il permesso `social`.", ephemeral=True)
        return
    base = nome.lower().replace(" ", "")
    varianti = [base, f"{base}_", f"{base}01", f"the{base}", f"{base}_official"]
    testo = "\n".join([f"`{v}` -> [IG](https://instagram.com/{v})" for v in varianti])
    embed = discord.Embed(title=f"Varianti per: {nome}", description=testo, color=0x9b59b6)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="dominio", description="Info pubbliche dominio")
async def dominio(interaction: discord.Interaction, dominio: str):
    if not ha_permesso(interaction.user.id, "social") and not is_admin(interaction):
        await interaction.response.send_message("Non hai il permesso `social`.", ephemeral=True)
        return
    try:
        ip = socket.gethostbyname(dominio)
        embed = discord.Embed(title=f"Dominio: {dominio}", color=0x3498db)
        embed.add_field(name="IP Server", value=ip)
        embed.add_field(name="WHOIS", value=f"https://who.is/whois/{dominio}")
        await interaction.response.send_message(embed=embed)
    except:
        await interaction.response.send_message("Dominio non valido.")

@bot.tree.command(name="ip", description="Info IP pubblico di server")
async def ipcheck(interaction: discord.Interaction, ip: str):
    if not ha_permesso(interaction.user.id, "ip") and not is_admin(interaction):
        await interaction.response.send_message("Non hai il permesso `ip`. Serve pacchetto ULTRA 10€.", ephemeral=True)
        return
    await interaction.response.defer()
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}?fields=query,country,city,isp", timeout=10).json()
        embed = discord.Embed(title=f"IP: {r['query']}", color=0xe67e22)
        embed.add_field(name="Paese/Città", value=f"{r.get('country')} - {r.get('city')}")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"Errore: {e}")

@bot.tree.command(name="emailcheck", description="Verifica formato email")
async def emailcheck(interaction: discord.Interaction, email: str):
    if not ha_permesso(interaction.user.id, "email") and not is_admin(interaction):
        await interaction.response.send_message("Non hai il permesso `email`. Serve pacchetto ULTRA.", ephemeral=True)
        return
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    valido = bool(re.match(pattern, email))
    await interaction.response.send_message(f"Email `{email}` -> {'VALIDO' if valido else 'NON valido'}")

bot.run(TOKEN)
