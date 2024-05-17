class Team:
    def __init__(self, team_id, team_name, team_image_url=None, country_code=None):
        self.team_id = team_id
        self.team_name = team_name
        self.team_image_url = team_image_url
        self.country_code = country_code

    def to_dict(self):
        return {
            "team_id": self.team_id,
            "team_name": self.team_name,
            "team_image_url": self.team_image_url,
            "country_code": self.country_code
        }
