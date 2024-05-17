from Gaming import MarketKey


class ResultsInterpreterFunctionsFactory:

    @staticmethod
    def get_results_interpreter_function(market_key_id):
        if market_key_id == MarketKey.MarketKeysMapping.FULL_TIME_RESULT.value or market_key_id == MarketKey.MarketKeysMapping.MATCH_WINNER_2WAY.value:
            return ResultsInterpreterFunctionsFactory.full_time_results_interpreter_function
        raise Exception(f"Not interpreter for market_key_id {market_key_id}")

    @staticmethod
    def full_time_results_interpreter_function(results):
        # {'Wolverhampton Wanderers': '0', 'Brighton and Hove Albion': '0'}
        max_score = max(results.values())
        winners = [team for team, score in results.items() if score == max_score]

        if len(winners) == len(results):
            return "Draw"
        else:
            return winners[0]

    @staticmethod
    def _example_results_interpreter_function(results):

        """
        :return: winning odd
        """
        return "TEST"
