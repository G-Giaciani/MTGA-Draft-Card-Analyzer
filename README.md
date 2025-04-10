
# MTGA Card Synergy Analyzer

This tool analyzes card synergies in *Magic: The Gathering Arena* (MTGA) using draft data from 17Lands. It identifies cards that perform better when paired with a selected "synergy card" and visualizes the results.

## Features

- Fetches card data from Scryfall API for a specified set and rarity
- Uses 17Lands draft data to calculate win rates with and without a chosen synergy card
- Generates an interactive scatter plot to compare card performance:
  - X-axis: Base win rate (GIH_wr)
  - Y-axis: Win rate when paired with the synergy card (GIH_wr_synergy)
  - Bubble size: Sample size (number of games)
  - Color: Win rate difference (synergy - base)

## Requirements

- Required libraries:
  - pandas
  - numpy
  - requests
  - matplotlib
  - mplcursors

## Usage

1. **Configure the script**:
   - Set `SET_CODE` to the MTG set you want to analyze (e.g., `'dft'` for *AetherDrift*)
   - Set `synergy_card` to the card you want to analyze (e.g., `"Boom Scholar"`)
   - Adjust `min_sample_size` to filter out small sample sizes (default: `200`)
   - Download the dataset from 17lands public datasets (https://www.17lands.com/public_datasets)
2. **Run the script**:
   ```bash
   python main.py
   ```

3. **Interpret the plot**:
   - Points above the dashed line indicate cards that perform better with the synergy card
   - Hover over points to see card names
   - Larger bubbles represent more reliable data (higher sample size)

## Data Sources

- Card metadata: [Scryfall API](https://scryfall.com/docs/api)
- Win rate data: 17Lands public dataset

## Notes

- The script caches Scryfall API responses locally to avoid repeated requests
- Sample data is limited to commons/uncommons by default (adjustable in code)
- Execution time depends on dataset size and API rate limits
