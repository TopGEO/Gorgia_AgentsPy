import os

path = 'fine-tune/topics'

finetuned_data = ""

for filename in os.listdir(path):
    file_path = os.path.join(path, filename)
    if os.path.isfile(file_path) and filename.endswith('.jsonl'):
        with open(file_path, "r") as f:
            data = f.read().strip() + "\n"
            finetuned_data += data
            
with open("fine-tune/fine-tuned.jsonl", "w") as f:
    f.write(finetuned_data.strip())