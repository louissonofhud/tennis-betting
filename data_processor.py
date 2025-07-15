import pandas as pd
import re

class TennisDataProcessor:
    def __init__(self, data):
        self.data = data

    @staticmethod
    def get_games_per_set(score):
        # Split sets by space
        sets = score.split()
        games = []
        for s in sets:
            # Remove tiebreak info in parentheses
            s_clean = re.sub(r'\(.*?\)', '', s)
            # Split by '-' and sum games
            if '-' in s_clean:
                try:
                    g1, g2 = map(int, s_clean.split('-'))
                    games.append(g1 + g2)
                except ValueError:
                    games.append(999)
        return games

    def derive_match_data(self):
        self.data.loc[:, "w_1stsv_acc"] =  self.data["w_1stIn"]/self.data["w_svpt"]
        self.data.loc[:, "l_1stsv_acc"] =  self.data["l_1stIn"]/self.data["l_svpt"]

        self.data.loc[:, "w_1stWon_pct"] = self.data["w_1stWon"]/self.data["w_1stIn"] 
        self.data.loc[:, "w_2ndWon_pct"] = self.data["w_2ndWon"]/(self.data["w_svpt"] - self.data["w_1stIn"]) 
        self.data.loc[:, "l_1stWon_pct"] = self.data["l_1stWon"]/self.data["l_1stIn"] 
        self.data.loc[:, "l_2ndWon_pct"] = self.data["l_2ndWon"]/(self.data["l_svpt"] - self.data["l_1stIn"])

        self.data.loc[:, "w_rt_won_pct"] = (self.data["l_svpt"] - (self.data["l_1stWon"] + self.data["l_2ndWon"]))/self.data["l_svpt"]
        self.data.loc[:, "l_rt_won_pct"] = (self.data["w_svpt"] - (self.data["w_1stWon"] + self.data["w_2ndWon"]))/self.data["w_svpt"]

        self.data.loc[:, "w_ace_rate"] = self.data["w_ace"]/self.data["w_svpt"]
        self.data.loc[:, "l_ace_rate"] = self.data["l_ace"]/self.data["l_svpt"]

        self.data.loc[:, "w_df_rate"] = self.data["w_df"]/self.data["w_svpt"]
        self.data.loc[:, "l_df_rate"] = self.data["l_df"]/self.data["l_svpt"]

        self.data.loc[:, "games_per_set"] = self.data["score"].apply(self.get_games_per_set)
        self.data.loc[:, "total_games"] = self.data["games_per_set"].apply(sum)
        self.data.loc[:, "set_count"] = self.data["score"].apply(lambda x: x.split()).apply(len)

        self.data.loc[:, "tiebreak_count"] = self.data["games_per_set"].apply(lambda x: x.count(13))

        filtered_data = self.data[
                            [
                                'tourney_id',
                                'tourney_name',
                                'surface',
                                'tourney_level',
                                'tourney_date',
                                'winner_name',
                                'loser_name',
                                "best_of",
                                "round",
                                "w_rt_won_pct",
                                "l_rt_won_pct",
                                "w_1stsv_acc",
                                "l_1stsv_acc",
                                "w_1stWon_pct",
                                "l_1stWon_pct",
                                "w_2ndWon_pct",
                                "l_2ndWon_pct",
                                "w_ace_rate",
                                "l_ace_rate",
                                "w_df_rate",
                                "l_df_rate",
                                'games_per_set',
                                'set_count',
                                'tiebreak_count',
                                "total_games",
                                "winner_rank_points",
                                "loser_rank_points",
                            ]
                        ]
        filtered_data = filtered_data.dropna(axis=0)

        return filtered_data
