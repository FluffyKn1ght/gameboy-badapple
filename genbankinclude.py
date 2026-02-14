import sys

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("USAGE: genbankinclude.py <num of banks>")
        exit(1)

    with open("banks.s", "w", encoding="utf-8") as f:
        for i in range(1, int(sys.argv[1]) + 1):
            f.write(f'SECTION "ROM{i}Data", ROMX[$4000], BANK[{i}]')
            f.write(f'\n  INCBIN "banks/bank{i}.bin"\n')
