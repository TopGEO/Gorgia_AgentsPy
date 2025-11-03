from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Cancel the specific job
client.fine_tuning.jobs.cancel("ftjob-Ctqq4qpAn8uPW6PbH8IyoGB9")
print("✅ Fine-tuning job cancelled")