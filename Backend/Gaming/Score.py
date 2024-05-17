class Score:
    def __init__(self, scores=None):
        self._team_id_score_pairs = {}
        if scores:
            self.set_scores(scores)

    def set_scores(self, scores):
        for score in scores:
            name = score["name"]
            score = score["score"]
            self._team_id_score_pairs[name] = score

    def get_scores(self):
        return self._team_id_score_pairs


    def to_dict(self):
        return self.get_scores()
