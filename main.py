import pandas as pd
import requests
import time
import numpy as np
from urllib.parse import quote
import matplotlib.pyplot as plt
import random

dataset_17lands = pd.read_csv('game_data_public.DFT.PremierDraft.csv', nrows=200000)
# dataset_17lands = dataset_17lands.head(100000)

# dataset_17lands = pd.read_csv('dataset_17lands_100000samples.csv')


SET_CODE = 'dft'  
RARITY = ''  

def get_cards_by_set_and_rarity(set_code, rarity):

    query = f"set:{quote(set_code)} rarity:{quote(rarity)}"
    url = f"https://api.scryfall.com/cards/search?q={quote(query)}"
    
    all_cards = []
    headers = {
        "User-Agent": "MTGCardFetcher/1.0",  
        "Accept": "application/json"
    }
    
    try:
        while url:

            time.sleep(0.1)  
            
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()  
                
                data = response.json()
                all_cards.extend([card["name"] for card in data["data"]])
                
               
                url = data.get("next_page")
                
            except requests.exceptions.RequestException as e:
                print(f"Erro na requisição: {e}")
                print(f"URL falha: {url}")
                break
                
    except KeyboardInterrupt:
        print("\nBusca interrompida pelo usuário")
    
    return all_cards


commons = get_cards_by_set_and_rarity(SET_CODE, 'common')
uncommons = get_cards_by_set_and_rarity(SET_CODE, 'uncommon')
non_rares = commons + uncommons


df_cards = pd.DataFrame(commons, columns=['card_name'])
df_cards_uncummons = pd.DataFrame(uncommons, columns=['card_name'])

synergy_card = random.choice(non_rares)
min_sample_size = 100

GIH_wr = []
GIH_wr_synergy = []
GIH_names = []
n_GIH_synergy = []

for card in non_rares:
    dataset_17lands_GIH = dataset_17lands[(dataset_17lands["opening_hand_"+card] + dataset_17lands["drawn_"+card]) > 0]
    dataset_17lands_GIH_syn = dataset_17lands[((dataset_17lands["opening_hand_"+card] + dataset_17lands["drawn_"+card]) > 0) & ((dataset_17lands["opening_hand_"+synergy_card] + dataset_17lands["drawn_"+synergy_card]) > 0)]
    if len(dataset_17lands_GIH_syn) >= min_sample_size:
        GIH_wr.append(dataset_17lands_GIH["won"].mean())
        GIH_wr_synergy.append(dataset_17lands_GIH_syn["won"].mean())
        GIH_names.append(card)
        n_GIH_synergy.append(len(dataset_17lands_GIH_syn))
    plotDataFrame = pd.DataFrame(list(zip(GIH_wr, GIH_wr_synergy, n_GIH_synergy)), columns=["GIH_wr", "GIH_wr_synergy", "n_GIH_synergy"])
    plotDataFrame.index = GIH_names


my_cards = []
for i in range(15):
    card = random.choice(non_rares)
    if card in plotDataFrame.index:
        my_cards.append(card)
    else:
        i = i - 1

print(f"\nCarta sinergia: {synergy_card}")

for cards in my_cards:
    if cards in plotDataFrame.index:
        wr_geral = plotDataFrame.loc[cards, 'GIH_wr']
        wr_sinergia = plotDataFrame.loc[cards, 'GIH_wr_synergy']
        diff = wr_sinergia - wr_geral
        num_games = plotDataFrame.loc[cards, 'n_GIH_synergy']
        
        print(f"\n{cards}:")
        print(f"  Winrate Geral: {wr_geral:.2%}")
        print(f"  Winrate com {synergy_card}: {wr_sinergia:.2%}")
        print(f"  Diferença: {diff:+.2%}")
        print(f"  Amostra: {num_games}")
    else:
        print(f"A card {cards} nao foi encontrada no DataFrame.")
