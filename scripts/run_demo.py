import httpx
import time
import subprocess

def main():
    print("Running end-to-end demo...")
    print("1. Benign Activity")
    subprocess.run(["python3", "scripts/simulate_benign_activity.py"])
    time.sleep(2)
    
    print("2. Brute Force Attack")
    subprocess.run(["python3", "scripts/simulate_brute_force.py"])
    time.sleep(2)
    
    print("3. Attack Chain")
    subprocess.run(["python3", "scripts/simulate_attack_chain.py"])
    print("Demo execution complete.")

if __name__ == "__main__":
    main()
