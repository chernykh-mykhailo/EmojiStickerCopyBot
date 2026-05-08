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

def generate_suggestions(count: int = 4) -> list[str]:
    suggestions = set()
    while len(suggestions) < count:
        adj = random.choice(ADJECTIVES)
        noun = random.choice(NOUNS)
        suggestions.add(f"{adj} {noun}")
    return list(suggestions)
