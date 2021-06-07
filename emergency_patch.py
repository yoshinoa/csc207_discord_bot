import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.all()
client = commands.Bot(intents=intents, command_prefix='!')
message_ids = [851114599922008094, 851114060736757850]

async def patch():
    channel1 = await client.fetch_channel(851114059520540722)
    message1 = await channel1.fetch_message(851114060736757850)
    channel2 = await client.fetch_channel(851114599091535912)
    message2 = await channel2.fetch_message(851114599922008094)
    await message1.add_reaction('<:BJT:851352478452285480>')
    await message2.add_reaction('<:BJT:851352478452285480>')


@client.command(name='patch')
async def patch_command(ctx):
    await patch()


@client.event
async def on_message(message):
    if message.author.id != client.user.id:
        await client.process_commands(message)

client.run(TOKEN)
