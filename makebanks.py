from PIL import Image
import wave
import tqdm

if __name__ == "__main__":
    images = []

    try:
        i = 0
        while True:
            i += 1
            if i % 2:
                continue

            img = Image.open(f"frames/{i}.png")
            img = img.convert("L")
            img = img.resize((20, 16), Image.Resampling.NEAREST)
            images.append(img.get_flattened_data())
            img.close()
            print(f"Loading images... ({i} loaded)", end="\r")
    except FileNotFoundError:
        print(f"Loaded {len(images)} images                                 ")

    data = b""

    for imagedata in tqdm.tqdm(images, desc="Processing images"):
        frame_bits = []

        for y in range(16):
            for x in range(20):
                frame_bits.append(0b1 if imagedata[x + (y * 20)] >= 125 else 0b0)
            # for _ in range(12):
            # frame_bits.append(0)

        i = 0
        data += b"\x01" + bytes(frame_bits)

        if len(frame_bits) != 320:
            print(f"WHAT THE FUCK {len(frame_bits)}")

    data += b"\x00"

    print(f"{len(data)} bytes ({len(data) / 1024} KB)")

    with open("frames-unsplit.bin", "wb") as f:
        f.write(data)

    audio_samples = []
    with wave.open("badapple.wav", "rb") as wf:
        audio_samples = wf.readframes(wf.getnframes())

    print(f"Read {len(audio_samples)} audio samples ({len(audio_samples) / 4320.0} s)")

    proc_samples = []
    for sample in tqdm.tqdm(audio_samples, desc="Processing audio samples..."):
        smp = ((sample >> 7) & 0x3) << 5
        proc_samples.append(smp)

    print("Splitting into banks...")

    vbanks = [b""]
    frame_count = 0
    i = 0
    try:
        while True:
            if frame_count > 50:
                while len(vbanks[-1]) < 0x4000:
                    vbanks[-1] += b"\x80"
                vbanks.append(b"")
                frame_count = 0

            byte = data[i]
            if byte == 0x1:
                frame_count += 1
                vbanks[-1] += data[i : i + 321]
                i += 321

            if byte == 0x0:
                vbanks[-1] += b"\x00"
                break
    except IndexError:
        pass

    print(f"{len(vbanks)} video (tilemap) banks")

    sample_count = 0
    i = 0
    abanks = [b""]
    try:
        cur_byte = 0
        cur_bit = 7

        while True:
            if sample_count >= 16384:
                abanks.append(b"")
                cur_byte = 0
                cur_bit = 7
                sample_count = 0

            # if cur_bit < 0:
            #    abanks[-1] += bytes([cur_byte])
            #    cur_byte = 0
            #    cur_bit = 7

            # cur_byte <<= 2
            # cur_byte |= proc_samples[i]
            # i += 2
            # cur_bit -= 2
            # sample_count += 1
            sample_count += 1
            i += 1
            abanks[-1] += bytes([proc_samples[i]])
    except IndexError:
        pass

    print(f"{len(abanks)} audio banks")

    i = 1
    for bank in vbanks:
        if len(bank) > (16 * 1024):
            print(f"I FUCKED UP :3333 V{i} {hex(len(bank))}")
            exit(1)

        with open(f"banks/bank{i}.bin", "wb") as f:
            f.write(bank)
        i += 1

    for bank in abanks:
        if len(bank) > (16 * 1024):
            print(f"I FUCKED UP :3333 A{i} {hex(len(bank))}")
            exit(1)

        with open(f"banks/bank{i}.bin", "wb") as f:
            f.write(bank)
        i += 1
