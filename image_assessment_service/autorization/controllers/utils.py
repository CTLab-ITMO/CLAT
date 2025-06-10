import random

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from image_assessment_service.autorization.models.core import Role, Token, User
from image_assessment_service.autorization.models.database import get_db
from sqlalchemy import select
from sqlalchemy.orm import Session

api_key_scheme = APIKeyHeader(name="Authorization")

# Lists of adjectives and nouns
adjectives = [
    "Happy", "Mysterious", "Brave", "Clever", "Swift", "Gentle", "Fierce", "Witty", "Calm", "Energetic",
    "Lucky", "Bright", "Silent", "Wild", "Noble", "Jolly", "Daring", "Radiant", "Vivid", "Zesty"
]

red_book_animals = [
    "AmurLeopard", "SnowLeopard", "SiberianTiger", "RedPanda", "GiantPanda", "BlackRhino", "SumatranOrangutan",
    "MountainGorilla", "Vaquita", "SaigaAntelope", "CaliforniaCondor", "Kakapo", "PhilippineEagle", "SiberianCrane",
    "WhoopingCrane", "SpoonBilledSandpiper", "GreatIndianBustard", "ForestOwlet", "MadagascarFishEagle", "HawaiianCrow",
    "LeatherbackTurtle", "HawksbillTurtle", "KomodoDragon", "Gharial", "RadiatedTortoise", "MadagascarSpiderTortoise",
    "ChineseAlligator", "GalapagosGiantTortoise", "ArubaIslandRattlesnake", "JamaicanIguana", "Axolotl", "GoldenToad",
    "PanamanianGoldenFrog", "ChineseGiantSalamander", "MadagascarTomatoFrog", "CorroboreeFrog", "MountainChickenFrog",
    "HoustonToad", "PuertoRicanCrestedToad", "BooroolongFrog", "BluefinTuna", "ChinesePaddlefish", "EuropeanEel",
    "MekongGiantCatfish", "DevilsHolePupfish", "AtlanticSturgeon", "HumpheadWrasse", "Sawfish", "Coelacanth"
]

def generate_nickname():
    # Choose a random adjective and noun
    adjective = random.choice(adjectives)
    noun = random.choice(red_book_animals)

    # Combine them to create a nickname
    nickname = f"{adjective}{noun}"

    # Optional: Add a random number or special character for uniqueness
    if random.choice([True, False]):  # 50% chance to add a number
        nickname += str(random.randint(0, 99))
    elif random.choice([True, False]):  # 25% chance to add a special character
        nickname += random.choice(["#", "!", "*", "&"])

    return nickname


def get_current_user(
        token: str = Depends(api_key_scheme),
        db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = db.scalar(select(Token).where(Token.access_token == token))
    if not token:
        raise credentials_exception

    return token.user

def require_role(*role_name: str):
    def role_checker(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        role = db.query(Role).filter(
            Role.user_id == user.id,
            Role.name.in_(role_name)
        ).first()
        
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {' or '.join(role_name)} role"
            )
        return user
    
    return role_checker
