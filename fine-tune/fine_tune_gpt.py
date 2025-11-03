import os
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ OPENAI_API_KEY not found in .env file")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Configuration
DATASET_PATH = Path(__file__).parent / "fine-tuned.jsonl"
BASE_MODEL = "gpt-4.1-2025-04-14"
CHECK_INTERVAL = 5  # seconds

def main():
    print("🚀 Starting GPT fine-tuning pipeline...\n")

    # 1. Validate dataset
    if not Path(DATASET_PATH).exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")
    print(f"✅ Dataset found: {DATASET_PATH}")

    # 2. Upload file
    print("\n📤 Uploading dataset to OpenAI...")
    with open(DATASET_PATH, "rb") as f:
        uploaded_file = client.files.create(file=f, purpose="fine-tune")
    print(f"✅ File uploaded: {uploaded_file.id}")

    # 3. Create fine-tuning job
    print("\n🔧 Creating fine-tuning job...")
    fine_tune = client.fine_tuning.jobs.create(
        training_file=uploaded_file.id,
        model=BASE_MODEL
    )
    job_id = fine_tune.id
    print(f"✅ Job created: {job_id}")

    # 4. Monitor progress
    print("\n⏳ Monitoring fine-tuning progress...\n")
    last_trained_tokens = 0
    while True:
        job = client.fine_tuning.jobs.retrieve(job_id)
        status = job.status

        # Display detailed progress info
        print(f"📊 Status: {status}")
        if hasattr(job, 'trained_tokens') and job.trained_tokens:
            print(f"   Trained tokens: {job.trained_tokens:,}")
            if last_trained_tokens > 0:
                delta = job.trained_tokens - last_trained_tokens
                print(f"   Progress: +{delta:,} tokens since last check")
            last_trained_tokens = job.trained_tokens

        if hasattr(job, 'estimated_finish') and job.estimated_finish:
            print(f"   Estimated finish: {job.estimated_finish}")

        # Show events/logs if available
        try:
            events = client.fine_tuning.jobs.list_events(job_id, limit=5)
            if events.data:
                print(f"\n📝 Recent events:")
                for event in reversed(events.data):
                    timestamp = time.strftime('%H:%M:%S', time.localtime(event.created_at))
                    print(f"   [{timestamp}] {event.message}")
        except Exception:
            pass

        print()  # Blank line for readability

        if status == "succeeded":
            print("🎉 Fine-tuning succeeded!")
            print(f"📝 Fine-tuned model ID: {job.fine_tuned_model}")
            print("\n💡 Usage example:")
            print(f'client.chat.completions.create(model="{job.fine_tuned_model}", messages=[{{"role": "user", "content": "Your prompt"}}])')
            break

        elif status == "failed":
            error_msg = getattr(job, 'error', 'Unknown error')
            print(f"❌ Fine-tuning failed: {error_msg}")
            break

        elif status in ["queued", "running", "validating_files"]:
            print(f"⏱️  Checking again in {CHECK_INTERVAL} seconds...\n")
            time.sleep(CHECK_INTERVAL)
        else:
            print(f"⚠️ Unexpected status: {status}")
            print(f"⏱️  Checking again in {CHECK_INTERVAL} seconds...\n")
            time.sleep(CHECK_INTERVAL)

    # 5. Cleanup (optional): delete uploaded file
    try:
        client.files.delete(uploaded_file.id)
        print(f"\n🗑️ Cleaned up uploaded file: {uploaded_file.id}")
    except Exception as e:
        print(f"\n⚠️ Failed to delete uploaded file: {e}")

if __name__ == "__main__":
    main()