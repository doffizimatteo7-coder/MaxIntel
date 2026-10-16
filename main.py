import os, json, asyncio, re, socket, hashlib
import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask
from threading import Thread
import requests

app = Flask('')
@app.route('/')
def home(): return "MAXINTEL V2 ONLINE"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080), daemon=True).start()

TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("TOKEN")
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
BLACK = 0x0a0a0a
PERM_FILE="permessi.json"
_lock=asyncio.Lock()

def carica_permessi():
    if not os.path.exists(PERM_FILE): return {}
    try:
        with open(PERM_FILE,"r") as f: return json.load(f)
    except: return {}
def salva_permessi(d):
    with open(PERM_FILE,"w") as f: json.dump(d,f,indent=4)
def ha_permesso(uid,tipo):
    p=carica_permessi(); uid=str(uid)
    if uid not in p: return False
    return "all" in p[uid] or "infinito" in p[uid] or tipo in p[uid]
def is_admin(i): return i.user.guild_permissions.administrator

@bot.event
async def on_ready():
    print(f"V2 ONLINE {bot.user}")
    # SYNC ISTANTANEO PER TUTTI I SERVER
    try:
        for guild in bot.guilds:
            bot.tree.copy_global_to(guild=guild)
            await bot.tree.sync(guild=guild)
            print(f"SYNC ISTANTANEO FATTO PER {guild.name}")
        # anche globale
        await bot.tree.sync()
    except Exception as e:
        print(f"SYNC ERR {e}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="MaxIntel V2 | /help"))

# COMANDO PER FORZARE SYNC A MANO
@bot.tree.command(name="sync", description="[ADMIN] Forza apparizione comandi subito")
async def sync_cmd(interaction: discord.Interaction):
    if not is_admin(interaction):
        await interaction.response.send_message("Solo admin",ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    try:
        bot.tree.copy_global_to(guild=interaction.guild)
        await bot.tree.sync(guild=interaction.guild)
        await interaction.followup.send("✅ Comandi sincronizzati! Ora scrivi `/` e vedrai tutti i comandi MaxIntel V2", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Errore sync: {e}", ephemeral=True)

@bot.tree.command(name="permesso", description="ADMIN - gestisci permessi")
@app_commands.choices(
    azione=[app_commands.Choice(name="aggiungi",value="aggiungi"),app_commands.Choice(name="rimuovi",value="rimuovi")],
    tipo=[app_commands.Choice(name="social",value="social"),app_commands.Choice(name="email",value="email"),app_commands.Choice(name="ip",value="ip"),app_commands.Choice(name="all",value="all")]
)
async def permesso(interaction: discord.Interaction, azione:str, user:discord.Member, tipo:str):
    if not is_admin(interaction):
        await interaction.response.send_message("Solo admin",ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    async with _lock:
        p=carica_permessi(); uid=str(user.id); p.setdefault(uid,[])
        if azione=="aggiungi":
            if tipo not in p[uid]: p[uid].append(tipo)
        else:
            if tipo in p[uid]: p[uid].remove(tipo)
        salva_permessi(p)
        embed=discord.Embed(title=f"Permesso {azione}", description=f"{tipo} -> {user.name}", color=BLACK)
        await interaction.followup.send(embed=embed,ephemeral=True)

@bot.tree.command(name="help", description="Pannello comandi MaxIntel")
async def help_cmd(interaction: discord.Interaction):
    embed=discord.Embed(title="MaxIntel V2 - Comandi", color=BLACK)
    embed.add_field(name="/osint <username> [social]", value="Cerca username pubblico", inline=False)
    embed.add_field(name="/usersearch <nome> [social]", value="Genera varianti", inline=False)
    embed.add_field(name="/similar <username> [social]", value="Cerca varianti simili", inline=False)
    embed.add_field(name="/userdeep <username> [social]", value="Check live se esiste davvero", inline=False)
    embed.add_field(name="/dominio <dominio> [social]", value="Link WHOIS / DNS", inline=False)
    embed.add_field(name="/siteintel <dominio> [ip]", value="Info complete sito - IP + tech", inline=False)
    embed.add_field(name="/dork <dominio> [ip]", value="Genera Google Dork pronti", inline=False)
    embed.add_field(name="/ip <ip> [ip]", value="Info su IP pubblico", inline=False)
    embed.add_field(name="/blacklist <ip> [ip]", value="Check se IP in blacklist", inline=False)
    embed.add_field(name="/emailcheck <email> [email]", value="Controlla formato email", inline=False)
    embed.add_field(name="/leakcheck <dominio> [email]", value="Check leak dominio", inline=False)
    embed.add_field(name="/hash <testo>", value="Genera MD5/SHA", inline=False)
    embed.add_field(name="/bin <bin>", value="Info BIN carta", inline=False)
    embed.add_field(name="/permesso [ADMIN]", value="/permesso aggiungi @user social/email/ip/all", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="osint", description="Cerca username pubblico")
async def osint(interaction: discord.Interaction, username:str):
    if not ha_permesso(interaction.user.id,"social") and not is_admin(interaction):
        await interaction.response.send_message("Serve permesso social",ephemeral=True); return
    username=username.replace("@","")[:25]
    embed=discord.Embed(title=f"[ TARGET ] {username}", color=BLACK)
    txt=f"instagram.com/{username}\ntiktok.com/@{username}\ngithub.com/{username}\nx.com/{username}"
    embed.add_field(name="PUBLIC LINKS", value=f"```\n{txt}\n```")
    await interaction.response.send_message(embed=embed,ephemeral=True)

@bot.tree.command(name="usersearch", description="Genera varianti nome")
async def usersearch(interaction: discord.Interaction, nome:str):
    if not ha_permesso(interaction.user.id,"social") and not is_admin(interaction):
        await interaction.response.send_message("Serve social",ephemeral=True); return
    base=nome.lower().replace(" ","")[:20]
    varianti=[base,f"{base}_",f"{base}01",f"the{base}"]
    embed=discord.Embed(title=f"[ VARIANTS ] {nome}", color=BLACK)
    embed.add_field(name="LIST", value="```\n"+"\n".join(varianti)+"\n```")
    await interaction.response.send_message(embed=embed,ephemeral=True)

@bot.tree.command(name="similar", description="Varianti simili username")
async def similar(interaction: discord.Interaction, username:str):
    if not ha_permesso(interaction.user.id,"social") and not is_admin(interaction):
        await interaction.response.send_message("Serve social",ephemeral=True); return
    base=username.lower().replace(" ","")[:20]
    varianti=[base,f"{base}_",f"real{base}",f"{base}_official"]
    embed=discord.Embed(title=f"[ SIMILAR ] {base}", color=BLACK)
    embed.add_field(name="VARIANTS", value="```\n"+"\n".join(varianti)+"\n```")
    await interaction.response.send_message(embed=embed,ephemeral=True)

@bot.tree.command(name="userdeep", description="Check live se username esiste")
async def userdeep(interaction: discord.Interaction, username:str):
    if not ha_permesso(interaction.user.id,"social") and not is_admin(interaction):
        await interaction.response.send_message("Serve social",ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    username=username.replace("@","").strip()
    sites={"GitHub": f"https://github.com/{username}","Reddit": f"https://www.reddit.com/user/{username}"}
    res=[]
    for n,u in sites.items():
        try:
            r=requests.get(u, timeout=5, headers={"User-Agent":"Mozilla/5.0"})
            res.append(f"{n}: {'ESISTE' if r.status_code==200 else 'NON TROVATO'}")
        except: res.append(f"{n}: ERRORE")
    embed=discord.Embed(title=f"[ USERDEEP ] {username}", color=BLACK)
    embed.add_field(name="LIVE CHECK", value="```\n"+"\n".join(res)+"\n```")
    await interaction.followup.send(embed=embed,ephemeral=True)

@bot.tree.command(name="dominio", description="Link WHOIS / DNS")
async def dominio_cmd(interaction: discord.Interaction, dominio:str):
    try:
        ip=socket.gethostbyname(dominio)
        embed=discord.Embed(title=f"[ DOMAIN ] {dominio}", color=BLACK)
        embed.add_field(name="IP", value=f"```\n{ip}\n```")
        embed.add_field(name="WHOIS", value=f"https://who.is/whois/{dominio}")
        await interaction.response.send_message(embed=embed,ephemeral=True)
    except: await interaction.response.send_message("Dominio non valido",ephemeral=True)

@bot.tree.command(name="siteintel", description="Info complete sito")
async def siteintel(interaction: discord.Interaction, dominio:str):
    if not ha_permesso(interaction.user.id,"ip") and not is_admin(interaction):
        await interaction.response.send_message("Serve ip",ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    try:
        dominio=dominio.replace("https://","").replace("http://","").split("/")[0]
        ip=socket.gethostbyname(dominio)
        embed=discord.Embed(title=f"[ SITEINTEL ] {dominio}", color=BLACK)
        embed.add_field(name="IP", value=f"```\n{ip}\n```")
        embed.add_field(name="LINKS", value=f"[WHOIS](https://who.is/whois/{dominio}) | [Wayback](https://web.archive.org/web/*/{dominio})")
        await interaction.followup.send(embed=embed,ephemeral=True)
    except Exception as e: await interaction.followup.send(f"Errore {e}",ephemeral=True)

@bot.tree.command(name="dork", description="Genera Google Dork")
async def dork_cmd(interaction: discord.Interaction, dominio:str):
    dominio=dominio.replace("https://","").replace("http://","").split("/")[0]
    dorks=[f"site:{dominio} filetype:pdf",f"site:{dominio} filetype:env | sql",f"site:{dominio} intitle:\"index of\""]
    embed=discord.Embed(title=f"[ DORK ] {dominio}", color=BLACK)
    embed.add_field(name="DORKS", value="```\n"+"\n".join(dorks)+"\n```")
    await interaction.response.send_message(embed=embed,ephemeral=True)

@bot.tree.command(name="ip", description="Info su IP pubblico")
async def ipcheck(interaction: discord.Interaction, ip:str):
    if not ha_permesso(interaction.user.id,"ip") and not is_admin(interaction):
        await interaction.response.send_message("Serve ip",ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    try:
        r=requests.get(f"http://ip-api.com/json/{ip}?fields=query,country,city,isp",timeout=8).json()
        embed=discord.Embed(title=f"[ IP ] {ip}", color=BLACK)
        embed.add_field(name="GEO", value=f"```\n{r.get('country')} - {r.get('city')}\n```")
        embed.add_field(name="ISP", value=f"```\n{r.get('isp')}\n```")
        await interaction.followup.send(embed=embed,ephemeral=True)
    except Exception as e: await interaction.followup.send(f"Errore {e}",ephemeral=True)

@bot.tree.command(name="blacklist", description="Check blacklist IP")
async def blacklist_cmd(interaction: discord.Interaction, ip:str):
    embed=discord.Embed(title=f"[ BLACKLIST ] {ip}", color=BLACK)
    embed.add_field(name="CHECK", value=f"[AbuseIPDB](https://www.abuseipdb.com/check/{ip}) | [VT](https://www.virustotal.com/gui/ip-address/{ip})")
    await interaction.response.send_message(embed=embed,ephemeral=True)

@bot.tree.command(name="emailcheck", description="Controlla formato email")
async def emailcheck(interaction: discord.Interaction, email:str):
    if not ha_permesso(interaction.user.id,"email") and not is_admin(interaction):
        await interaction.response.send_message("Serve email",ephemeral=True); return
    dom=email.split("@")[-1] if "@" in email else "N/A"
    embed=discord.Embed(title=f"[ EMAIL ] {email}", color=BLACK)
    embed.add_field(name="DOMAIN", value=f"`{dom}`")
    await interaction.response.send_message(embed=embed,ephemeral=True)

@bot.tree.command(name="leakcheck", description="Check leak dominio")
async def leakcheck(interaction: discord.Interaction, dominio:str):
    embed=discord.Embed(title=f"[ LEAKCHECK ] {dominio}", color=BLACK)
    embed.add_field(name="LINKS", value=f"[HIBP](https://haveibeenpwned.com/domain/{dominio})")
    await interaction.response.send_message(embed=embed,ephemeral=True)

@bot.tree.command(name="hash", description="Genera hash")
async def hash_cmd(interaction: discord.Interaction, testo:str):
    md5=hashlib.md5(testo.encode()).hexdigest()
    embed=discord.Embed(title=f"[ HASH ]", color=BLACK)
    embed.add_field(name="MD5", value=f"```\n{md5}\n```")
    await interaction.response.send_message(embed=embed,ephemeral=True)

@bot.tree.command(name="bin", description="Info BIN carta")
async def bin_cmd(interaction: discord.Interaction, bin_code:str):
    bin_code=re.sub(r"[^0-9]","",bin_code)[:8]
    await interaction.response.defer(ephemeral=True)
    try:
        r=requests.get(f"https://lookup.binlist.net/{bin_code}", headers={"Accept-Version":"3"}, timeout=8).json()
        embed=discord.Embed(title=f"[ BIN ] {bin_code}", color=BLACK)
        embed.add_field(name="BANK", value=f"`{r.get('bank',{}).get('name','N/A')}`")
        await interaction.followup.send(embed=embed,ephemeral=True)
    except: await interaction.followup.send("BIN non trovato",ephemeral=True)

bot.run(TOKEN)
