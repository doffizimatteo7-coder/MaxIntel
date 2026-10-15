import os, re, requests, whois, phonenumbers
from phonenumbers import geocoder, carrier
from email_validator import validate_email, EmailNotValidError
import aiohttp
import discord
from discord import app_commands
from flask import Flask
import threading

# --- WEB SERVER PER RENDER ---
app = Flask(__name__)
@app.route('/')
def home(): return "MaxIntel V2 Online"
def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"MaxIntel V2 Online come {bot.user} - {len(tree.get_commands())} comandi")

# /ping
@tree.command(name="ping", description="Stato bot")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🟢 **MaxIntel V2 Online**\n🏓 {round(bot.latency*1000)}ms")

# /osint - USERNAME SCAN 20+ SITI
@tree.command(name="osint", description="Scansione username su 20+ social")
async def osint(interaction: discord.Interaction, username: str):
    await interaction.response.defer()
    sites = {
        "Instagram": f"https://www.instagram.com/{username}",
        "GitHub": f"https://github.com/{username}",
        "TikTok": f"https://www.tiktok.com/@{username}",
        "X/Twitter": f"https://x.com/{username}",
        "Reddit": f"https://www.reddit.com/user/{username}",
        "YouTube": f"https://www.youtube.com/@{username}",
        "Twitch": f"https://www.twitch.tv/{username}",
        "Pinterest": f"https://www.pinterest.com/{username}/",
        "Telegram": f"https://t.me/{username}",
        "Spotify": f"https://open.spotify.com/user/{username}",
        "Steam": f"https://steamcommunity.com/id/{username}",
        "Medium": f"https://medium.com/@{username}",
        "Behance": f"https://www.behance.net/{username}",
        "GitLab": f"https://gitlab.com/{username}",
        "SoundCloud": f"https://soundcloud.com/{username}",
        "Roblox": f"https://www.roblox.com/user.aspx?username={username}"
    }
    embed = discord.Embed(title=f"🔍 OSINT: {username}", color=0x00ff00)
    found = 0
    async with aiohttp.ClientSession() as session:
        for name, url in sites.items():
            try:
                async with session.get(url, timeout=6, headers={"User-Agent": "Mozilla/5.0"}) as r:
                    if r.status == 200:
                        embed.add_field(name=name, value=f"[✅ Trovato]({url})", inline=True)
                        found += 1
            except: pass
    embed.set_footer(text=f"Trovati {found}/{len(sites)} profili pubblici | OSINT legale")
    await interaction.followup.send(embed=embed)

# /email - ANALISI EMAIL
@tree.command(name="email", description="Analizza email (validità, gravatar, dominio)")
async def email_check(interaction: discord.Interaction, email: str):
    await interaction.response.defer()
    try:
        v = validate_email(email)
        domain = email.split('@')[1]
        # Check Gravatar
        grav = f"https://www.gravatar.com/avatar/{email.lower().strip()}?d=404"
        has_grav = requests.get(grav, timeout=5).status_code == 200

        # Info dominio
        w = whois.whois(domain)

        embed = discord.Embed(title=f"📧 Analisi Email: {email}", color=0x3498db)
        embed.add_field(name="✅ Valida", value=str(v.email), inline=False)
        embed.add_field(name="Dominio", value=domain, inline=True)
        embed.add_field(name="Gravatar", value="Sì, ha avatar" if has_grav else "No avatar", inline=True)
        embed.add_field(name="Registrar Dominio", value=str(w.registrar)[:100] if w.registrar else "N/D", inline=False)
        embed.set_footer(text="Dati solo pubblici")
        await interaction.followup.send(embed=embed)
    except EmailNotValidError as e:
        await interaction.followup.send(f"❌ Email non valida: {e}")
    except Exception as e:
        await interaction.followup.send(f"Errore: {e}")

# /phone - INFO NUMERO
@tree.command(name="phone", description="Info su numero di telefono")
async def phone_check(interaction: discord.Interaction, numero: str):
    await interaction.response.defer()
    try:
        # Es: +39 3331234567
        parsed = phonenumbers.parse(numero, None)
        valid = phonenumbers.is_valid_number(parsed)
        embed = discord.Embed(title=f"📱 {numero}", color=0x9b59b6)
        embed.add_field(name="Valido", value="Sì ✅" if valid else "No ❌", inline=True)
        embed.add_field(name="Paese", value=geocoder.description_for_number(parsed, "it"), inline=True)
        embed.add_field(name="Operatore", value=carrier.name_for_number(parsed, "it") or "N/D", inline=True)
        embed.add_field(name="Formato E164", value=phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164), inline=False)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"Formato non valido. Usa formato internazionale: +39 333... | Errore: {e}")

# /ip - GEO IP AVANZATO
@tree.command(name="ip", description="Geolocalizzazione IP + ISP + Mappa")
async def ipinfo(interaction: discord.Interaction, ip: str):
    await interaction.response.defer()
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}?fields=status,message,country,regionName,city,zip,lat,lon,isp,org,as,proxy,hosting,query").json()
        if r['status'] == 'fail':
            await interaction.followup.send("IP non valido")
            return
        embed = discord.Embed(title=f"🌍 IP: {r['query']}", color=0xe74c3c)
        embed.add_field(name="📍 Posizione", value=f"{r.get('city')}, {r.get('regionName')}, {r.get('country')} {r.get('zip')}", inline=False)
        embed.add_field(name="ISP / Org", value=f"{r.get('isp')} / {r.get('org')}", inline=False)
        embed.add_field(name="AS", value=r.get('as'), inline=True)
        embed.add_field(name="Hosting/VPN", value=f"Proxy: {r.get('proxy')} | Hosting: {r.get('hosting')}", inline=True)
        embed.add_field(name="Maps", value=f"[Google Maps](https://www.google.com/maps/search/{r.get('lat')},{r.get('lon')})", inline=False)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"Errore IP: {e}")

# /domain - WHOIS + DNS
@tree.command(name="domain", description="Analisi dominio completa")
async def domain(interaction: discord.Interaction, dominio: str):
    await interaction.response.defer()
    try:
        w = whois.whois(dominio)
        dns = requests.get(f"https://dns.google/resolve?name={dominio}").json()
        embed = discord.Embed(title=f"🌐 {dominio}", color=0xf1c40f)
        embed.add_field(name="Registrar", value=str(w.registrar)[:200] if w.registrar else "N/D", inline=False)
        embed.add_field(name="Creato", value=str(w.creation_date)[:100], inline=True)
        embed.add_field(name="Scadenza", value=str(w.expiration_date)[:100], inline=True)
        embed.add_field(name="NameServers", value=str(w.name_servers)[:500] if w.name_servers else "N/D", inline=False)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"Errore dominio: {e}")

# /help
@tree.command(name="help", description="Lista comandi MaxIntel")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="📚 MaxIntel V2 - Comandi", color=0x00ff00, description="Tutto OSINT pubblico e legale")
    embed.add_field(name="/osint <user>", value="Cerca username su 16+ social", inline=False)
    embed.add_field(name="/email <email>", value="Valida email + gravatar + dominio", inline=False)
    embed.add_field(name="/phone <+39...>", value="Info numero, paese, operatore", inline=False)
    embed.add_field(name="/ip <ip>", value="Geo IP, ISP, mappa", inline=False)
    embed.add_field(name="/domain <sito.com>", value="Whois + DNS", inline=False)
    embed.add_field(name="/ping", value="Stato bot", inline=False)
    await interaction.response.send_message(embed=embed)

threading.Thread(target=run_web).start()
bot.run(TOKEN)
