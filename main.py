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
import mplcursors

start_time = time.time()

chunk_start_time = time.time()
MAX_CHUNKS = 50
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
                print(f"Request failed: {e}")
                print(f"URL: {url}")
                break
                
    except KeyboardInterrupt:
        print("\Search interrupted by user.")
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

#Selecting synergy card
synergy_card = "Boom Scholar"
min_sample_size = 200

calc_start_time = time.time()
plotDataFrame = calculate_card_stats(dataset_17lands, non_rares, synergy_card, min_sample_size)
calc_end_time = time.time()
calc_time = calc_end_time - calc_start_time

my_cards = []
#Selecting random cards for test purposes
# for i in range(15):
#     card = random.choice(non_rares)
#     if card in plotDataFrame.index:
#         my_cards.append(card)
#     else:
#         i = i - 1

print(f"\Synergy Card: {synergy_card}")

for cards in my_cards:
    if cards in plotDataFrame.index:
        wr_geral = plotDataFrame.loc[cards, 'GIH_wr']
        wr_sinergia = plotDataFrame.loc[cards, 'GIH_wr_synergy']
        diff = wr_sinergia - wr_geral
        num_games = plotDataFrame.loc[cards, 'n_GIH_synergy']
        
        print(f"\n{cards}:")
        print(f"  Winrate: {wr_geral:.2%}")
        print(f"  Winrate with {synergy_card}: {wr_sinergia:.2%}")
        print(f"  Difference: {diff:+.2%}")
        print(f"  Samples: {num_games}")
    else:
        print(f"A card {cards} nao foi encontrada no DataFrame.")

end_time = time.time()
execution_time = end_time - start_time

print(f"\Time to make API request: {api_time:.2f} seconds")
print(f"Time to calculate stats: {calc_time:.2f} seconds")
print(f"Total execution time: {execution_time:.2f} seconds")
print(f"Chunk time: {chunk_time:.2f} seconds")


plt.figure(figsize=(12, 8))


min_wr = min(plotDataFrame['GIH_wr'].min(), plotDataFrame['GIH_wr_synergy'].min())
max_wr = max(plotDataFrame['GIH_wr'].max(), plotDataFrame['GIH_wr_synergy'].max())
plt.plot([min_wr, max_wr], [min_wr, max_wr], 'k--', alpha=0.3, label='Same Win Rate')


scatter = plt.scatter(
    plotDataFrame['GIH_wr'], 
    plotDataFrame['GIH_wr_synergy'],
    s=np.sqrt(plotDataFrame['n_GIH_synergy']) * 2,  
    alpha=0.7,
    c=plotDataFrame['GIH_wr_synergy'] - plotDataFrame['GIH_wr'], 
    cmap='coolwarm'
)

cursor = mplcursors.cursor(scatter, hover=True)

@cursor.connect("add")
def on_add(sel):
    index = sel.index
    card_name = plotDataFrame.index[index]
    sel.annotation.set(text=card_name)
    sel.annotation.get_bbox_patch().set(fc="white", alpha=0.8)

cbar = plt.colorbar(scatter)
cbar.set_label('Difference in Win Rate (Synergy - Original)')

for card in my_cards:
    if card in plotDataFrame.index:
        plt.scatter(
            plotDataFrame.loc[card, 'GIH_wr'],
            plotDataFrame.loc[card, 'GIH_wr_synergy'],
            s=150,  
            facecolors='none',  
            edgecolors='black', 
            linewidth=2
        )


plt.title(f'Card performance with and without "{synergy_card}"', fontsize=14)
plt.xlabel('Original Win Rate (GIH_wr)', fontsize=12)
plt.ylabel(f'Win Rate with {synergy_card} (GIH_wr_synergy)', fontsize=12)


plt.grid(True, alpha=0.3)


sizes = [min(plotDataFrame['n_GIH_synergy']), 
         plotDataFrame['n_GIH_synergy'].median(), 
         max(plotDataFrame['n_GIH_synergy'])]
labels = [f'n={int(s)}' for s in sizes]
for i, size in enumerate(sizes):
    plt.scatter([], [], s=np.sqrt(size)*2, c='gray', alpha=0.7, label=labels[i])


plt.scatter([], [], s=150, facecolors='none', edgecolors='black', linewidth=2, label='Cartas Selecionadas')

plt.legend(title='Tamanho da Amostra', loc='lower right')
plt.axis('equal')
plt.tight_layout()
plt.show()