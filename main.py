import asyncio
from collections import deque
from datetime import datetime
import discord
from discord import app_commands
from discord.ext import commands
import logging
from dotenv import load_dotenv
import platform
from openai import OpenAI
import os
import yt_dlp

load_dotenv()

guild_id = int(os.getenv('GUILD_ID'))

DC_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_KEY = os.getenv('OPENAI_TOKEN')
GUILD_ID = discord.Object(id=guild_id)

SONG_QUEUES = {}

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

# Set-up the bot
bot = commands.Bot(command_prefix='!', intents=intents)

client = OpenAI(api_key=OPENAI_KEY)

# Generate response with gpt-4o-mini
def generate_response(msg):
    instruction = f'''You are an AI assistant, named Botify. 
        You can play music if they are in a voice channel, by typing the following command: /play [song name]. 
        Respond to the messages concretely, as short as possible. Today is {datetime.today()}'''
    body = client.responses.create(
        model="gpt-4o-mini",
        instructions=instruction,
        temperature=0.5,
        input=msg
    )
    
    return body.output_text

# Check is bot connects succesfully
@bot.event
async def on_ready():
    print(f"{bot.user.name} is ready")
    try:
        guild = discord.Object(id=guild_id)
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} commands to guild {guild.id}")
    except Exception as e:
        print(f"Error syncing commands: {e}")
        
# Bot reacts to events   
@bot.event
async def on_member_join(member):
    await member.send(f'Welcome to the server, {member.name}!')

# Send a response to user messages        
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # Generate response and send it
    response = generate_response(message.content)
    await message.channel.send(response)     
    await bot.process_commands(message)
        
# Assign role     
@bot.tree.command(name='assign', description='Assign a role', guild=GUILD_ID)
@app_commands.describe(role_query='Enter a role')
async def assign_role(interaction: discord.Interaction, role_query: str):
    await interaction.response.defer()
    role = discord.utils.get(interaction.guild.roles, name=role_query.strip().lower())
    if role:
        if role not in interaction.user.roles:
            await interaction.user.add_roles(role)
            await interaction.followup.send(f'{interaction.user.mention} is a {role}')
        else:
            await interaction.followup.send(f'You already have this role')
    else:
        await interaction.followup.send("Role doesn't exist")

# Remove role
@bot.tree.command(name='remove', description='Remove a role', guild=GUILD_ID)
@app_commands.describe(role_query='Enter a role')
async def remove_role(interaction: discord.Interaction, role_query: str):
    await interaction.response.defer()
    role = discord.utils.get(interaction.guild.roles, name=role_query.strip().lower())
    if role:
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.followup.send(f'{interaction.user.mention} is no longer a {role}')
        else:
            await interaction.followup.send(f"You do not have that role")
    else:
        await interaction.followup.send("Role doesn't exist")
    
# Create a poll  
@bot.tree.command(name='poll', description='Create a poll', guild=GUILD_ID)
@app_commands.describe(question='Write your question')
async def code(interaction: discord.Interaction, question: str):
    embed = discord.Embed(title=question, description='⬇Vote here⬇', color=discord.Color.purple())
    await interaction.response.send_message(embed=embed)
    poll_message = await interaction.original_response()
    # Bot adds reactions to the poll
    await poll_message.add_reaction('👍')
    await poll_message.add_reaction('👎')

# Get current date and time
@bot.tree.command(name='datetime', description='Get current date and time', guild=GUILD_ID)
async def get_datetime(interaction: discord.Interaction):
    await interaction.response.defer()
    now = datetime.now()
    formatted_time = now.strftime("%H:%M %d-%m-%Y")
    await interaction.followup.send(f'{formatted_time}')

@bot.tree.command(name='clear-chat', description='Delete all messages in the channel', guild=GUILD_ID)
async def delete_messages(interaction: discord.Interaction):
    await interaction.response.defer()
    if 'admin' in str(interaction.user.roles):
        await interaction.channel.purge()
        await interaction.followup.send('Chat cleared!')
    else:
        await interaction.followup.send('You do not have permission to do that')

# Play a song or add it to the queue
@bot.tree.command(name='play', description='Play a song or add it to the queue', guild=GUILD_ID)
@app_commands.describe(song_query='Search query')
async def play(interaction: discord.Interaction, song_query: str):
    await interaction.response.defer()

    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.followup.send("You must be in a voice channel")
        return
    
    voice_channel = interaction.user.voice.channel
    voice_client = interaction.guild.voice_client
    
    # Bot connects to voice channel
    if voice_client is None:
        voice_client = await voice_channel.connect()
    elif voice_channel != voice_client.channel:
        await voice_client.move_to(voice_channel)
    
    ydl_options = {
        'format': 'bestaudio[abr<=96]/bestaudio',
        'noplaylist': True,
        'youtube_include_dash_manifest': False,
        'youtube_include_hls_manifest': False,
        'cookiefile': 'cookies.txt',
    }

    query = 'ytsearch1: ' + song_query
    results = await search_ytdlp_async(query, ydl_options)
    tracks = results.get('entries', [])

    if not tracks:
        await interaction.followup.send("No results found")
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
        await interaction.followup.send(f'Botify connected!')
        await play_next_song(voice_client, guild_id, interaction.channel)
    

# Skip current song
@bot.tree.command(name='skip', description='Skip the current song', guild=GUILD_ID)
async def skip(interaction: discord.Interaction):
    await interaction.response.defer()
    if interaction.guild.voice_client and (interaction.guild.voice_client.is_playing() or interaction.guild.voice_client.is_paused()):
        interaction.guild.voice_client.stop()
        await interaction.followup.send('⏭ Skipped the current song')
    else:
        await interaction.followup.send('Nothing to skip')

# Pause the playback
@bot.tree.command(name='pause', description='Pause the current song', guild=GUILD_ID)
async def pause(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    
    if voice_client is None:
        return await interaction.response.send_message("I'm not in a voice channel")
    
    if not voice_client.is_playing():
        return await interaction.response.send_message("Nothing is being played")

    voice_client.pause()
    await interaction.response.send_message('⏸Song paused')

# Resume the song
@bot.tree.command(name="resume", description="Resume the currently paused song", guild=GUILD_ID)
async def resume(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client

    # Check if the bot is in a voice channel
    if voice_client is None:
        return await interaction.response.send_message("I'm not in a voice channel")

    # Check if it's actually paused
    if not voice_client.is_paused():
        return await interaction.response.send_message("Song is not paused right now")
    
    # Resume playback
    voice_client.resume()
    await interaction.response.send_message("▶ Song resumed")

# Stop the playback
@bot.tree.command(name="stop", description="Stop playback and clear the queue", guild=GUILD_ID)
async def stop(interaction: discord.Interaction):
    await interaction.response.defer()
    voice_client = interaction.guild.voice_client

    # Check if the bot is in a voice channel
    if not voice_client or not voice_client.is_connected():
        return await interaction.followup.send("I'm not connected to any voice channel")

    # Clear the guild's queue
    guild_id_str = str(interaction.guild_id)
    if guild_id_str in SONG_QUEUES:
        SONG_QUEUES[guild_id_str].clear()

    # If something is playing or paused, stop it
    if voice_client.is_playing() or voice_client.is_paused():
        voice_client.stop()

    # Disconnect from the channel
    await interaction.followup.send("Music disconnected")
    
    await voice_client.disconnect()

print(platform.system())   
    
async def play_next_song(voice_client, guild_id, channel):
    if SONG_QUEUES[guild_id]:
        audio_url, title = SONG_QUEUES[guild_id].popleft()

        ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn -c:a libopus -b:a 96k',
        }
        
        ffmpeg_path = "bin\\ffmpeg\\ffmpeg.exe" if platform.system() == "Windows" else "bin/ffmpeg/ffmpeg"

        source = discord.FFmpegOpusAudio(audio_url, **ffmpeg_options, executable=ffmpeg_path)

        def after_play(error):
            if error:
                print(f'Error playing {title}: {error}')
            asyncio.run_coroutine_threadsafe(play_next_song(voice_client, guild_id, channel), bot.loop)
        
        voice_client.play(source, after=after_play)
        asyncio.create_task(channel.send(f'▶ {title} is playing'))
        
    else:
        await voice_client.disconnect()
        SONG_QUEUES[guild_id] = deque()
        

bot.run(DC_TOKEN, log_handler=handler, log_level=logging.DEBUG)
