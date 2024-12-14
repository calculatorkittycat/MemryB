from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments
import os

# Ensure the model path is correct and uses raw strings to avoid escape sequence issues
from transformers import AutoModelForCausalLM

AutoModelForCausalLM.from_pretrained("Llama-3.2-1B", cache_dir="C:/Users/cicai/.llama/checkpoints/Llama3.2-3B2")
model_path = r"C:\Users\cicai\.llama\checkpoints\Llama3.2-1BCustom"

# Check if the model path exists
if not os.path.exists(model_path):
    raise FileNotFoundError(f"Model path '{model_path}' does not exist. Please check the path.")

# Load tokenizer and model
try:
    tokenizer = AutoTokenizer.from_pretrained(model_path, legacy=False, use_fast=False)
    model = AutoModelForCausalLM.from_pretrained(model_path)
except Exception as e:
    raise RuntimeError(f"Failed to load tokenizer or model. Ensure the files exist in '{model_path}'. Error: {e}")

# Path to dataset file
dataset_file = r"C:\Users\cicai\PycharmProjects\MemryB\Sandbox\Experimental\X86\Junkyard\solomonsCoat.txt"

# Check if the dataset file exists
if not os.path.exists(dataset_file):
    raise FileNotFoundError(f"Dataset file '{dataset_file}' does not exist. Please check the path.")

# Load and preprocess dataset
dataset = load_dataset("text", data_files=dataset_file)

# Preprocessing function
def preprocess(examples):
    return tokenizer(examples["text"], truncation=True, padding="max_length", max_length=512)

# Apply preprocessing to the dataset
try:
    tokenized_dataset = dataset.map(preprocess, batched=True)
except Exception as e:
    raise RuntimeError(f"Error during dataset preprocessing: {e}")

# Define training arguments
training_args = TrainingArguments(
    output_dir="./fine_tuned_llama",
    evaluation_strategy="epoch",
    learning_rate=5e-5,
    per_device_train_batch_size=4,
    num_train_epochs=3,
    save_strategy="epoch",
    logging_dir="./logs",
    save_total_limit=1,  # Keeps only the most recent checkpoint
    logging_steps=10
)

# Split dataset into train and validation (if no predefined split exists)
if "train" not in tokenized_dataset:
    raise KeyError("The dataset does not contain a 'train' split. Check the dataset format.")

try:
    train_test_split = tokenized_dataset["train"].train_test_split(test_size=0.1)
    train_dataset = train_test_split["train"]
    eval_dataset = train_test_split["test"]
except Exception as e:
    raise RuntimeError(f"Error splitting the dataset into training and validation sets: {e}")

# Train the model
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset
)

try:
    trainer.train()
except Exception as e:
    raise RuntimeError(f"Training failed: {e}")
