import discord
import os
import asyncio
import time
from pytube import YouTube
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
is_paused = False

def play_next_song(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    #Queue is not empty 
    if len(queue) >= 1:
        newSong = queue.pop(0)
        #The next song is an mp3 file 
        if str(newSong).endswith(".mp3"): 
            source = discord.FFmpegOpusAudio(newSong)
            asyncio.run_coroutine_threadsafe(ctx.send("Now playing..." + newSong),client.loop)
        #The next song was either a youtube link or a search
        else: 
            source = newSong
            asyncio.run_coroutine_threadsafe(ctx.send("Now playing..." + str(source)),client.loop)
        voice.play(source,after=lambda f: play_next_song(ctx))

def search_yt(item):
    with YoutubeDL(ydlOptions) as ydl:
        try:
            info = ydl.extract_info("ytsearch:%s" % item,download=False)["entries"][0]
        except:
            return False
    return info["formats"][0]["url"]

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
    if not voice.is_playing() and len(queue) == 0 and not url.startswith("https://www.youtube.com") and len(ctx.message.content) == 0:
        #Checks if the user uploaded a file
        if len(ctx.message.attachments) == 0:
            await ctx.send("No file was attached/no link was provided")
        else:
            filename = ctx.message.attachments[0].filename
            await ctx.message.attachments[0].save(cwd + '/' + filename)
            source = discord.FFmpegOpusAudio(filename)
            await ctx.send("Now playing... " + filename)
            voice.play(source,after=lambda f: play_next_song(ctx))
    #If the user sent a youtube link
    elif url.startswith("https://www.youtube.com") and len(queue) == 0 and not voice.is_playing():
        with youtube_dl.YoutubeDL(ydlOptions) as ydl:
            info = ydl.extract_info(url,download=False)
            newUrl = info['formats'][0]['url']
            source = await discord.FFmpegOpusAudio.from_probe(newUrl,**ffmpegOptions)
            await ctx.send("Now playing... " + YouTube(url).title)
            voice.play(source,after=lambda f: play_next_song(ctx))
    #If user sent a link but a song is currently playing 
    elif url.startswith("https://www.youtube.com") and len(queue) >= 0 and not is_paused: 
        with youtube_dl.YoutubeDL(ydlOptions) as ydl:
            info = ydl.extract_info(url,download=False)
            newUrl = info['formats'][0]['url']
            source = await discord.FFmpegOpusAudio.from_probe(newUrl,**ffmpegOptions)
            queue.append(source)    
            await ctx.send(YouTube(url).title + " has been added to the queue")
    #If a user enters the title of a song 
    elif not url.startswith("https://www.youtube.com") and len(queue) == 0 and not voice.is_playing():
        song = ctx.message.content[5::]
        source = discord.FFmpegOpusAudio(search_yt(song),**ffmpegOptions)
        voice.play(source,after=lambda f: play_next_song(ctx))
        await ctx.send("Now playing... " + song)
    elif not url.startswith("https://www.youtube.com") and len(queue) >= 0 and voice.is_playing():
        song = ctx.message.content[5::]
        source = discord.FFmpegOpusAudio(search_yt(song),**ffmpegOptions)
        queue.append(source)    
        await ctx.send(song + " has been added to the queue")
    #Add the audio file to the queue
    else:
        filename = ctx.message.attachments[0].filename
        queue.append(filename)
        await ctx.send(filename + " has been added to the queue")
@client.command()
async def pause(ctx):
#Two cases: music is playing or no music is playing 
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice == None:
        await ctx.send("No audio being played")
    elif voice.is_playing():
        voice.pause()
        is_paused = True
    elif not voice.is_playing() and len(queue) > 0:
        await ctx.send("You can't pause a paused song")
    else:
        await ctx.send("Nothing is playing")
@client.command()
async def resume(ctx):
    voice = discord.utils.get(client.voice_clients,guild=ctx.guild)
    if voice == None:
        await ctx.send("No audio being played")
    elif voice.is_paused():
        voice.resume()
        is_paused = False
    elif not voice.is_paused() and len(queue) > 0:
        await ctx.send("You can't resume a playing song")
    else:
        await ctx.send("Nothing is playing")
@client.command()
async def skip(ctx):
    if len(queue) >= 0:
        voice = discord.utils.get(client.voice_clients,guild=ctx.guild)
        voice.stop()
        play_next_song(ctx)
    else:
        await ctx.send("The queue is empty")

with open("password.txt", "r") as token_file:
    TOKEN = token_file.read()
    print("Token file read")
    client.run(TOKEN)
client.run(TOKEN) 