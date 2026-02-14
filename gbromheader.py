import argparse


NINTENDO_LOGO = b"\xce\xed\x66\x66\xcc\x0d\x00\x0b\x03\x73\x00\x83\x00\x0c\x00\x0d\x00\x08\x11\x1f\x88\x89\x00\x0e\xdc\xcc\x6e\xe6\xdd\xdd\xd9\x99\xbb\xbb\x67\x63\x6e\x0e\xec\xcc\xdd\xdc\x99\x9f\xbb\xb9\x33\x3e"


def main():
    argparser = argparse.ArgumentParser(
        prog="gbromheader.py",
        description="Generates and writes a GameBoy ROM (.gb/.gbc) header",
    )

    argparser.add_argument(
        "-t",
        "--title",
        required=True,
        help="Game title (<=15 symbols, ASCII only, will get converted to UPPERCASE and padded with 0x00 bytes/trimmed)",
    )
    argparser.add_argument(
        "-c",
        "--cgb",
        action="store_true",
        help="Mark ROM as GameBoy Color (CGB) compatible",
    )
    argparser.add_argument(
        "-b",
        "--sgb",
        action="store_true",
        help="Mark ROM as Super GameBoy (SGB) compatible",
    )
    argparser.add_argument(
        "-l",
        "--licensee",
        default="\x00\x00",
        help=f"Licensee code (two-byte ASCII string) (default is {r'"\x00\x00"'})",
    )
    argparser.add_argument(
        "-m",
        "--mapper",
        default="rom",
        help=f"Memory mapper chip (MBC/MMM/etc), see {'"Mappers"'} below (default is {'"rom"'} aka mapper 0x00 aka ROM ONLY) (make sure to specify ROM/SRAM bank size via -r/--rom-size and -s/--sram-size when using a mapper!!)",
    )
    argparser.add_argument(
        "-r",
        "--rom-size",
        action="store",
        type=int,
        default=-1,
        help="Cartridge ROM size, in banks: 2/4/8/16/32/64/128/72/80/96",
    )
    argparser.add_argument(
        "-s",
        "--sram-size",
        action="store",
        type=int,
        default=-1,
        help="Cartridge RAM (SRAM) size, in kilobytes: 2/8/32/128",
    )
    argparser.add_argument(
        "-e",
        "--region",
        default="export",
        help=f"Destination region: {'"japan"'}/{'"export"'}",
    )
    argparser.add_argument(
        "-n",
        "--logo",
        "--nintendo-logo",
        default="$NINTENDO$",
        help=f"Logo data file name (must match Nintendo logo in CPU BootROM, otherwise game won't run on real hardware!!) (default is {'"$NINTENDO$"'}, which will use use the Nintendo logo hardcoded into the script)",
    )
    argparser.add_argument(
        "-o",
        "--out",
        "--output",
        required=True,
        help=f"Output file name, will overwrite header if file already exists",
    )

    argparser.epilog = 'Mappers: "rom"; "mbc1"/"mbc1+ram"/"mbc1+ram+batt"; "mbc2"/"mbc2+ram"/"mbc2+batt"; "mbc3"/"mbc3+rtc+batt"/"mbc3+rtc+ram+batt" "ram"/"ram+batt"; "mmm01"/"mmm01+ram"/"mmm01+ram+batt"; "mbc3+ram"/"mbc3+ram+batt"; "mbc5"/"mbc5+ram"/"mbc5+ram+batt"/"mbc5+rumble"/"mbc5+rumble+ram"/"mbc5+rumble+ram+batt"; "camera"; "tama5"; "huc3"; "huc1"; "mbc6"; "mbc7";'
    args = argparser.parse_args()

    data = b""

    nlogo = NINTENDO_LOGO
    if args.logo != "$NINTENDO$":
        try:
            with open(args.logo, "rb") as f:
                nlogo = f.read()[0 : len(NINTENDO_LOGO) + 1]
                if len(nlogo) < len(NINTENDO_LOGO):
                    print(
                        "ERROR: Not enough bytes in provided logo file to fill logo section"
                    )
                    print(
                        "ERROR: Couldn't generate header - output file was not changed"
                    )
                    exit(1)
        except Exception as e:
            print(
                f"ERROR: Couldn't read logo data from provided logo file: {e.__class__.__name__} - {e}"
            )
            print("ERROR: Couldn't generate header - output file was not changed")
            exit(1)

    data += nlogo

    title = args.title.upper().encode("ascii")
    if len(title) > 15:
        print(
            f"WARN: Title is longer than 15 characters and will be trimmed to {f'"{title.decode("ascii")[0:15]}"'}"
        )
        title = title[0:15]
    while len(title) < 15:
        title += b"\x00"
    data += title

    if args.cgb:
        data += b"\x80"
    else:
        data += b"\x00"

    data += args.licensee[0:3].encode("ascii")

    if args.sgb:
        data += b"\x03"
    else:
        data += b"\x00"

    try:
        data += {
            "rom": b"\x00",
            "mbc1": b"\x01",
            "mbc1+ram": b"\x02",
            "mbc1+ram+batt": b"\x03",
            "mbc2": b"\x05",
            "mbc2+batt": b"\x06",
            "ram": b"\x08",
            "ram+batt": b"\x09",
            "mmm01": b"\x0b",
            "mmm01+ram": b"\x0c",
            "mmm01+ram+batt": b"\x0d",
            "mbc3+rtc+batt": b"\x0f",
            "mbc3+rtc+ram+batt": b"\x10",
            "mbc3": b"\x11",
            "mbc3+ram": b"\x12",
            "mbc3+ram+batt": b"\x13",
            "mbc5": b"\x19",
            "mbc5+ram": b"\x1a",
            "mbc5+ram+batt": b"\x1b",
            "mbc5+rumble": b"\x1c",
            "mbc5+rumble+ram": b"\x1d",
            "mbc5+rumble+ram+batt": b"\x1e",
            "camera": b"\x1f",
            "tama5": b"\xfd",
            "huc3": b"\xfe",
            "huc1": b"\xff",
            "mbc6": b"\x20",
            "mbc7": b"\x22",
        }[args.mapper.lower()]
    except KeyError:
        print(f"ERROR: Unknown mapper {args.mapper.lower()}")
        print("ERROR: Couldn't generate header - output file was not changed")
        exit(1)

    if args.mapper.lower() != "rom":
        try:
            data += {
                2: b"\x00",
                4: b"\x01",
                8: b"\x02",
                16: b"\x03",
                32: b"\x04",
                64: b"\x05",
                128: b"\x06",
                72: b"\x52",
                80: b"\x53",
                96: b"\x54",
            }[args.rom_size]
        except KeyError:
            if args.rom_size == -1:
                print(
                    "ERROR: Please specify ROM bank size via -r/--rom-size (-h for a list of supported values)"
                )
            else:
                print(
                    f"ERROR: Unsupported ROM bank size: {args.rom_size} (-h for a list of supported values)"
                )
            print("ERROR: Couldn't generate header - output file was not changed")
            exit(1)

        if "ram" in args.mapper.lower().split("+"):
            try:
                data += {0: b"\x00", 2: b"\x01", 8: b"\x02", 32: b"\x03", 128: b"\x04"}[
                    args.sram_size
                ]
            except KeyError:
                if args.sram_size == -1:
                    print(
                        "ERROR: Please specify total SRAM size via -s/--sram-size (-h for a list of supported values)"
                    )
                else:
                    print(f"ERROR: Unsupported SRAM size: {args.rom_size}")
                print(
                    "ERROR: Couldn't generate header - output file was not changed (-h for a list of supported values)"
                )
                exit(1)
        else:
            data += b"\x00"
    else:
        data += b"\x00\x00"

    try:
        data += {"japan": b"\x00", "export": b"\x01"}[args.region]
    except KeyError:
        print(
            f"ERROR: Unknown destination region: {args.region} (-h for a list of supported values)"
        )
        print("ERROR: Couldn't generate header - output file was not changed")
        exit(1)

    data += b"\x33\x00"

    complement_sum = 0
    for i in range(len(NINTENDO_LOGO), len(data)):
        complement_sum += data[i]

    data += bytes([(-complement_sum - 25) & 0xFF])

    outfile_exists = False
    try:
        with open(args.out, "rb") as f:
            outfile_exists = True
    except FileNotFoundError:
        print("WARN: Output file not found, can't calculate global checksum")

    romdata = b""
    if outfile_exists:
        with open(args.out, "rb") as f:
            romdata = f.read()

        global_checksum = 0
        for i in range(len(romdata)):
            if 0x0104 <= i <= 0x014D:
                global_checksum += data[i - 0x104]
                continue

            if i != 0x014E and i != 0x14F:
                global_checksum += romdata[i]

        data += bytes([(global_checksum & 0xFF00) >> 8, global_checksum & 0xFF])

    try:
        with open(args.out, "wb") as f:
            f.write(romdata)
            f.seek(0x104)
            f.write(data)
    except Exception as e:
        print(
            f"ERROR: Couldn't write generated header to output file: {e.__class__.__name__} - {e}"
        )
        print(
            "ERROR: Output file could have possibly been overwritten with incomplete/corrupted data!!"
        )
        exit(1)

    print(f"Successfully wrote generated header to {args.out} :3")


if __name__ == "__main__":
    main()
