import aiohttp  # Eşzamansız HTTP istekleri için bir kütüphane
import random

import logging
import string

logger = logging.Logger(__name__, logging.INFO)

class Pokemon:
    info_template = string.Template(
        f'''
{"="*10}Pokemon Kartı{"="*10}
- İsim: $name
- ID: #$id
- Tipleri: $types
{"="*10}Pokemon Kartı{"="*10}
'''
    )
    pokemons = {}
    # Nesne başlatma (kurucu)

    def __init__(self, pokemon_trainer):
        self.pokemon_trainer = pokemon_trainer
        self.pokemon_number = random.randint(1, 1000)
        self.name = None
        self.element_types: list = None

        self.raw_data: dict = None
        if pokemon_trainer not in Pokemon.pokemons:
            Pokemon.pokemons[pokemon_trainer] = self
        else:
            self = Pokemon.pokemons[pokemon_trainer]

    async def get_data(self) -> dict | None:
        '''PokeAPI aracılığıyla pokemonun bütün verilerini alan asenkron metot. Bir istekte bütün verilere erişebilmek için.'''
        url = f"https://pokeapi.co/api/v2/pokemon/{self.pokemon_number}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status in [200, 302]:
                    data = await response.json()

                    self.raw_data = data
                    return data

                else:
                    logger.warning(f"PokeAPI returned status that is not 200 or 302: {response.status}. URL: {url}")

                    return None
                    

    async def get_name(self):
        '''PokeAPI aracılığıyla bir pokémonun adını almak için asenktron metot'''

        if self.raw_data is None:
            self.raw_data = await self.get_data()

        self.name = self.raw_data['forms'][0]['name']
        
        return self.name

    async def info(self):
        '''Pokémon hakkında bilgi döndüren bir metot'''
        if not self.name:
            self.name = await self.get_name()  # Henüz yüklenmemişse bir adın geri alınması

        if not self.element_types:
            self.element_types = await self.get_element_types()

        
        return Pokemon.info_template.substitute(
            name=self.name,
            id=self.pokemon_number,
            types=",".join([str(tip_d["type"]["name"]) for tip_d in self.element_types])
        )

    async def show_img(self):
        '''PokeAPI aracılığıyla bir pokémon görüntüsünün URL'sini almak için asenktron metot'''

        if self.raw_data is None:
            self.raw_data = await self.get_data()

        return self.raw_data['sprites']['other']['home']['front_default']

    async def get_element_types(self):
        '''PokeAPI aracılığıyla bir pokemonun element tiplerini almak için asenkron metot'''

        if self.raw_data is None:
            self.raw_data = await self.get_data()

        self.element_types = self.raw_data["types"]

        return self.element_types
