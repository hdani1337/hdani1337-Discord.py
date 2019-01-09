import asyncio
import discord
import youtube_dl
from discord.ext import commands
from youtube_dl import YoutubeDL
youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
token = open("token.txt","r").read()

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            #Lejátssza az elsőt egy lejátszási listáról
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Music:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        #Csatlakozás a voice channelhez

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @commands.command()
    async def play(self, ctx, *, url):
        #Lejátszás YT-ről, de nem tölti le a videót (streamelés), ezzel sok tárhelyet megspórolva

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

        await ctx.send('Ezt nyomatom: {}'.format(player.title))

    @commands.command()
    async def stop(self, ctx):
        await ctx.voice_client.disconnect()

    @play.before_invoke
    @join.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("Nem csatlakozol egy csatornához sem.\nCsatlakozz egy csatornához, mielőtt zenét kérnél!")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()

bot = commands.Bot(command_prefix=commands.when_mentioned_or(".","alexa, "))
                   

@bot.event
async def on_ready():
    print(f"Musicbot készen áll.")

bot.add_cog(Music(bot))
bot.run(token)
