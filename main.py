import discord
import os
import asyncio
import time
import youtube_dl
from youtube_dl import YoutubeDL
from discord.ext import commands
from discord import FFmpegPCMAudio
import logging

logging.basicConfig(level=logging.INFO)
client = commands.Bot(command_prefix="!")
cwd = os.getcwd()
queue = []
ffmpegOptions = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'}
ydlOptions = {"format":"bestaudio"}

def play_next_song(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    queue.pop(0) #Removes the extra queue of the very first song
    #Queue is not empty 
    if len(queue) >= 1:
        newSong = queue.pop(0)
        source = discord.FFmpegOpusAudio(newSong)
        asyncio.run_coroutine_threadsafe(ctx.send("Now playing..." + newSong),client.loop)
        voice.play(source,after=lambda f: play_next_song(ctx))
    else:
        time.sleep(15)
        if not voice.is_playing():
            asyncio.run_coroutine_threadsafe(voice.disconnect(), client.loop)
            asyncio.run_coroutine_threadsafe(ctx.send("No more songs in queue."),client.loop)

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.command()
async def connect(ctx):
    #If the person isn't in vc 
    if ctx.author.voice == None:
        await ctx.send("Join a channel to summon me")
    channel = ctx.author.voice.channel.name
    vc = discord.utils.get(ctx.guild.voice_channels, name=channel)
    if ctx.voice_client == None:
        await vc.connect()
    #If the person moved to a different channel and wants to bring the bot
    else: 
        await ctx.voice_client.move_to(vc)
@client.command()
async def disconnect(ctx):
    vc = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if ctx.voice_client != None:
        await vc.disconnect()
    #If the bot isn't in vc 
    else:
        await ctx.send("I must be in vc to be disconnected")
@client.command()
async def play(ctx,url=None):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    #If the user uploaded an audio file 
    if not voice.is_playing() and len(queue) == 0 and url == None:
        #Checks if the user uploaded a file
        if len(ctx.message.attachments) == 0:
            await ctx.send("No file was attached")
        else:
            filename = ctx.message.attachments[0].filename
            await ctx.message.attachments[0].save(cwd + '/' + filename)
        source = discord.FFmpegOpusAudio(filename)
        queue.append(filename)
        await ctx.send("Now playing... " + filename)
        voice.play(source,after=lambda f: play_next_song(ctx))
    #If the user sent a youtube link
    elif url != None and len(queue) == 0 and not voice.is_playing():
        with youtube_dl.YoutubeDL(ydlOptions) as ydl:
            info = ydl.extract_info(url,download=False)
            title = info['track'] + ' by ' + info['artist']
            newUrl = info['formats'][0]['url']
            source = await discord.FFmpegOpusAudio.from_probe(newUrl,**ffmpegOptions)
            queue.append(str(source))
            await ctx.send("Now playing... " + title)
            voice.play(source,after=lambda f: play_next_song(ctx))
    elif url != None and len(queue) > 0: 
        with youtube_dl.YoutubeDL(ydlOptions) as ydl:
            info = ydl.extract_info(url,download=False)
            newUrl = info['formats'][0]['url']
            title = info['track'] + ' by ' + info['artist']
            source = await discord.FFmpegOpusAudio.from_probe(newUrl,**ffmpegOptions)
            queue.append(str(source))    
            await ctx.send(title + " has been added to the queue")
    #Add the audio file to the queue
    else:
        filename = ctx.message.attachments[0].filename
        queue.append(filename)
        await ctx.send(filename + " has been added to  the queue")
@client.command()
async def pause(ctx):
#Two cases: music is playing or no music is playing 
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice == None:
        await ctx.send("No audio being played")
    elif voice.is_playing():
        voice.pause()
    else:
        await ctx.send("You can't pause a paused song")
@client.command()
async def resume(ctx):
    voice = discord.utils.get(client.voice_clients,guild=ctx.guild)
    if voice == None:
        await ctx.send("No audio being played")
    elif voice.is_paused():
        voice.resume()
    else:
        await ctx.send("You can't resume a playing song")
with open("password.txt", "r") as token_file:
    TOKEN = token_file.read()
    print("Token file read")
    client.run(TOKEN)
client.run(TOKEN) 