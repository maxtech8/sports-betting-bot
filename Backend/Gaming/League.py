class League:
    def __init__(self, league_id, league_name, country_code=None, league_image_url=None):
        self.league_id = league_id
        self.league_name = league_name
        self.league_image_url = league_image_url
        self.country_code = country_code

    def to_dict(self):
        return {
            "league_id": self.league_id,
            "league_name": self.league_name,
            "league_image_url": self.league_image_url,
            "country_code": self.country_code
        }
