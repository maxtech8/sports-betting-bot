NOOP_BUTTON = ' '
PREVIOUS_BUTTON = "‹ Prev"
NEXT_BUTTON = "Next ›"
START_BUTTON = "«"
END_BUTTON = "»"
HOME_BUTTON = "🏠 Home"
BACK_BUTTON = '‹ Back'
SORT_BUTTON = "⇅ Sort"
CONTINUE_BUTTON = 'Continue »'
INSERT_PAGE = "✏️ Select page"
SHARE_BUTTON = "Share"

SELECT_ADDRESS_REGEX = "✏️ Enter (\w+) address"


def get_select_address_message(wallet_type):
    return f"✏️ Enter {wallet_type} address"


def get_sport_emoji(sport_name):
    sport_emojis = {
        "Soccer": "⚽",
        "Basketball": "🏀",
        "American Football": "🏈",
        "Baseball": "⚾",
        "Tennis": "🎾",
        "Volleyball": "🏐",
        "Table Tennis": "🏓",
        "Badminton": "🏸",
        "Rugby": "🏉",
        "Cricket": "🏏",
        "Hockey": "🏒",
        "Ice Hockey": "🏒",
        "Field Hockey": "🏑",
        "Bowling": "🎳",
        "Golf": "⛳",
        "Boxing": "🥊",
        "Martial Arts": "🥋",
        "Karate": "🥋",
        "Judo": "🥋",
        "Taekwondo": "🥋",
        "Wrestling": "🤼",
        "Fencing": "🤺",
        "Skiing": "⛷",
        "Snowboarding": "🏂",
        "Ice Skating": "⛸",
        "Cycling": "🚴",
        "Mountain Biking": "🚵",
        "Horse Racing": "🏇",
        "Swimming": "🏊",
        "Surfing": "🏄",
        "Diving": "🤿",
        "Snooker": "🎱",
        "Chess": "♟",
        "Darts": "🎯",
        "Gymnastics": "🤸",
        "Weightlifting": "🏋️",
        "Running": "🏃",
        "Track and Field": "🏟",
        "Sailing": "⛵",
        "Rowing": "🚣",
        "Kayaking": "🛶",
        "Skydiving": "🪂",
        "Rock Climbing": "🧗",
        "Skateboarding": "🛹",
        "Archery": "🏹",
        "Fishing": "🎣",
        "Yoga": "🧘"
    }

    return sport_emojis.get(sport_name, "🏆")  # Default emoji if the sport is not in the list
