import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoConfig, AutoModelForCausalLM

device = torch.device("cuda" if torch.cuda.is_available else "cpu")

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b",
    device_map='auto',
    token = "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"
)

tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b")
