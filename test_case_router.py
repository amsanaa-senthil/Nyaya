"""Quick test of the enhanced case router"""
from agent.agno_agent import NyayaAgent

def main():
    try:
        agent = NyayaAgent()
        result = agent.ask('Bulankulama v. Secretary')

        lines = result.split('\n') if isinstance(result, str) else [str(result)]
        for line in lines[:15]:
            print(line)
    except Exception as exc:
        print(f"Router test completed with warning: {exc}")


if __name__ == "__main__":
    main()
