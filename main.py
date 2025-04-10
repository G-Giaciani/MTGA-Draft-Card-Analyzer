import pandas as pd
import requests
import time
import numpy as np
from urllib.parse import quote
import matplotlib.pyplot as plt
import random
import json
import os
import time 

start_time = time.time()

chunk_start_time = time.time()
MAX_CHUNKS = 170
chunk_iterator = pd.read_csv("game_data_public.DFT.PremierDraft.csv", chunksize=1000)

chunks = []
for i, chunk in enumerate(chunk_iterator):
    if i >= MAX_CHUNKS:
        break
    chunks.append(chunk)

dataset_17lands = pd.concat(chunks)
chunk_end_time = time.time()
chunk_time = chunk_end_time - chunk_start_time


SET_CODE = 'dft'  
RARITY = ''  

def get_cards_by_set_and_rarity(set_code, rarity):

    cache_file = f"cache_{set_code}_{rarity}.json"
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return json.load(f)
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
    with open(cache_file, 'w') as f:
        json.dump(all_cards, f)
        
    return all_cards

def calculate_card_stats(dataset, cards, synergy_card, min_samples=100):
    results = {}

    synergy_condition = (dataset[f"opening_hand_{synergy_card}"] + dataset[f"drawn_{synergy_card}"]) > 0
    
    for card in cards:
        try:

            card_condition = (dataset[f"opening_hand_{card}"] + dataset[f"drawn_{card}"]) > 0

            card_data = dataset[card_condition]
            if len(card_data) == 0:
                continue

            synergy_data = dataset[card_condition & synergy_condition]
            if len(synergy_data) < min_samples:
                continue
                
            results[card] = {
                'GIH_wr': card_data["won"].mean(),
                'GIH_wr_synergy': synergy_data["won"].mean(),
                'n_GIH_synergy': len(synergy_data)
            }
        except KeyError:
            continue
        
    return pd.DataFrame.from_dict(results, orient='index')


api_start_time = time.time()
commons = get_cards_by_set_and_rarity(SET_CODE, 'common')
uncommons = get_cards_by_set_and_rarity(SET_CODE, 'uncommon')
api_end_time = time.time()
api_time = api_end_time - api_start_time
non_rares = commons + uncommons

synergy_card = random.choice(non_rares)
min_sample_size = 100

calc_start_time = time.time()
plotDataFrame = calculate_card_stats(dataset_17lands, non_rares, synergy_card, min_sample_size)
calc_end_time = time.time()
calc_time = calc_end_time - calc_start_time

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

end_time = time.time()
execution_time = end_time - start_time

print(f"\nTempo para buscar cartas: {api_time:.2f} segundos")
print(f"Tempo para calcular estatísticas: {calc_time:.2f} segundos")
print(f"Tempo total de execução: {execution_time:.2f} segundos")
print(f"Chunk time: {chunk_time:.2f} segundos")