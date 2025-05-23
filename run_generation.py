from generator import DataGenerator

file = "data/generation-console.json"
dg = DataGenerator(input_file=file, output_file=file[:-5] + "-test.json", llm='gpt-4o') # gpt-4o
dg.generate(framework=False)