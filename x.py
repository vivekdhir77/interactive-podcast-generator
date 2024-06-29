import pandas as pd

df = pd.read_json("hf://datasets/RamAnanth1/lex-fridman-podcasts/lex-fridman-podcast-dataset.jsonl", lines=True)

df.to_csv("data.csv", index=False)