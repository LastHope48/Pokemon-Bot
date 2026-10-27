import aiohttp  # Eşzamansız HTTP istekleri için bir kütüphane
import random

import logging
import string

URL = r"https://pokeapi.co/api/v2/pokemon"

logger = logging.Logger(__name__, logging.INFO)


class Pokemon:
    info_template = string.Template(
        f'''
{"="*10}Pokemon Kartı{"="*10}
- İsim: $name
- ID: #$id
- Can: $hp HP

- Power: $power
- Tipleri: $types
{"="*10}Pokemon Kartı{"="*10}
'''
    )
    pokemons: dict[str, "Pokemon"] = {}
    # Nesne başlatma (kurucu)

    def __init__(self, pokemon_trainer):
        self.pokemon_trainer = pokemon_trainer
        self.pokemon_number = random.randint(1, 1000)
        self.name = None
        self.element_types: list = None
        self.feed = 0
        self.old_feed = self.feed
        self.evolutions = None

        # Hp ve Power
        self.hp = random.randint(50, 300)
        self.power = random.randint(20, 60)

        self.raw_data: dict = None
        if pokemon_trainer not in Pokemon.pokemons:
            Pokemon.pokemons[pokemon_trainer] = self
        else:
            self = Pokemon.pokemons[pokemon_trainer]

    async def get_data(self) -> dict | None:
        '''PokeAPI aracılığıyla pokemonun bütün verilerini alan asenkron metot. Bir istekte bütün verilere erişebilmek için.'''
        url = f"{URL}/{self.pokemon_number}"

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

        
        return Pokemon.info_template.safe_substitute(
            name=self.name,
            id=self.pokemon_number,
            types=",".join([str(tip_d["type"]["name"]) for tip_d in self.element_types]),
            hp=self.hp,
            power=self.power
        )

    async def get_evolutions(self) -> list[str]:
        '''Mevcut Pokémon'un sonraki evrimlerinin isim listesini çeker.'''
        if not self.name:
            await self.get_name()

        async with aiohttp.ClientSession() as session:
            # 1. Species bilgisinden evolution_chain URL'sini al
            species_url = f"{URL}/pokemon-species/{self.name.lower()}"
            async with session.get(species_url) as resp:
                if resp.status != 200:
                    return []
                species_data = await resp.json()
                evo_chain_url = species_data.get("evolution_chain", {}).get("url")

            if not evo_chain_url:
                return []

            # 2. Evrim zinciri verisini al
            async with session.get(evo_chain_url) as resp:
                if resp.status != 200:
                    return []
                chain_data = await resp.json()

            # 3. Zincir ağacından sıradaki evrimleri düz listeye dök
            def extract_line(node) -> list[str]:
                chain_list = [node["species"]["name"]]
                if node.get("evolves_to"):
                    # İlk evrim kolunu takip eder
                    chain_list.extend(extract_line(node["evolves_to"][0]))
                return chain_list

            full_line = extract_line(chain_data["chain"])

            # Mevcut formdan sonraki formları listele
            try:
                current_idx = full_line.index(self.name.lower())
                self.evolutions = full_line[current_idx + 1:]
            except ValueError:
                self.evolutions = []

            return self.evolutions

    async def show_img(self) -> str:
        '''
        Besleme durumuna göre (feed) uygun evrimin görselini,
        yoksa temel Pokémon görselini döndürür.
        '''
        if self.raw_data is None:
            await self.get_data()

        # Eğer besleme yapılmışsa ve evrimleşebiliyorsa
        if self.feed > 0:
            if not self.evolutions:
                self.evolutions = await self.get_evolutions()

            # feed adımına denk gelen evrim var mı kontrol et (örneğin 1. beslemede ilk evrim)
            target_idx = self.feed - 1
            if target_idx < len(self.evolutions):
                target_pokemon = self.evolutions[target_idx]

                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{URL}/pokemon/{target_pokemon}") as p_resp:
                        if p_resp.status == 200:
                            p_data = await p_resp.json()
                            artwork = p_data["sprites"]["other"]["official-artwork"]["front_default"]
                            logging.info("Evrim görseli başarılı!")

                            return artwork or p_data["sprites"]["front_default"]

        # Varsayılan temel görsel (Home ya da Official Artwork)
        default_artwork = (
            self.raw_data['sprites']['other']['home']['front_default']
            or self.raw_data['sprites']['other']['official-artwork']['front_default']
            or self.raw_data['sprites']['front_default']
        )
        return default_artwork

    async def get_element_types(self):
        '''PokeAPI aracılığıyla bir pokemonun element tiplerini almak için asenkron metot'''

        if self.raw_data is None:
            self.raw_data = await self.get_data()

        self.element_types = self.raw_data["types"]

        return self.element_types

    async def feed_pokemon(self):
        self.feed += 1

    async def attack(self, enemy: "Pokemon"):
        if self.hp <= 0:
            return f"Pokemonunun canı 0!"
        
        enemy.hp = max(0, enemy.hp - self.power)

        if enemy.hp <= 0:
            return f"Pokemon eğitmeni @{self.pokemon_trainer}, Pokemon eğitmeni @{enemy.pokemon_trainer} yendi!"

        else:
            return f"Pokemon eğitmeni @{self.pokemon_trainer}, Pokemon eğitmeni @{enemy.pokemon_trainer} {self.power} vurdu! Kalan can: {enemy.hp}"


class Fighter(Pokemon):
    async def attack(self, enemy):
        super_power = random.randint(5, 15)
        self.power += super_power
        result = await super().attack(enemy)
        self.power -= super_power
        return result + f"\nDövüşçü Pokémon süper saldırı kullandı. Eklenen güç: {super_power}"

class Wizard(Pokemon):
    pass
