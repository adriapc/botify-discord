import asyncio
import discord
from discord import app_commands
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import yt_dlp

load_dotenv()


token = os.getenv('DISCORD_TOKEN')
    
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
    
bot = commands.Bot(command_prefix='!', intents=intents)

coder_role = 'Coder'

# Set-up the bot
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'{bot.user.name} està llest!')

# Bot reacts to events   
@bot.event
async def on_member_join(member):
    await member.send(f'Benvingut a la comunitat, {member.name}')
        
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    ctx = await bot.get_context(message)
    if ctx.valid:
        await bot.process_commands(message)
        return
    
    if 'hola' in message.content.lower():
        await message.channel.send(f'Hola, {message.author.name}!')
        
    if 'adeu' in message.content.lower():
        await message.channel.send(f'A reveure, {message.author.name}!')
            
    await bot.process_commands(message)
        
# Assign role     
@bot.command()
async def code(ctx):
    role = discord.utils.get(ctx.guild.roles, name=coder_role)
    if role:
        await ctx.author.add_roles(role)
        await ctx.send(f'{ctx.author.mention} és un {coder_role}')
    else:
        await ctx.send("El rol no existeix")

# Remove role      
@bot.command()
async def uncode(ctx):
    role = discord.utils.get(ctx.guild.roles, name=coder_role)
    if role:
        await ctx.author.remove_roles(role)
        await ctx.send(f'{ctx.author.mention} ja no és un {coder_role}')
    else:
        await ctx.send("El rol no existeix")

# Create a poll        
@bot.command()
async def poll(ctx, *, question):
    embed = discord.Embed(title='New Poll', description=question)
    poll_message = await ctx.send(embed=embed)
    await poll_message.add_reaction('👍')
    await poll_message.add_reaction('👎')

@bot.tree.command(name='play', description='Reprodueix una cançó o afegeix-la a la cua.')
@app_commands.describe(song_query='Search query')
async def play(interaction: discord.Interaction, song_query: str):
    await interaction.response.defer()

    voice_channel = interaction.user.voice.channel

    if voice_channel is None:
        await interaction.followup.send("Has d'estar en un canal de veu")
        return
    
    voice_client = interaction.guild.voice_client

    if voice_client is None:
        voice_client = await voice_channel.connect()
    elif voice_channel != voice_client.channel:
        await voice_client.move_to(voice_channel)
    
ydl_options = {
    'format': 'bestaudio[abr<=96]/bestaudio',
    'noplaylist': True,
    'youtube_include_dash_manifest': False,
    'youtube_include_hls_manifest': False,
}

query = 'ytsearch1: ' + song_query



bot.run(token, log_handler=handler, log_level=logging.DEBUG)
