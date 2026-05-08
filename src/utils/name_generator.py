import random

ADJECTIVES = [
    "Neon", "Quantum", "Space", "Golden", "Epic", "Turbo", "Mega", "Cyber",
    "Magic", "Super", "Ultra", "Retro", "Future", "Cosmic", "Prime", "Elite",
    "Giga", "Dark", "Light", "Shadow", "Fire", "Ice", "Thunder", "Zen"
]

NOUNS = [
    "Cats", "Memes", "Vibes", "Pack", "Stickers", "Emoji", "Cloud", "Star",
    "World", "Zone", "Gems", "Legends", "Heroes", "Squad", "Kings", "Masters",
    "Lab", "Studio", "Draft", "Box", "Collection", "Vault", "Nexus", "Core"
]

class NameGenerator:
    @staticmethod
    def get_random_suggestions(count: int = 4, exclude_titles: list[str] = None) -> list[str]:
        if exclude_titles is None:
            exclude_titles = []
            
        suggestions = set()
        attempts = 0
        # Normalizing exclude list for comparison
        exclude_set = {t.lower().strip() for t in exclude_titles}
        
        while len(suggestions) < count and attempts < 100:
            attempts += 1
            adj = random.choice(ADJECTIVES)
            noun = random.choice(NOUNS)
            title = f"{adj} {noun}"
            
            if title.lower().strip() not in exclude_set:
                suggestions.add(title)
                
        return list(suggestions)
