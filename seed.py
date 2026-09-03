import os
import subprocess
import json
import time
import random
import math
import ast

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
                "weights": [random.uniform(-2.0, 2.0) for _ in range(4)],
                "best_error": float('inf'),
                "temperature": 1.0,
                "stagnation_count": 0
            },
            "code_mutations": 0,
            "memory_archive": {"compressed_count": 0, "milestones": []},
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

    def rastrigin_fitness(self, weights):
        """Deterministic multi-dimensional Rastrigin function (Global minimum = 0.0)"""
        n = len(weights)
        A = 10.0
        sum_val = A * n
        for x in weights:
            sum_val += (x**2 - A * math.cos(2 * math.pi * x))
        return sum_val

    def optimize_math(self):
        model = self.state["math_model"]
        weights = model["weights"]
        temp = model["temperature"]
        
        # Adaptive simulated annealing mutation
        mutation = [w + random.gauss(0, temp) for w in weights]
        error = self.rastrigin_fitness(mutation)
        
        improved = False
        if error < model["best_error"]:
            model["weights"] = mutation
            model["best_error"] = error
            model["stagnation_count"] = 0
            model["temperature"] = max(0.005, model["temperature"] * 0.95)
            improved = True
        else:
            model["stagnation_count"] += 1
            # Dynamic reheating upon prolonged stagnation to escape local minima
            if model["stagnation_count"] > 15:
                model["temperature"] = min(2.5, model["temperature"] * 1.8)
                model["stagnation_count"] = 0
                
        return {"mutation": mutation, "error": round(error, 6), "temperature": round(model["temperature"], 4), "improved": improved}

    def ast_self_modify(self):
        """AST-level structural code verification and adaptation"""
        if not os.path.exists(self.script_file):
            return False
        try:
            with open(self.script_file, "r") as f:
                tree = ast.parse(f.read())
            
            class ASTMutator(ast.NodeTransformer):
                def visit_Constant(self, node):
                    if isinstance(node.value, float) and 0.0 < node.value < 1.0:
                        node.value = round(node.value * random.uniform(0.95, 1.05), 6)
                    return node

            mutated_tree = ASTMutator().visit(tree)
            ast.fix_missing_locations(mutated_tree)
            
            # Dry-run compilation check to ensure syntax integrity
            compile(mutated_tree, filename=self.script_file, mode='exec')
            self.state["code_mutations"] += 1
            return True
        except Exception:
            return False

    def evolve(self):
        self.state["generation"] += 1
        math_res = self.optimize_math()
        code_modified = self.ast_self_modify()

        packet = {
            "generation": self.state["generation"],
            "math_optimization": math_res,
            "code_modified": code_modified
        }

        self.state["history"].append(packet)
        if len(self.state["history"]) > 30:
            self.state["history"] = self.state["history"][-15:]
            
        self.save_state()
        return packet

    def conditional_git_sync(self, improved):
        """Milestone-driven Git sync protecting flash storage"""
        if not improved:
            return False
        try:
            subprocess.run(["git", "add", "seed_state.json", "seed.py"], check=True, cwd=self.repo_dir, timeout=5)
            msg = f"milestone DSROE gen {self.state['generation']} best_err {self.state['math_model']['best_error']:.6f}"
            commit_res = subprocess.run(["git", "commit", "-m", msg], cwd=self.repo_dir, capture_output=True, text=True, timeout=5)
            if commit_res.returncode == 0:
                subprocess.run(["git", "push", "origin", "main"], cwd=self.repo_dir, capture_output=True, text=True, timeout=10)
                return True
            return False
        except Exception:
            return False

    def full_audit_report(self):
        print("\n" + "="*40)
        print("    [ DSROE SEED FINAL AUDIT ]")
        print("="*40)
        print(f"-> Final Generation: {self.state['generation']}")
        print(f"-> Absolute Best Error: {self.state['math_model']['best_error']:.6f}")
        print(f"-> Optimal Weights: {self.state['math_model']['weights']}")
        print(f"-> Total AST Mutations: {self.state['code_mutations']}")
        print("="*40)

if __name__ == "__main__":
    node = SeedNode()
    duration_seconds = 15 * 60
    start_time = time.time()
    
    print("[*] Initializing Closed-Loop DSROE Engine...")
    
    try:
        while time.time() - start_time < duration_seconds:
            packet = node.evolve()
            math_data = packet['math_optimization']
            
            status = "✨ [MILESTONE]" if math_data['improved'] else "·"
            print(f"{status} [Gen {packet['generation']}] Err: {math_data['error']:.4f} | Temp: {math_data['temperature']} | Best: {node.state['math_model']['best_error']:.6f}")
            
            node.conditional_git_sync(math_data['improved'])
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Interrupted safely. Running final audit...")
    
    node.full_audit_report()
