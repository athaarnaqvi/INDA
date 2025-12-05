"""
Network Topology Inference Module
Generates structured network topology from natural language descriptions
"""

import os
import torch
import re
from typing import Dict, List, Tuple
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel, PeftConfig


class TopologyInference:
    def __init__(self, model_path: str):
        """
        Initialize the topology inference model
        """
        self.model_path = model_path
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        print(f"🔄 Loading model from {model_path}")
        print(f"📍 Device: {self.device}")

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)

        # Detect if folder contains LoRA config
        if os.path.exists(os.path.join(model_path, "adapter_config.json")):
            print("🟣 Detected LoRA adapter — loading base model + adapter")
            config = PeftConfig.from_pretrained(model_path)
            base_model = AutoModelForCausalLM.from_pretrained(
                config.base_model_name_or_path,
                torch_dtype=torch.float32,
                device_map="auto"
            )
            self.model = PeftModel.from_pretrained(base_model, model_path)
        else:
            print("🟢 Loading merged final model")
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float32,
                device_map="auto"
            )

        self.model.eval()
        print("✅ Model loaded successfully!")

    def generate_topology(self, description: str, max_tokens: int = 300) -> str:
        prompt = (
            f"Extract machines and network connections.\n"
            f"Prompt: {description}\nResponse:"
        )

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            output = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=0.2,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id
            )

        full_text = self.tokenizer.decode(output[0], skip_special_tokens=True)

        # Extract only the "Response:" part
        if "Response:" in full_text:
            return full_text.split("Response:", 1)[1].strip()
        return full_text

    def parse_topology(self, text: str) -> Dict[str, List]:
        result = {"machines": [], "connections": []}
        lines = text.strip().split("\n")
        section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if "MACHINES" in line.upper():
                section = "machines"
                continue
            if "CONNECTIONS" in line.upper():
                section = "connections"
                continue

            # Parse machines
            if section == "machines":
                m = re.match(r"(.+?)\s*\(type=(.+?)\)", line)
                if m:
                    name, t = m.groups()
                    result["machines"].append({"name": name.strip(), "type": t.strip()})
                else:
                    result["machines"].append({"name": line, "type": "Unknown"})

            # Parse connections
            elif section == "connections":
                m = re.match(r"(.+?)\s*->\s*(.+?)(?:\((.+?)\))?", line)
                if m:
                    src, dst, ctype = m.groups()
                    result["connections"].append({
                        "source": src.strip(),
                        "target": dst.strip(),
                        "type": ctype.strip() if ctype else "Ethernet"
                    })

        return result

    def predict(self, description: str) -> Tuple[str, Dict]:
        raw = self.generate_topology(description)
        parsed = self.parse_topology(raw)
        return raw, parsed

    def format_output(self, parsed: Dict) -> str:
        out = ["[MACHINES]"]
        for m in parsed["machines"]:
            out.append(f"{m['name']} (type={m['type']})")

        out.append("\n[CONNECTIONS]")
        for c in parsed["connections"]:
            out.append(f"{c['source']} -> {c['target']} ({c['type']})")

        return "\n".join(out)
