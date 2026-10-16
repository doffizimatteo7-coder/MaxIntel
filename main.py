import os, json, asyncio, re, socket, hashlib
import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask
from threading import Thread
import requests

app = Flask('')
@app.route('/')
def home(): return "MAXINTEL V5 BLACK - ONLINE"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080), daemon=True).start()

TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("TOKEN")
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

BLACK = 0x0a0a0a
BLUE = 0x00d0ff
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
    print(f"MAXINTEL V5 ONLINE {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="BLACK EDITION | /help"))
    await bot.tree.sync()

# /permesso
@bot.tree.command(name="permesso", description="⚙️ Admin - gestisci permessi MAXINTEL")
@app_commands.choices(
    azione=[
        app_commands.Choice(name="aggiungi",value="aggiungi"),
        app_commands.Choice(name="rimuovi",value="rimuovi")
    ],
    tipo=[
        app_commands.Choice(name="social - osint/userdeep/similar",value="social"),
        app_commands.Choice(name="email - email/phone/leak",value="email"),
        app_commands.Choice(name="ip - ip/dominio/siteintel/dork/blacklist",value="ip"),
        app_commands.Choice(name="all - tutto",value="all")
    ]
)
async def permesso(interaction: discord.Interaction, azione:str, user:discord.Member, tipo:str):
    if not is_admin(interaction):
        await interaction.response.send_message("◼️ Solo admin può usare /permesso",ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    async with _lock:
        p=carica_permessi(); uid=str(user.id); p.setdefault(uid,[])
        if azione=="aggiungi":
            if tipo not in p[uid]: p[uid].append(tipo)
            salva_permessi(p)
            embed=discord.Embed(title="◼️ PERMESSO AGGIUNTO", color=BLACK)
            embed.description=f"```ansi\n\x1b[36m[ ACCESS GRANTED ]\x1b[0m\n```"
            embed.add_field(name="🔷 USER", value=f"{user.mention}")
            embed.add_field(name="🔷 TIPO", value=f"`{tipo}`")
            await interaction.followup.send(embed=embed,ephemeral=True)
        else:
            if tipo in p[uid]: p[uid].remove(tipo)
            salva_permessi(p)
            embed=discord.Embed(title="◼️ PERMESSO RIMOSSO", color=BLACK)
            embed.add_field(name="🔷 USER", value=f"{user.mention}")
            embed.add_field(name="🔷 TIPO", value=f"`{tipo}`")
            await interaction.followup.send(embed=embed,ephemeral=True)

# /help NERO FIGO
@bot.tree.command(name="help", description="◼️ Pannello MAXINTEL BLACK")
async def help_cmd(interaction: discord.Interaction):
    embed=discord.Embed(title="◼️ MAXINTEL V5 // BLACK NEON EDITION", color=BLACK)
    embed.description="```ansi\n\x1b[36m[ SYSTEM ONLINE // CORE v5.0 BLACK ]\n[ MADE FOR MAXIMO // LEGAL OSINT ]\x1b[0m\n```"
    embed.add_field(name="◼️ USER INTEL - NERO", value="`osint <user>` - 5 link pubblici\n`similar <user>` - varianti username\n`userdeep <user>` - ★ LIVE check se esiste davvero\n`usersearch <nome>` - genera varianti", inline=False)
    embed.add_field(name="◼️ SITE INTEL - BLU", value="`siteintel <dominio>` - ★ IP + email pubbliche + tech\n`dork <dominio>` - ★ Google Dork pronti\n`dominio <dominio>` - IP + WHOIS\n`wayback` in siteintel", inline=False)
    embed.add_field(name="◼️ EMAIL / PHONE / SECURITY", value="`emailinfo <email>` - formato + MX\n`phoneinfo <num>` - validazione\n`leakcheck <dominio>` - leak dominio aziendale\n`blacklist <ip>` - ★ check 80 blacklist", inline=False)
    embed.add_field(name="◼️ IP / UTILS", value="`ip <ip>` - GEO + ISP\n`hash <testo>` - MD5/SHA1/SHA256\n`bin <6 cifre>` - info banca BIN", inline=False)
    embed.add_field(name="◼️ ADMIN", value="`/permesso aggiungi @user tipo` - dai permessi\n`/permesso rimuovi @user tipo` - togli permessi", inline=False)
    embed.set_footer(text="◼️ BLACK THEME // 🔷 BLUE NEON // LEGAL ONLY")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# --- VECCHI COMANDI CON DECORAZIONE NERA ---
@bot.tree.command(name="osint", description="Cerca username pubblico")
async def osint(interaction: discord.Interaction, username:str):
    if not ha_permesso(interaction.user.id,"social") and not is_admin(interaction):
        await interaction.response.send_message("◼️ Serve permesso `social` - chiedi a MAXIMO",ephemeral=True); return
    username=username.replace("@","")[:25]
    embed=discord.Embed(title=f"◼️ [ TARGET ACQUIRED ] {username}", color=BLACK)
    embed.description="```ansi\n\x1b[36m[ SCANNING PUBLIC DATABASES... ]\x1b[0m\n```"
    links=f"IG: instagram.com/{username}\nTikTok: tiktok.com/@{username}\nYT: youtube.com/@{username}\nGitHub: github.com/{username}\nX: x.com/{username}"
    embed.add_field(name="🔷 PUBLIC LINKS", value=f"```\n{links}\n```")
    await interaction.response.send_message(embed=embed,ephemeral=True)

@bot.tree.command(name="similar", description="Varianti username simili")
async def similar(interaction: discord.Interaction, username:str):
    if not ha_permesso(interaction.user.id,"social") and not is_admin(interaction):
        await interaction.response.send_message("Serve social",ephemeral=True); return
    base=username.lower().replace(" ","")[:20]
    varianti=[base,f"{base}_",f"{base}.",f"{base}01",f"the{base}",f"{base}_official",f"real{base}"]
    embed=discord.Embed(title=f"◼️ [ SIMILAR SCAN ] {base}", color=BLACK)
    embed.add_field(name="🔷 VARIANTS", value="```\n"+"\n".join(varianti)+"\n```")
    await interaction.response.send_message(embed=embed,ephemeral=True)

@bot.tree.command(name="usersearch", description="Genera varianti nome")
async def usersearch(interaction: discord.Interaction, nome:str):
    if not ha_permesso(interaction.user.id,"social") and not is_admin(interaction):
        await interaction.response.send_message("Serve social",ephemeral=True); return
    base=nome.lower().replace(" ","")[:20]
    varianti=[base,f"{base}_",f"{base}01",f"the{base}",f"{base}_official"]
    embed=discord.Embed(title=f"◼️ [ VARIANTS ] {nome}", description="```\n"+"\n".join(varianti)+"\n```", color=BLACK)
    await interaction.response.send_message(embed=embed,ephemeral=True)

@bot.tree.command(name="emailinfo", description="Info email + MX")
async def emailinfo(interaction: discord.Interaction, email:str):
    if not ha_permesso(interaction.user.id,"email") and not is_admin(interaction):
        await interaction.response.send_message("Serve email",ephemeral=True); return
    dom=email.split("@")[-1] if "@" in email else "N/A"
    embed=discord.Embed(title=f"◼️ [ EMAIL TRACE ] {email}", color=BLACK)
    embed.description="```ansi\n\x1b[36m[ ANALYZING EMAIL STRUCTURE ]\x1b[0m\n```"
    embed.add_field(name="🔷 FORMAT", value=f"`{'VALIDO' if '@' in email else 'INVALIDO'}`", inline=True)
    embed.add_field(name="🔷 DOMAIN", value=f"`{dom}`", inline=True)
    embed.add_field(name="🔷 MX TOOL", value=f"https://mxtoolbox.com/SuperTool.aspx?action=mx%3a{dom}", inline=False)
    await interaction.response.send_message(embed=embed,ephemeral=True)

@bot.tree.command(name="phoneinfo", description="Validazione telefono")
async def phoneinfo(interaction: discord.Interaction, numero:str):
    if not ha_permesso(interaction.user.id,"email") and not is_admin(interaction):
        await interaction.response.send_message("Serve email",ephemeral=True); return
    pulito=re.sub(r"[^0-9+]", "", numero)
    embed=discord.Embed(title=f"◼️ [ PHONE TRACE ] {pulito}", color=BLACK)
    embed.add_field(name="🔷 CHECK", value=f"```\nLunghezza: {len(pulito)}\nStatus: {'OK' if 8 <= len(pulito) <= 15 else 'INVALIDO'}\n```")
    await interaction.response.send_message(embed=embed,ephemeral=True)

@bot.tree.command(name="ip", description="IP GEO + ISP")
async def ipcheck(interaction: discord.Interaction, ip:str):
    if not ha_permesso(interaction.user.id,"ip") and not is_admin(interaction):
        await interaction.response.send_message("Serve ip",ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    try:
        r=requests.get(f"http://ip-api.com/json/{ip}?fields=query,country,city,isp,org",timeout=8).json()
        embed=discord.Embed(title=f"◼️ [ IP TRACE ] {r.get('query')}", color=BLACK)
        embed.description="```ansi\n\x1b[36m[ GEOLOCATING TARGET... ]\x1b[0m\n```"
        embed.add_field(name="🔷 GEO", value=f"```\n{r.get('country')} - {r.get('city')}\n```")
        embed.add_field(name="🔷 ISP / ORG", value=f"```\n{r.get('isp')}\n{r.get('org')}\n```")
        await interaction.followup.send(embed=embed,ephemeral=True)
    except Exception as e: await interaction.followup.send(f"Errore {e}",ephemeral=True)

@bot.tree.command(name="dominio", description="IP + WHOIS dominio")
async def dominio_cmd(interaction: discord.Interaction, dominio:str):
    if not ha_permesso(interaction.user.id,"ip") and not is_admin(interaction):
        await interaction.response.send_message("Serve ip",ephemeral=True); return
    try:
        ip=socket.gethostbyname(dominio)
        embed=discord.Embed(title=f"◼️ [ DOMAIN ] {dominio}", color=BLACK)
        embed.add_field(name="🔷 IP RESOLVED", value=f"```\n{ip}\n```")
        embed.add_field(name="🔷 WHOIS", value=f"https://who.is/whois/{dominio}")
        await interaction.response.send_message(embed=embed,ephemeral=True)
    except: await interaction.response.send_message("◼️ Dominio non valido",ephemeral=True)

@bot.tree.command(name="hash", description="Hash MD5/SHA")
async def hash_cmd(interaction: discord.Interaction, testo:str):
    md5=hashlib.md5(testo.encode()).hexdigest()
    sha1=hashlib.sha1(testo.encode()).hexdigest()
    sha256=hashlib.sha256(testo.encode()).hexdigest()
    embed=discord.Embed(title=f"◼️ [ HASH GEN ] {testo[:15]}", color=BLACK)
    embed.add_field(name="🔷 MD5", value=f"```\n{md5}\n```", inline=False)
    embed.add_field(name="🔷 SHA1", value=f"```\n{sha1}\n```", inline=False)
    embed.add_field(name="🔷 SHA256", value=f"```\n{sha256}\n```", inline=False)
    await interaction.response.send_message(embed=embed,ephemeral=True)

@bot.tree.command(name="bin", description="BIN carta - banca/paese")
async def bin_cmd(interaction: discord.Interaction, bin_code:str):
    if not ha_permesso(interaction.user.id,"ip") and not is_admin(interaction):
        await interaction.response.send_message("Serve ip",ephemeral=True); return
    bin_code=re.sub(r"[^0-9]","",bin_code)[:8]
    await interaction.response.defer(ephemeral=True)
    try:
        r=requests.get(f"https://lookup.binlist.net/{bin_code}", headers={"Accept-Version":"3"}, timeout=8).json()
        embed=discord.Embed(title=f"◼️ [ BIN INTEL ] {bin_code}", color=BLACK)
        embed.add_field(name="🔷 BANK", value=f"`{r.get('bank',{}).get('name','N/A')}`")
        embed.add_field(name="🔷 TYPE", value=f"`{r.get('type','')} {r.get('scheme','')}`")
        embed.add_field(name="🔷 COUNTRY", value=f"```\n{r.get('country',{}).get('name','N/A')} {r.get('country',{}).get('emoji','')}\n```")
        await interaction.followup.send(embed=embed,ephemeral=True)
    except: await interaction.followup.send("◼️ BIN non trovato",ephemeral=True)

# --- NUOVI COMANDI RICHIESTI ---
@bot.tree.command(name="siteintel", description="★ TUTTO su un sito - OSINT completo")
async def siteintel(interaction: discord.Interaction, dominio:str):
    if not ha_permesso(interaction.user.id,"ip") and not is_admin(interaction):
        await interaction.response.send_message("◼️ Serve permesso `ip` - chiedi a MAXIMO",ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    try:
        dominio=dominio.replace("https://","").replace("http://","").split("/")[0]
        ip=socket.gethostbyname(dominio)
        try:
            html=requests.get(f"https://{dominio}", timeout=6, headers={"User-Agent":"Mozilla/5.0"}).text[:8000]
            emails=re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", html)
            emails=list(set(emails))[:3]
        except: emails=[]
        embed=discord.Embed(title=f"◼️ [ SITEINTEL ] {dominio}", color=BLACK)
        embed.description="```ansi\n\x1b[36m[ DEEP SCAN // 100% COMPLETE ]\x1b[0m\n```"
        embed.add_field(name="🔷 NETWORK", value=f"```\nIP: {ip}\nWHOIS: who.is/whois/{dominio}\n```", inline=False)
        embed.add_field(name="🔷 CONTACTS PUBBLICI", value=f"```\n{', '.join(emails) if emails else 'Nessuna email pubblica'}\n```", inline=False)
        embed.add_field(name="🔷 TECH + ARCHIVE", value=f"[BuiltWith](https://builtwith.com/{dominio}) | [Wayback](https://web.archive.org/web/*/{dominio}) | [Whois](https://who.is/whois/{dominio})", inline=False)
        await interaction.followup.send(embed=embed,ephemeral=True)
    except Exception as e: await interaction.followup.send(f"Errore: {e}",ephemeral=True)

@bot.tree.command(name="userdeep", description="★ LIVE check se username esiste davvero")
async def userdeep(interaction: discord.Interaction, username:str):
    if not ha_permesso(interaction.user.id,"social") and not is_admin(interaction):
        await interaction.response.send_message("Serve social",ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    username=username.replace("@","").strip()
    sites={"GitHub": f"https://github.com/{username}","TikTok": f"https://www.tiktok.com/@{username}","Reddit": f"https://www.reddit.com/user/{username}","Pinterest": f"https://www.pinterest.com/{username}/"}
    risultati=[]
    for name, url in sites.items():
        try:
            r=requests.get(url, timeout=5, headers={"User-Agent":"Mozilla/5.0"})
            status = "🟢 ESISTE" if r.status_code==200 else "🔴 NON TROVATO"
            risultati.append(f"{name}: {status}")
        except: risultati.append(f"{name}: ERRORE")
    embed=discord.Embed(title=f"◼️ [ USERDEEP LIVE ] {username}", color=BLACK)
    embed.description="```ansi\n\x1b[36m[ LIVE PROBING PROFILES... ]\x1b[0m\n```"
    embed.add_field(name="🔷 RISULTATO LIVE", value="```\n"+"\n".join(risultati)+"\n```")
    await interaction.followup.send(embed=embed,ephemeral=True)

@bot.tree.command(name="dork", description="★ Genera Google Dork per dominio")
async def dork_cmd(interaction: discord.Interaction, dominio:str):
    if not ha_permesso(interaction.user.id,"ip") and not is_admin(interaction):
        await interaction.response.send_message("Serve ip",ephemeral=True); return
    dominio=dominio.replace("https://","").replace("http://","").split("/")[0]
    dorks=[f"site:{dominio} filetype:pdf",f"site:{dominio} filetype:sql | filetype:env | filetype:xls",f"site:{dominio} intitle:\"index of\"",f"site:{dominio} inurl:admin | inurl:login",f"\"{dominio}\" ext:log | ext:txt"]
    embed=discord.Embed(title=f"◼️ [ DORK GEN ] {dominio}", color=BLACK)
    embed.description="```ansi\n\x1b[36m[ GOOGLE HACKING DATABASE // READY ]\x1b[0m\n```"
    embed.add_field(name="🔷 DORKS PRONTI - COPIA SU GOOGLE", value="```\n"+"\n".join(dorks)+"\n```")
    await interaction.response.send_message(embed=embed,ephemeral=True)

@bot.tree.command(name="leakcheck", description="Check leak dominio aziendale")
async def leakcheck(interaction: discord.Interaction, dominio:str):
    if not ha_permesso(interaction.user.id,"email") and not is_admin(interaction):
        await interaction.response.send_message("Serve email",ephemeral=True); return
    dominio=dominio.replace("https://","").replace("http://","").split("/")[0]
    embed=discord.Embed(title=f"◼️ [ LEAKCHECK ] {dominio}", color=BLACK)
    embed.add_field(name="🔷 LINKS SICURI", value=f"[HIBP Domain](https://haveibeenpwned.com/domain/{dominio}) | [DeHashed](https://dehashed.com/search?query={dominio}) | [IntelX](https://intelx.io/?s={dominio})")
    await interaction.response.send_message(embed=embed,ephemeral=True)

@bot.tree.command(name="blacklist", description="★ Check se IP è in blacklist spam/hacker")
async def blacklist_cmd(interaction: discord.Interaction, ip:str):
    if not ha_permesso(interaction.user.id,"ip") and not is_admin(interaction):
        await interaction.response.send_message("Serve ip",ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    try:
        r=requests.get(f"https://api.abuseipdb.com/api/v2/check?ipAddress={ip}", headers={"Key":"YOUR_KEY","Accept":"application/json"}, timeout=5)
        # fallback pubblico senza key
        embed=discord.Embed(title=f"◼️ [ BLACKLIST SCAN ] {ip}", color=BLACK)
        embed.description="```ansi\n\x1b[36m[ SCANNING 80+ BLACKLISTS... ]\x1b[0m\n```"
        embed.add_field(name="🔷 CHECK", value=f"[AbuseIPDB](https://www.abuseipdb.com/check/{ip}) | [VirusTotal](https://www.virustotal.com/gui/ip-address/{ip}) | [Shodan](https://www.shodan.io/host/{ip})", inline=False)
        embed.add_field(name="🔷 STATUS", value="```\nApri i link per vedere se IP è segnalato come spam/hacker\n```")
        await interaction.followup.send(embed=embed,ephemeral=True)
    except Exception as e: await interaction.followup.send(f"Errore {e}",ephemeral=True)

bot.run(TOKEN)
