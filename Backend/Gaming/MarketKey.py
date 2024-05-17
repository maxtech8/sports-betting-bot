from Gaming.ResultsInterpreterFunctionsFactory import ResultsInterpreterFunctionsFactory

from enum import Enum


class MarketKeysMapping(Enum):
    FULL_TIME_RESULT = "1X2, Full Time Result"
    ASIAN_HANDICAP = "Asian Handicap"
    GOAL_LINE = "O/U, Goal Line"
    ASIAN_CORNERS = "Asian Corners"
    FIRST_HALF_ASIAN_HANDICAP = "1st Half Asian Handicap"
    FIRST_HALF_GOAL_LINE = "1st Half Goal Line"
    FIRST_HALF_ASIAN_CORNERS = "1st Half Asian Corners"
    HALF_TIME_RESULT = "Half Time Result"
    MONEY_LINE = "Money Line"
    SPREAD = "Spread"
    TOTAL_POINTS = "Total Points"
    MONEY_LINE_HALF = "Money Line (Half)"
    SPREAD_HALF = "Spread (Half)"
    TOTAL_POINTS_HALF = "Total Points (Half)"
    QUARTER_WINNER_2WAY = "Quarter - Winner (2-Way)"
    QUARTER_HANDICAP = "Quarter - Handicap"
    QUARTER_TOTAL_2WAY = "Quarter - Total (2-Way)"
    MATCH_WINNER_2WAY = "Match Winner 2-Way"
    ASIAN_HANDICAP_2 = "Asian Handicap"
    OVER_UNDER = "Over/Under"
    DRAW_NO_BET_CRICKET = "Draw No Bet (Cricket)"


class MarketKey:
    def __init__(self, market_key_name: str, odds: list):
        self.market_key_name = market_key_name
        self._odds = odds
        self.results_interpreter_function = ResultsInterpreterFunctionsFactory.get_results_interpreter_function(
            market_key_name)

    def get_winner(self, scores):
        winner_odd_id = self.results_interpreter_function(scores)
        return winner_odd_id

    def get_odds(self):
        return self._odds

    def set_odds(self, odds: list):
        self._odds = odds

    def to_dict(self):
        return {
            "market_key_name": self.market_key_name,
            "odds": [odd.to_dict() for odd in self._odds] if self._odds else []
            # You might need to add additional attributes here based on serialization requirements
        }
