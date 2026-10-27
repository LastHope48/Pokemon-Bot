import discord
from discord.ext import commands
from config import token
from logic import Pokemon

# Bot için yetkileri/intents ayarlama
intents = discord.Intents.default()  # Varsayılan ayarların alınması
intents.messages = True              # Botun mesajları işlemesine izin verme
intents.message_content = True       # Botun mesaj içeriğini okumasına izin verme
intents.guilds = True                # Botun sunucularla çalışmasına izin verme

# Tanımlanmış bir komut önekine ve etkinleştirilmiş amaçlara sahip bir bot oluşturma
bot = commands.Bot(command_prefix='!', intents=intents)

# Bot çalışmaya hazır olduğunda tetiklenen bir olay
@bot.event
async def on_ready():
    print(f'Giriş yapıldı:  {bot.user.name}')  # Botun adını konsola çıktı olarak verir

# '!go' komutu
@bot.command(help="Size bir Pokemon oluşturur.")
async def go(ctx):
    author = ctx.author.name  # Mesaj yazarının adını alma
    # Kullanıcının zaten bir Pokémon'u olup olmadığını kontrol edin. Eğer yoksa, o zaman...
    if author not in Pokemon.pokemons.keys():

        pokemon = Pokemon(author)  # Yeni bir Pokémon oluşturma
        await pokemon.get_data()
        pokemon.evolutions = await pokemon.get_evolutions()

        await ctx.send(await pokemon.info())  # Pokémon hakkında bilgi gönderilmesi

        image_url = await pokemon.show_img()  # Pokémon resminin URL'sini alma

        if image_url:
            embed = discord.Embed()  # Gömülü mesajı oluşturma
            embed.set_image(url=image_url)  # Pokémon'un görüntüsünün ayarlanması
            await ctx.send(embed=embed)  # Görüntü içeren gömülü bir mesaj gönderme
        else:
            await ctx.send("Pokémonun görüntüsü yüklenemedi!")
    else:
        await ctx.send("Zaten kendi Pokémonunuzu oluşturdunuz!")  # Bir Pokémon'un daha önce oluşturulup oluşturulmadığını gösteren bir mesaj

@bot.command(help="Pokemonunuzu besler.")
async def gofeed(ctx):
    author = ctx.author.name

    if author not in Pokemon.pokemons.keys():
        await ctx.send("Pokemonunuzu oluşturmadınız!\n!go Komuduyla oluşturabilirsiniz.")
        return

    pokemon = Pokemon.pokemons.get(author)
    await pokemon.feed_pokemon()

    await ctx.send(f"Pokemonunuzu beslediniz! Şuanki beslenme sayacı: {pokemon.feed}")

@bot.command(help="Pokemonunuzun bilgilerini verir.")
async def goinfo(ctx):
    author = ctx.author.name

    if author in Pokemon.pokemons.keys():
        pokemon = Pokemon.pokemons.get(author)

        await ctx.send(await pokemon.info())  # Pokémon hakkında bilgi gönderilmesi

        image_url = await pokemon.show_img()  # Pokémon resminin URL'sini alma

        if image_url:
            embed = discord.Embed()  # Gömülü mesajı oluşturma
            embed.set_image(url=image_url)  # Pokémon'un görüntüsünün ayarlanması
            await ctx.send(embed=embed)  # Görüntü içeren gömülü bir mesaj gönderme
        else:
            await ctx.send("Pokémonun görüntüsü yüklenemedi!")

    else:
        await ctx.send("Pokemonunuzu oluşturmadınız!\n!go Komuduyla oluşturabilirsiniz.")

@bot.command(help="Pokemonunuz ile bir kullanıcıya saldırın.")
async def goattack(ctx):
    author = ctx.author.name

    if author not in Pokemon.pokemons.keys():
        await ctx.send("Pokemonunuz yok!")
        return

    enemy = ctx.message.mentions[0] if ctx.message.mentions else None

    if enemy is None:
        await ctx.send("Bir kişi etiketleyin!")
        return

    enemy = Pokemon.pokemons.get(enemy.name)

    pokemon = Pokemon.pokemons.get(author)

    attack_message = await pokemon.attack(enemy)

    await ctx.send(attack_message)

@bot.command(help="Pokemon'unuzu sıfırlar.")
async def goreset(ctx):
    del Pokemon.pokemons[ctx.author.name]
    await ctx.send("Pokemon'unuz sıfırlandı!")

# Botun çalıştırılması
bot.run(token)
