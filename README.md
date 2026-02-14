# Bad Apple for the GameBoy (DMG)

## Stats

🖥️ **Video:** 20x16 1bpp @ ~30FPS

🔉 **Sound:** 4320Hz 2bpp via [Pokemon Yellow/Wave Channel DAC](https://www.youtube.com/watch?v=fooSxCuWvZ4) trick

💾 **Storage:** MBC3, 128 bank mode (123 banks [~1.9MB] used)

🎛️ **Hardware:** Will run on any DMG-CPU GameBoy-compatible device

## FAQ

### Are other videos possible?

They should be - `makebanks.py` can take any number of frames and any audio - however, the MBC3 has a 128 bank limit, so all of the data shouldn't exceed 2 MB

### Does this implement any compression?

No, as they wouldn't fit into the interrupt timings (the VBlank is already a tight fit).

### Does this work on real hardware?

**YES!** Proof: https://youtu.be/dTDWjWFa-xQ (thanks @Dominicentek)

### How do I compile this?

rgbds is required for this - https://rgbds.gbdev.io/

Step 1. Obtain the frames and audio

- Frames can be easily obtained via ffmpeg:
  `ffmpeg -i badapple.mp4 "frames/%d.png"`

- Audio **MUST BE 4320Hz** for correct playback

Step 2. Generate bank files

    - Run `makebanks.py` to generate the data banks themselves IF CHANGING VIDEO: change the value at line 134 in badapple.s (`ld a, 66`) to the number of video banks plus one

    - Run `genbankinclude.py <total number of banks>` to generate `banks.s`

Step 3. Assemble

```
rgbasm badapple.s -o badapple.o
```

Step 4. Link

```
rgblink badapple.o -o badapple.gb -n badapple.sym -m badapple.map
```

Step 5. Add a header to the ROM file (you can use `gbromheader.py` or `rgbfix` for this) - NOTE THAT THE NINTENDO LOGO AND HEADER CHECKSUM HAVE TO BE CORRECT FOR THE GAME TO WORK ON REAL HARDWARE!!

Step 6. Run the ROM on an emulator or flash it to an MBC3-capable flashcart
