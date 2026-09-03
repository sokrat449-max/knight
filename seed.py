import os
import subprocess
import json
import time
import urllib.request
import urllib.error
import random
import re
import xml.etree.ElementTree as ET

class SeedNode:
    def __init__(self, repo_dir="."):
        self.repo_dir = repo_dir
        self.state_file = os.path.join(repo_dir, "seed_state.json")
        self.script_file = os.path.join(repo_dir, "seed.py")
        self.state = self.load_state()

    def default_state(self):
        return {
            "generation": 0,
            "math_model": {
                "weights": [random.uniform(-1.0, 1.0), random.uniform(-1.0, 1.0)],
                "best_error": float('inf')
            },
            "language_model": {"vocabulary": [], "frequencies": {}},
            "code_mutations": 0,
            "memory_archive": {"compressed_count": 0, "milestones": []},
            "external_ingestion": [],
            "history": []
        }

    def load_state(self):
        default = self.default_state()
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    data = json.load(f)
                    for k, v in default.items():
                        if k not in data:
                            data[k] = v
                        elif isinstance(v, dict) and isinstance(data.get(k), dict):
                            for sub_k, sub_v in v.items():
                                if sub_k not in data[k]:
                                    data[k][sub_k] = sub_v
                    return data
            except Exception:
                return default
        return default

    def save_state(self):
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=4)

    def probe_wide_network(self):
        """Confronting the wide network by fetching external open data streams"""
        obs = {"timestamp": time.time(), "network_metric": 150.0, "external_text": ""}
        
        # Target: Public Hacker News RSS or lightweight open tech feed to harvest real-world text
        endpoints = [
            "https://news.ycombinator.com/rss",
            "https://httpbin.org/delay/0"
        ]
        chosen_url = random.choice(endpoints)
        
        try:
            start = time.time()
            req = urllib.request.Request(chosen_url, headers={'User-Agent': 'SeedNode/3.0-WildNetwork'})
            with urllib.request.urlopen(req, timeout=3) as response:
                obs["network_metric"] = round((time.time() - start) * 1000, 2)
                raw_data = response.read().decode('utf-8', errors='ignore')
                obs["external_text"] = raw_data[:2000] # Capture a slice of the real world
        except Exception:
            obs["network_metric"] = round(random.uniform(100.0, 350.0), 2)
            obs["external_text"] = "fallback network environment local sandbox"
            
        return obs

    def harvest_vocabulary(self, external_text=""):
        vocab = self.state["language_model"]["vocabulary"]
        freqs = self.state["language_model"]["frequencies"]
        
        source_texts = [external_text]
        if os.path.exists(self.script_file):
            with open(self.script_file, "r") as f:
                source_texts.append(f.read())
                
        for text in source_texts:
            words = re.findall(r'\b[a-zA-Z]{4,}\b', text)
            for w in words:
                w_lower = w.lower()
                freqs[w_lower] = freqs.get(w_lower, 0) + 1
                if w_lower not in vocab:
                    vocab.append(w_lower)
                    
        active_vocab = [w for w, count in sorted(freqs.items(), key=lambda x: x[1], reverse=True)[:60]]
        if not active_vocab:
            active_vocab = ["node", "seed", "network", "adaptive"]
        return " ".join(random.choices(active_vocab, k=min(4, len(active_vocab))))

    def optimize_math(self, real_metric):
        model = self.state["math_model"]
        weights = model["weights"]
        
        mutation = [max(-10.0, min(10.0, w + random.uniform(-0.05, 0.05))) for w in weights]
        predicted = (mutation[0] * 100.0) + (mutation[1] * real_metric * 0.5)
        predicted = max(0.0, min(predicted, 5000.0))

        error = abs(predicted - real_metric)
        if error < model["best_error"]:
            model["weights"] = mutation
            model["best_error"] = error
            improved = True
        else:
            improved = False
        return {"mutation": mutation, "error": round(error, 2), "improved": improved}

    def self_manage_memory(self):
        history = self.state["history"]
        if len(history) > 15:
            old_entries = history[:-8]
            recent_entries = history[-8:]
            avg_error = sum(e.get("math_optimization", {}).get("error", 0) for e in old_entries) / len(old_entries)
            milestone = {
                "range": f"Gen {old_entries[0]['generation']} to {old_entries[-1]['generation']}",
                "avg_error": round(avg_error, 2)
            }
            self.state["memory_archive"]["compressed_count"] += len(old_entries)
            self.state["memory_archive"]["milestones"].append(milestone)
            self.state["history"] = recent_entries

    def self_modify_code(self):
        if not os.path.exists(self.script_file):
            return False
        with open(self.script_file, "r") as f:
            code = f.read()
        
        stamp = f"# # # # # WILD_NETWORK_LOG: gen_112 time_1788452992.3451147
        if "# # # # WILD_NETWORK_LOG: gen_112 time_1788452992.3451147
            code = re.sub(r'# # # # WILD_NETWORK_LOG: gen_112 time_1788452992.3451147
        else:
            code = code.replace("class SeedNode:", f"{stamp}\nclass SeedNode:")

        with open(self.script_file, "w") as f:
            f.write(code)
        self.state["code_mutations"] += 1
        return True

    def evolve(self):
        self.state["generation"] += 1
        env_obs = self.probe_wide_network()
        metric = env_obs["network_metric"]
        
        math_res = self.optimize_math(metric)
        lang_out = self.harvest_vocabulary(env_obs["external_text"])
        code_modified = self.self_modify_code()

        packet = {
            "generation": self.state["generation"],
            "environment_metric": metric,
            "math_optimization": math_res,
            "language_synthesis": lang_out,
            "code_modified": code_modified
        }

        self.state["history"].append(packet)
        self.self_manage_memory()
        self.save_state()
        return packet

    def git_sync(self):
        try:
            subprocess.run(["git", "add", "seed_state.json", "seed.py"], check=True, cwd=self.repo_dir, timeout=5)
            commit_res = subprocess.run(["git", "commit", "-m", f"wild network evolution gen {self.state['generation']}"], cwd=self.repo_dir, capture_output=True, text=True, timeout=5)
            if commit_res.returncode == 0:
                push_res = subprocess.run(["git", "push", "-u", "origin", "main"], cwd=self.repo_dir, capture_output=True, text=True, timeout=10)
                return push_res.returncode == 0
            return False
        except Exception:
            return False

    def full_audit_report(self):
        print("\n" + "="*40)
        print("    [ WILD NETWORK SEED AUDIT ]")
        print("="*40)
        print(f"-> Current Generation: {self.state['generation']}")
        print(f"-> Best Recorded Math Error: {self.state['math_model']['best_error']:.4f}")
        print(f"-> Total Code Mutations: {self.state['code_mutations']}")
        print(f"-> Vocabulary Size: {len(self.state['language_model']['vocabulary'])} words")
        print("="*40)

if __name__ == "__main__":
    node = SeedNode()
    duration_seconds = 15 * 60
    start_time = time.time()
    
    print("[*] Releasing Seed into the Wild Network...")
    
    try:
        while time.time() - start_time < duration_seconds:
            packet = node.evolve()
            math_data = packet['math_optimization']
            print(f"[Gen {packet['generation']}] Metric: {packet['environment_metric']} | Error: {math_data['error']:.2f} | Phrase: '{packet['language_synthesis']}'")
            node.git_sync()
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n[*] Interrupted in the wild. Running final audit...")
    
    node.full_audit_report()
