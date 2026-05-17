import sys
import json
import subprocess
import os
from web3 import Web3

real_user = os.environ.get("SUDO_USER") or os.environ.get("USER")
home = os.path.expanduser(f"~{real_user}") if real_user else os.path.expanduser("~")
anvil = os.path.join(home, ".foundry/bin/anvil")
forge = os.path.join(home, ".foundry/bin/forge")
url = "http://127.0.0.1:8545"
contract_file = "contract.txt"
artifact_file = "out/Voting.sol/Voting.json"
voters_file = "voters.txt"

w3 = Web3(Web3.HTTPProvider(url))


def is_root():
    return os.getuid() == 0


def get_user():
    return os.environ.get("SUDO_USER") or os.environ.get("USER") or os.getlogin()


def already_voted(user):
    if not os.path.exists(voters_file):
        return False
    with open(voters_file, "r") as f:
        voters = f.read().splitlines()
    return user in voters


def mark_voted(user):
    with open(voters_file, "a") as f:
        f.write(user + "\n")


def compile():
    print("Compiling contract...")
    subprocess.run([forge, "build", "--silent"], check=True)
    print("Done.")


def load_artifact():
    with open(artifact_file, "r") as f:
        data = json.load(f)
    abi = data["abi"]
    bytecode = data["bytecode"]["object"]
    return abi, bytecode


def save_address(addr):
    with open(contract_file, "w") as f:
        f.write(addr)


def load_address():
    with open(contract_file, "r") as f:
        return f.read().strip()


def get_contract():
    addr = load_address()
    abi, _ = load_artifact()
    return w3.eth.contract(address=addr, abi=abi)


def start_node():
    print("Starting blockchain at " + url)
    print("Keep this running. Open a new terminal for other commands.")
    subprocess.run([anvil])


def deploy(names):
    if not is_root():
        print("Only root can start the election.")
        print("Run: sudo python3 vote.py deploy ...")
        return

    compile()

    abi, bytecode = load_artifact()

    me = w3.eth.accounts[0]
    c = w3.eth.contract(abi=abi, bytecode=bytecode)

    print("Deploying contract with candidates:", names)
    tx = c.constructor(names).transact({"from": me})
    r = w3.eth.wait_for_transaction_receipt(tx)
    addr = r.contractAddress

    save_address(addr)

    with open(voters_file, "w") as f:
        f.write("")
    os.chmod(voters_file, 0o666)

    print("Election started! Contract deployed at:", addr)


def stop():
    if not is_root():
        print("Only root can stop the election.")
        print("Run: sudo python3 vote.py stop")
        return

    c = get_contract()
    me = w3.eth.accounts[0]

    print("Stopping election...")
    tx = c.functions.stopElection().transact({"from": me})
    w3.eth.wait_for_transaction_receipt(tx)
    print("Election stopped.")


def show_candidates():
    c = get_contract()
    total = c.functions.getTotalCandidates().call()

    print("Candidates:")
    for i in range(total):
        name = c.functions.candidates(i).call()
        votes = c.functions.getVoteCount(i).call()
        print(" ", i, "-", name, ":", votes, "votes")


def cast_vote(cid, acc):
    user = get_user()

    if already_voted(user):
        print("You already voted,", user)
        return

    c = get_contract()

    running = c.functions.active().call()
    if not running:
        print("Election is stopped. No more votes.")
        return

    me = w3.eth.accounts[acc]
    name = c.functions.candidates(cid).call()

    print("Voting for", name, "from user", user, "...")

    try:
        tx = c.functions.vote(cid).transact({"from": me})
        w3.eth.wait_for_transaction_receipt(tx)
        mark_voted(user)
        print("Vote cast successfully!")
    except Exception as e:
        print("Failed:", str(e))


def show_results():
    c = get_contract()
    total = c.functions.getTotalCandidates().call()

    print("Results:")
    for i in range(total):
        name = c.functions.candidates(i).call()
        votes = c.functions.getVoteCount(i).call()
        print(" ", name, "got", votes, "vote(s)")


def show_help():
    print("Simple Voting System")
    print("")
    print("  python3 vote.py node                                    start the blockchain")
    print("  sudo python3 vote.py deploy Alice Bob Charlie           start the election")
    print("  python3 vote.py candidates                              list candidates")
    print("  python3 vote.py vote <id> <account>                    cast a vote")
    print("  python3 vote.py results                                 see results")
    print("  sudo python3 vote.py stop                               stop the election")


cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

if cmd == "node":
    start_node()

elif cmd == "deploy":
    names = sys.argv[2:]
    if len(names) == 0:
        print("Tell me the candidate names.")
        print("Example: sudo python3 vote.py deploy candidate1 candidate2 candidate3")
    else:
        deploy(names)

elif cmd == "candidates":
    show_candidates()

elif cmd == "vote":
    if len(sys.argv) < 4:
        print("Usage: python3 vote.py vote <candidate number> <account number>")
    else:
        cast_vote(int(sys.argv[2]), int(sys.argv[3]))

elif cmd == "results":
    show_results()

elif cmd == "stop":
    stop()

else:
    show_help()
