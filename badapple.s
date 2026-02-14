SECTION "WorkRAM0", WRAM0[$C000]
    wCurrentVideoBank: ds 1
    wCurrentAudioBank: ds 1
    wCurrentFrameHalf: ds 1
    wSkipFrame: ds 1
    wSkipSample: ds 1

SECTION "RSTVector", ROM0[$0]
    REPT 8
        rst $38
        REPT 7
            nop
        ENDR
    ENDR

SECTION "InterruptVector", ROM0[$40]
    ; VBlank
    jp VBlankHandler
    REPT 5
        nop
    ENDR

    ; LCD STAT
    jp HBlankHandler
    REPT 5
        nop
    ENDR

    ; everything else
    REPT 3
        rst $38
        REPT 5
            nop
        ENDR
    ENDR

SECTION "EntryPoint", ROM0[$100]
    jp EntryPoint

SECTION "ROM0Code", ROM0[$150]
    EntryPoint:
        ; Disable LCD
        call WaitForVBlank
        ld a, 0
        ldh [$FF40], a

        ; Initialize VRAM, WRAM and OAM
        ld a, $00

        ld hl, $8000
        ld de, $1FFF
        call FillMemory

        ld hl, $C000
        ld de, $1FFF
        call FillMemory

        ld hl, $FE00
        ld de, $9F
        call FillMemory

        ; Copy tile data to VRAM
        ld hl, VRAMTiles
        ld de, $8000
        ld b, (8 * 2 * 3)
        call CopyMemory

        ; Set up BG & OBJ palletes
        ld a, %10010011
        ldh [$FF47], a
        ldh [$FF48], a
        ldh [$FF49], a

        ld a, $02
        ld hl, $9C00
        ld de, 20
        call FillMemory

        ld hl, $9E20
        ld de, 20
        call FillMemory

        ; Init sound channels 1, 2 and 4
        ld a, 0
        ldh [$FF10], a
        ldh [$FF11], a
        ldh [$FF12], a
        ldh [$FF13], a
        ldh [$FF14], a

        ldh [$FF16], a
        ldh [$FF17], a
        ldh [$FF18], a
        ldh [$FF19], a

        ldh [$FF20], a
        ldh [$FF21], a
        ldh [$FF22], a
        ldh [$FF23], a

        ; Init sound engine (APU + channel 3)
        ld a, %01110111
        ldh [$FF24], a

        ld a, %01000100
        ldh [$FF25], a

        ld a, %10000000
        ldh [$FF26], a

        ld a, %01100000
        ldh [$FF1C], a

        ld a, $FF
        ldh [$FF1D], a

        ld a, %10000111
        ldh [$FF1E], a

        ld a, $80
        ldh [$FF1A], a

        ld a, $FF
        ld hl, $FF30
        REPT 16
            ldi [hl], a
        ENDR

        ; Initialize variables and registers
        ld a, $01
        ld [wCurrentVideoBank], a
        ld hl, $4000
        ld bc, $4000
        ld a, 66
        ld [wCurrentAudioBank], a
        ld a, $00
        ld [wCurrentFrameHalf], a

        ; Enable HBlank interrupts
        ld a, %00001000
        ldh [$FF41], a

        ; Enable LCD
        ld a, %10011001
        ldh [$FF40], a

        ; Enable interrupts
        ei
        ld a, $00
        ldh [$FF0F], a
        ld a, $FF
        ldh [$FFFF], a

        ; Off we go! :3
        .wait_for_interrupt:
            halt
            nop
            jr .wait_for_interrupt

        ; hl = video ROM read pointer
        ; de = VRAM/WRAM write pointer
        ; bc = audio ROM read pointer

    HBlankHandler:
        ld a, [wSkipSample]
        xor $01
        jr nz, .skip
        ld [wSkipSample], a

        ld a, [wCurrentAudioBank]
        ld [$2000], a

        ld a, $FF
        cp c
        jr nz, .update_dac
        ld a, $7F
        cp b
        jr nz, .update_dac

        ld a, [wCurrentAudioBank]
        inc a
        ld [$2000], a
        ld [wCurrentAudioBank], a
        ld bc, $4000

        .update_dac:
            ld a, [bc]
            ldh [$FF1C], a
            inc bc
            ld a, %10000111
            ldh [$FF1E], a

        ld a, [wCurrentVideoBank]
        ld [$2000], a

        reti

        .skip:
            ld [wSkipSample], a
            reti


    VBlankHandler:
        ld a, $00
        ldh [$FF0F], a

        ld a, [wSkipFrame]
        and a
        jr z, .do_not_skip_frame
        ld a, 0
        ld [wSkipFrame], a
        reti

        .do_not_skip_frame

        ld a, [wCurrentFrameHalf]
        xor $01
        ld [wCurrentFrameHalf], a
        ld de, $9D20
        jr z, .copy_video

        ; Check if a ROM bank switch is needed
        ld a, $FF
        cp l
        jr nz, .after_bank_check_1
        ld a, $7F
        cp h
        jr nz, .after_bank_check_1
        call NextVideoBank
        jr VBlankHandler

        .after_bank_check_1

        ; Load and check command
        ; %00000000 = End playback
        ; %10000000 (bit 7 set) = Switch to next ROM bank
        ; Anything else = Load frame
        ldi a, [hl]
        and a
        jp z, EndPlayback
        rlca
        jr nc, .after_bank_check_2
        call NextVideoBank
        jr VBlankHandler

        .after_bank_check_2

        ; Set de to point to VRAM
        ld de, $9C20

        .copy_video:
        REPT 8
            REPT 20
                ldi a, [hl] ; 8
                ld [de], a ; 8
                inc de ; 8
            ENDR
            ld a, 12
            add e
            ld e, a
            ld a, d
            adc 0
            ld d, a
        ENDR

        ld a, $01
        ld [wSkipFrame], a

        reti

    EndPlayback:
        ld a, $00
        ldh [$FFFF], a
        ldh [$FF0F], a
        di
        halt
        nop

    FillMemory:
        ; hl = start/current address
        ; de = how many bytes to fill
        ; a = value to fill with

        push af

        .loop:
            pop af
            ldi [hl], a
            push af
            dec de
            ld a, e
            and a
            jr nz, .loop
            ld a, d
            and a
            jr nz, .loop
        pop af
        ret

    CopyMemory:
        ; hl = source area start/current address
        ; de = destination area start/currnt address
        ; b = bytes to copy

        push af

        .loop:
            ldi a, [hl]
            push hl
            push de
            pop hl
            ldi [hl], a
            push hl
            pop de
            pop hl
            dec b
            jr nz, .loop

        pop af
        ret

    WaitForVBlank:
        push af
        push hl
        ld a, 143
        ld hl, $FF44
        .loop:
            cp [hl]
            jr nc, .loop
        pop hl
        pop af
        ret

    NextVideoBank:
        ld a, [wCurrentVideoBank]
        inc a
        ld [wCurrentVideoBank], a
        ld [$2000], a
        ld a, 0
        ld [wCurrentFrameHalf], a
        ld hl, $4000
        ret

    VRAMTiles:
        REPT 8
            db $00, $00
        ENDR
        REPT 8
            db $FF, $00
        ENDR
        REPT 4
            db %10101010, %11111111
            db %01010101, %11111111
        ENDR

INCLUDE "banks.s"
