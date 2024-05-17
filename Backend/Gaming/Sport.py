class Sport:
    def __init__(self, sport_id, sport_name):
        self.sport_id = sport_id
        self.sport_name = sport_name

    def to_dict(self):
        return {
            "sport_id": self.sport_id,
            "sport_name": self.sport_name
            # Add more attributes if needed for serialization
        }