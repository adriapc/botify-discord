import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

load_dotenv()


token = os.getenv('DISCORD_TOKEN')
    
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
    
bot = commands.Bot(command_prefix='!', intents=intents)

coder_role = 'Coder'

@bot.event
async def on_ready():
    print(f'{bot.user.name} està llest!')
    
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
        
        
@bot.command()
async def code(ctx):
    role = discord.utils.get(ctx.guild.roles, name=coder_role)
    if role:
        await ctx.author.add_roles(role)
        await ctx.send(f'{ctx.author.mention} és un {coder_role}')
    else:
        await ctx.send("El rol no existeix")
        
@bot.command()
async def uncode(ctx):
    role = discord.utils.get(ctx.guild.roles, name=coder_role)
    if role:
        await ctx.author.remove_roles(role)
        await ctx.send(f'{ctx.author.mention} ja no és un {coder_role}')
    else:
        await ctx.send("El rol no existeix")
        
@bot.command()
async def poll(ctx, *, question):
    embed = discord.Embed(title='New Poll', description=question)
    poll_message = await ctx.send(embed=embed)
    await poll_message.add_reaction('👍')
    await poll_message.add_reaction('👎')




bot.run(token, log_handler=handler, log_level=logging.DEBUG)
