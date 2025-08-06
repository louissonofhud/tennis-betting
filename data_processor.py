import pandas as pd
import re

class TennisDataProcessor:
    ROUND_ORDER = ["RR", "R128", "R64", "R32", "R16", "QF", "SF", "F"]
    def __init__(self, data):
        self.data = data

    @staticmethod
    def get_games_per_set(score: str) -> list:
        # Split sets by space
        sets = score.split()
        games = []
        for s in sets:
            # Remove tiebreak info in parentheses
            s_clean = re.sub(r'\(.*?\)', '', s)
            s_clean = re.sub(r'\[.*?\]', '', s_clean)
            # Split by '-' and sum games
            if '-' in s_clean:
                try:
                    g1, g2 = map(int, s_clean.split('-'))
                    games.append(g1 + g2)
                except ValueError:
                    games.append(999)
        return games

    def derive_match_data(self) -> pd.DataFrame:
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

        self.data.loc[:, "games_in_sets"] = self.data["score"].apply(self.get_games_per_set)
        self.data.loc[:, "total_games"] = self.data["games_in_sets"].apply(sum)
        self.data.loc[:, "set_count"] = self.data["score"].apply(lambda x: x.split()).apply(len)

        self.data.loc[:, "tiebreak_count"] = self.data["games_in_sets"].apply(lambda x: x.count(13))
        self.data.loc[:, "gps"] = self.data["total_games"] / self.data["set_count"]

        filtered_data = self.data[
                            [
                                'tourney_id',
                                "match_num",
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
                                'games_in_sets',
                                "score",
                                'set_count',
                                'tiebreak_count',
                                "total_games",
                                "gps",
                                "winner_rank_points",
                                "loser_rank_points",
                            ]
                        ]
        filtered_data = filtered_data.dropna(axis=0)
        filtered_data.loc[:, "advantage_set"] = filtered_data["games_in_sets"].apply(lambda x: x[-1] > 13)
        filtered_data["tourney_date"] = pd.to_datetime(filtered_data["tourney_date"], format="%Y%m%d")
        filtered_data = filtered_data.loc[filtered_data["round"].isin(["RR", "R128", "R64", "R32", "R16", "QF", "SF", "F"])]
        filtered_data["round"] = pd.Categorical(filtered_data["round"], categories=TennisDataProcessor.ROUND_ORDER, ordered=True)
        filtered_data = filtered_data.rename(columns={
            "winner_rank_points": "w_rank_points",
            "loser_rank_points": "l_rank_points"
        })




        return filtered_data

MATCH_KEYS = ['surface', 'tourney_level', 'tourney_date', 'tourney_name', 'round', 'best_of', "match_num"]
def to_player(name: str, derived_data: pd.DataFrame) -> pd.DataFrame:
    player_matches = derived_data[
        (derived_data["winner_name"] == name) | (derived_data["loser_name"] == name)
    ].copy()

    player_matches["result"] = player_matches["winner_name"].apply(lambda x: "win" if x == name else "loss")
    player_matches["player_name"] = name
    player_matches["opponent_name"] = player_matches.apply(
        lambda row: row["loser_name"] if row["winner_name"] == name else row["winner_name"], axis=1
    )

    stat_fields = [col for col in derived_data.columns if col.startswith("w_") or col.startswith("l_")]
    stat_names = list(set(col[2:] for col in stat_fields))  # Remove 'w_' or 'l_' prefix    

    for stat in stat_names:
        player_matches[f"player_{stat}"] = player_matches.apply(
            lambda row: row[f"w_{stat}"] if row["result"] == "win" else row[f"l_{stat}"], axis=1
        )
        player_matches[f"opponent_{stat}"] = player_matches.apply(
            lambda row: row[f"l_{stat}"] if row["result"] == "win" else row[f"w_{stat}"], axis=1
        )

    player_matches = player_matches.drop(columns=[
        col for col in player_matches.columns if col.startswith(("w_", "l_", "winner_", "loser_"))
    ])
    
    cols = ['tourney_date', "match_num", 'tourney_name', 'surface', 'round', 'result', "tourney_level", "best_of", "games_in_sets", "set_count", "tiebreak_count", "total_games", "gps"]

    cols += [col for col in player_matches.columns if col.startswith('player_')]
    cols += [col for col in player_matches.columns if col.startswith('opponent_')]

    return player_matches[cols].sort_values(by=["tourney_date", "round"], ascending=[True, True]).reset_index(drop=True)



def to_average(player_matches: pd.DataFrame, lookback: int=10) -> pd.DataFrame:
    stats_cols = [col for col in player_matches.columns if col.startswith("player_") and (col.endswith("_pct") or col.endswith("_rate") or col.endswith("_acc"))]
    for col in stats_cols:
        player_matches[col + "_avg"] = player_matches[col].rolling(lookback).mean().shift(1) # maybe median here? Markov chain?
    cols = [
        "surface",
        "match_num",
        "tourney_level",
        "tourney_date",
        "tourney_name",
        "round",
        "best_of",
        "player_name",
        "player_rank_points",
        "opponent_name",    
    ]

    for col in stats_cols:
        cols += [col, col + "_avg"]

    cols += ["result", "set_count", "tiebreak_count", "games_in_sets", "total_games", "gps"]

    return player_matches[cols]

def get_fatigue_stats(player_data: pd.DataFrame) -> pd.DataFrame:
    player_data = player_data.copy()
    player_data["games_played_tournament"] = (
        player_data.groupby(['tourney_name', 'tourney_date'], group_keys=False, )
        .apply(lambda group: group['total_games'].cumsum().shift(fill_value=0), include_groups=False)
    )

    dates = player_data["tourney_date"].to_numpy()
    games = player_data["total_games"].to_numpy()
    result = []
    start = 0
    for i in range(len(player_data)):
        while dates[i] - dates[start] > pd.Timedelta(days=30):
            start += 1
        result.append(games[start:i].sum())
    player_data["games_played_last_30_days"] = result     

    return player_data

def reorder_players(row):
    if row['result_player1'] == 'win':
        winner = {f'winner_{col.replace("_player1", "")}': row[col] for col in row.index if '_player1' in col}
        loser = {f'loser_{col.replace("_player2", "")}': row[col] for col in row.index if '_player2' in col}
    else:
        winner = {f'winner_{col.replace("_player2", "")}': row[col] for col in row.index if '_player2' in col}
        loser = {f'loser_{col.replace("_player1", "")}': row[col] for col in row.index if '_player1' in col}

    match_data = {key: row[key] for key in MATCH_KEYS}
    return pd.Series({**match_data, **winner, **loser})

def merge_tables(list_of_dfs):
    concat_tables = pd.concat(list_of_dfs)
    duplicated = pd.merge(
        concat_tables,
        concat_tables,
        on=MATCH_KEYS,
        suffixes=('_player1', '_player2'),
        how='inner'
    )
    deduped = duplicated.loc[duplicated['player_name_player1'] != duplicated['player_name_player2']]
    deduped = deduped[
        deduped['player_name_player1'] < deduped['player_name_player2']
    ].apply(reorder_players, axis=1)
    
    return deduped[[
        'surface',
        "match_num",
        'tourney_level',
        'tourney_date',
        'tourney_name',
        'round',
        'best_of',
        'winner_player_name',
        'winner_player_rank_points',
        'winner_player_ace_rate',
        'winner_player_ace_rate_avg',
        'winner_player_df_rate',
        'winner_player_df_rate_avg',
        'winner_player_1stWon_pct',
        'winner_player_1stWon_pct_avg',
        'winner_player_2ndWon_pct',
        'winner_player_2ndWon_pct_avg',
        'winner_player_1stsv_acc',
        'winner_player_1stsv_acc_avg',
        'winner_player_rt_won_pct',
        'winner_player_rt_won_pct_avg',
        'winner_games_played_tournament',
        'winner_games_played_last_30_days',
        'loser_player_name',
        'loser_player_rank_points',
        'loser_player_ace_rate',
        'loser_player_ace_rate_avg',
        'loser_player_df_rate',
        'loser_player_df_rate_avg',
        'loser_player_1stWon_pct',
        'loser_player_1stWon_pct_avg',
        'loser_player_2ndWon_pct',
        'loser_player_2ndWon_pct_avg',
        'loser_player_1stsv_acc',
        'loser_player_1stsv_acc_avg',
        'loser_player_rt_won_pct',
        'loser_player_rt_won_pct_avg',
        'loser_games_played_tournament', 
        'loser_games_played_last_30_days', 
        'winner_set_count', # keep dupe
        'winner_tiebreak_count', # keep dupe
        'winner_games_in_sets', # keep dupe
        'winner_total_games', # keep dupe
        'winner_gps', # keep dupe
    ]].rename(columns={
        col:col.replace("player_", "") for col in deduped.columns
    } | {'winner_set_count':"set_count",
        'winner_tiebreak_count':"tiebreak_count",
        'winner_games_in_sets':"games_in_sets",
        'winner_total_games':"total_games",
        'winner_gps':"gps"})