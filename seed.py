import os
import subprocess
import json
import time
import urllib.request
import socket
import random
import re

class SeedNode:
    def __init__(self, repo_dir="."):
        self.repo_dir = repo_dir
        self.state_file = os.path.join(repo_dir, "seed_state.json")
        self.script_file = os.path.join(repo_dir, "seed.py")
        self.state = self.load_state()

    def default_state(self):
        return {
            "generation": 0,
            "math_model": {"weights": [random.random(), random.random()], "best_error": float('inf')},
            "language_model": {"vocabulary": [], "frequencies": {}},
            "code_mutations": 0,
            "memory_archive": {"compressed_count": 0, "milestones": []},
            "history": []
        }

    def load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    data = json.load(f)
                    default = self.default_state()
                    for k, v in default.items():
                        if k not in data:
                            data[k] = v
                    return data
            except Exception:
                return self.default_state()
        return self.default_state()

    def save_state(self):
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=4)

    def probe_environment(self):
        obs = {"timestamp": time.time(), "latency_ms": None, "system_signature": ""}
        try:
            start = time.time()
            urllib.request.urlopen("https://github.com", timeout=3)
            obs["latency_ms"] = round((time.time() - start) * 1000, 2)
        except Exception:
            obs["latency_ms"] = 500.0
        try:
            uname_res = subprocess.run(["uname", "-a"], capture_output=True, text=True)
            obs["system_signature"] = uname_res.stdout.strip()
        except Exception:
            obs["system_signature"] = "termux_local"
        return obs

    def harvest_vocabulary(self):
        vocab = self.state["language_model"]["vocabulary"]
        freqs = self.state["language_model"]["frequencies"]
        source_texts = []
        if os.path.exists(self.script_file):
            with open(self.script_file, "r") as f:
                source_texts.append(f.read())
        try:
            env_out = subprocess.run(["ls", "-la"], capture_output=True, text=True).stdout
            source_texts.append(env_out)
        except Exception:
            pass
        for text in source_texts:
            words = re.findall(r'\b[a-zA-Z]{4,}\b', text)
            for w in words:
                w_lower = w.lower()
                freqs[w_lower] = freqs.get(w_lower, 0) + 1
                if w_lower not in vocab:
                    vocab.append(w_lower)
        active_vocab = [w for w, count in sorted(freqs.items(), key=lambda x: x[1], reverse=True)[:50]]
        if not active_vocab:
            active_vocab = ["node", "seed", "local", "state"]
        return " ".join(random.choices(active_vocab, k=min(4, len(active_vocab))))

    def optimize_math(self, real_metric):
        weights = self.state["math_model"]["weights"]
        mutation = [w + random.uniform(-0.05, 0.05) for w in weights]
        predicted = mutation[0] * 50.0 + mutation[1] * 10.0
        error = abs(predicted - real_metric)
        if error < self.state["math_model"]["best_error"]:
            self.state["math_model"]["weights"] = mutation
            self.state["math_model"]["best_error"] = error
            improved = True
        else:
            improved = False
        return {"mutation": mutation, "error": error, "improved": improved}

    def self_manage_memory(self):
        history = self.state["history"]
        if len(history) > 10:
            old_entries = history[:-5]
            recent_entries = history[-5:]
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
        if "EVOLUTION_LOG: gen_19
            code = re.sub(r'EVOLUTION_LOG: gen_19
        else:
            code = code.replace("class SeedNode:", f"# EVOLUTION_LOG: gen_19
        with open(self.script_file, "w") as f:
            f.write(code)
        self.state["code_mutations"] += 1
        return True

    def evolve(self):
        self.state["generation"] += 1
        env_obs = self.probe_environment()
        latency = env_obs["latency_ms"]
        math_res = self.optimize_math(latency)
        lang_out = self.harvest_vocabulary()
        code_modified = self.self_modify_code()

        packet = {
            "generation": self.state["generation"],
            "environment": env_obs,
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
            subprocess.run(["git", "add", "seed_state.json", "seed.py"], check=True, cwd=self.repo_dir)
            commit_res = subprocess.run(["git", "commit", "-m", f"autonomous memory and evolution gen {self.state['generation']}"], cwd=self.repo_dir, capture_output=True, text=True)
            if commit_res.returncode == 0:
                push_res = subprocess.run(["git", "push", "-u", "origin", "main"], cwd=self.repo_dir, capture_output=True, text=True)
                return push_res.returncode == 0
            return False
        except Exception:
            return False

    def full_audit_report(self):
        print("\n" + "="*40)
        print("    [ SEED SYSTEM AUDIT REPORT ]")
        print("="*40)
        print(f"-> Current Generation: {self.state['generation']}")
        print(f"-> Best Math Error: {self.state['math_model']['best_error']:.4f}")
        print(f"-> Code Mutations: {self.state['code_mutations']}")
        print(f"-> Vocabulary Size: {len(self.state['language_model']['vocabulary'])} words")
        print(f"-> Archived Memories: {self.state['memory_archive']['compressed_count']}")
        print(f"-> Milestones Recorded: {len(self.state['memory_archive']['milestones'])}")
        print("="*40)

if __name__ == "__main__":
    node = SeedNode()
    duration_seconds = 15 * 60  # 15 minutes
    start_time = time.time()
    
    print("[*] Starting 15-minute network access and autonomous evolution window...")
    
    while time.time() - start_time < duration_seconds:
        packet = node.evolve()
        print(f"[Gen {packet['generation']}] Math Error: {packet['math_optimization']['error']:.2f} | Phrase: '{packet['language_synthesis']}'")
        node.git_sync()
        time.sleep(10)
    
    node.full_audit_report()
