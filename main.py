import asyncio
from collections import deque
import discord
from discord import app_commands
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import yt_dlp

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
SONG_QUEUES = {}
GUILD_ID = discord.Object(id=1404769845719072799)

async def search_ytdlp_async(query, ydl_opts):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _extract(query, ydl_opts))

def _extract(query, ydl_opts):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(query, download=False)

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
    
bot = commands.Bot(command_prefix='!', intents=intents)

coder_role = 'Coder'

# Set-up the bot
@bot.event
async def on_ready():
    # await bot.tree.sync(guild=discord.Object(id=GUILD_ID)) 
    print(f"{bot.user} is ready")

    try:
        guild = discord.Object(id=1404769845719072799)
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} commands to guild {guild.id}")
    except Exception as e:
        print(f"Error syncing commands: {e}")
        
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

@bot.tree.command(name='play', description='Reprodueix una cançó o afegeix-la a la cua.', guild=GUILD_ID)
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
    results = await search_ytdlp_async(query, ydl_options)
    tracks = results.get('entries', [])

    if tracks is None:
        await interaction.followup.send("No s'ha trobat cap resultat.")
        return
    
    first_track = tracks[0]
    audio_url = first_track['url']
    title = first_track.get('title', 'Untitled')
    
    guild_id = str(interaction.guild_id)
    if SONG_QUEUES.get(guild_id) is None:
        SONG_QUEUES[guild_id] = deque()
        
    SONG_QUEUES[guild_id].append((audio_url, title))
    
    if voice_client.is_playing() or voice_client.is_paused():
        await interaction.followup.send(f'{title} added to queue')
    else:
        await interaction.followup.send(f'{title} is playing')
        await play_next_song(voice_client, guild_id, interaction.channel)
    
    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn -c:a libopus -b:a 96k',
    }
    
    source = discord.FFmpegOpusAudio(audio_url, **ffmpeg_options, executable="bin\\ffmpeg\\ffmpeg.exe")
    
    voice_client.play(source)

@bot.tree.command(name='skip', description='Skip the current song', guild=GUILD_ID)
async def skip(interaction: discord.Interaction):
    if interaction.guild.voice_client and (interaction.guild.voice_client.is_playing() or interaction.guild.voice_client.is_paused()):
        interaction.guild.voice_client.stop()
        await interaction.followup.send_message('Skipped the current song')
    else:
        await interaction.followup.send_message('Nothing to skip')
        
@bot.tree.command(name='pause', description='Pause the current song', guild=GUILD_ID)
async def pause(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    
    if voice_client is None:
        return await interaction.response.send_message("I'm not in a voice channel")
    
    if not voice_client.is_playing():
        return await interaction.response.send_message("Nothing is being played")

    voice_client.pause()
    await interaction.response.send_message('The song was paused')
    
@bot.tree.command(name="resume", description="Resume the currently paused song.", guild=GUILD_ID)
async def resume(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client

    # Check if the bot is in a voice channel
    if voice_client is None:
        return await interaction.response.send_message("I'm not in a voice channel.")

    # Check if it's actually paused
    if not voice_client.is_paused():
        return await interaction.response.send_message("Song is not paused right now.")
    
    # Resume playback
    voice_client.resume()
    await interaction.response.send_message("Song resumed!")
    
@bot.tree.command(name="stop", description="Stop playback and clear the queue.", guild=GUILD_ID)
async def stop(interaction: discord.Interaction):
    await interaction.response.defer()
    voice_client = interaction.guild.voice_client

    # Check if the bot is in a voice channel
    if not voice_client or not voice_client.is_connected():
        return await interaction.followup.send("I'm not connected to any voice channel.")

    # Clear the guild's queue
    guild_id_str = str(interaction.guild_id)
    if guild_id_str in SONG_QUEUES:
        SONG_QUEUES[guild_id_str].clear()

    # If something is playing or paused, stop it
    if voice_client.is_playing() or voice_client.is_paused():
        voice_client.stop()

    # (Optional) Disconnect from the channel
    await interaction.followup.send("Stopped playback and disconnected!")
    
    await voice_client.disconnect()
    
    
async def play_next_song(voice_client, guild_id, channel):
    if SONG_QUEUES[guild_id]:
        audio_url, title = SONG_QUEUES[guild_id].popleft()

        ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn -c:a libopus -b:a 96k',
        }
    
        source = discord.FFmpegOpusAudio(audio_url, **ffmpeg_options, executable="bin\\ffmpeg\\ffmpeg.exe")

        def after_play(error):
            if error:
                print(f'Error playing {title}: {error}')
            asyncio.run_coroutine_threadsafe(play_next_song(voice_client, guild_id, channel), bot.loop)
        
        voice_client.play(source, after=after_play)
        asyncio.create_task(channel.send(f'{title} is playing'))
        
    else:
        await voice_client.disconnect()
        SONG_QUEUES[guild_id] = deque()
        


bot.run(token, log_handler=handler, log_level=logging.DEBUG)
