from machine import Pin, I2S
import _thread
import time
import math

# ============================================================
# SETTINGS
# ============================================================

MUSIC_FILE = "Arcade.wav"

# MAX98357A
BCLK_PIN = 10
LRC_PIN  = 11
DIN_PIN  = 12

# Arcade.wav actual format
SAMPLE_RATE = 11025
BUFFER_SIZE = 2048

# Volume
VOLUME = 10

# Band-pass filter
# Start with OFF to verify clean audio first
FILTER_ENABLED = True

# Arcade music filter range
LOW_CUTOFF = 120
HIGH_CUTOFF = 6000


# ============================================================
# INTERNAL
# ============================================================

_i2s = None

_playing = False
_started = False

# Filter state
_hp_x = 0.0
_hp_y = 0.0
_lp_y = 0.0


# ============================================================
# I2S INIT
# ============================================================

def init():

    global _i2s

    if _i2s is not None:
        return

    _i2s = I2S(
        0,
        sck=Pin(BCLK_PIN),
        ws=Pin(LRC_PIN),
        sd=Pin(DIN_PIN),
        mode=I2S.TX,
        bits=16,
        format=I2S.MONO,
        rate=SAMPLE_RATE,
        ibuf=30000
    )

    print("I2S initialized")
    print("Sample rate:", SAMPLE_RATE)
    print("Bits: 16")
    print("Format: MONO")


# ============================================================
# FIND WAV DATA
# ============================================================

def find_data_chunk(f):

    f.seek(12)

    while True:

        header = f.read(8)

        if len(header) < 8:
            return None

        chunk_id = header[0:4]

        chunk_size = int.from_bytes(
            header[4:8],
            "little"
        )

        if chunk_id == b"data":

            return (
                f.tell(),
                chunk_size
            )

        # WAV chunks are word aligned
        skip = chunk_size

        if skip & 1:
            skip += 1

        f.seek(skip, 1)


# ============================================================
# CONVERT 8-BIT PCM TO 16-BIT PCM
# ============================================================

def convert_8bit_to_16bit(
    input_buffer,
    count,
    output_buffer
):

    out = 0

    for i in range(count):

        # ----------------------------------------------------
        # 8-bit PCM WAV:
        #
        # 0      = negative maximum
        # 128    = silence
        # 255    = positive maximum
        # ----------------------------------------------------

        sample = input_buffer[i]

        # Convert unsigned 8-bit -> signed 16-bit
        sample = (
            (sample - 128)
            << 8
        )

        # Apply volume
        sample = int(
            sample * VOLUME
        )

        # Clip
        if sample > 32767:
            sample = 32767

        elif sample < -32768:
            sample = -32768

        # Signed -> unsigned representation
        if sample < 0:
            sample += 65536

        # Little-endian 16-bit
        output_buffer[out] = (
            sample & 0xFF
        )

        output_buffer[out + 1] = (
            (sample >> 8) & 0xFF
        )

        out += 2

    return out


# ============================================================
# BAND-PASS FILTER
# ============================================================

def filter_audio(
    buffer,
    count
):

    global _hp_x
    global _hp_y
    global _lp_y

    # --------------------------------------------------------
    # High-pass
    # --------------------------------------------------------

    rc_high = 1.0 / (
        2.0 * math.pi * LOW_CUTOFF
    )

    dt = 1.0 / SAMPLE_RATE

    alpha_hp = (
        rc_high /
        (rc_high + dt)
    )

    # --------------------------------------------------------
    # Low-pass
    # --------------------------------------------------------

    rc_low = 1.0 / (
        2.0 * math.pi * HIGH_CUTOFF
    )

    alpha_lp = (
        dt /
        (rc_low + dt)
    )

    for i in range(
        0,
        count,
        2
    ):

        # ----------------------------------------------------
        # Read 16-bit signed PCM
        # ----------------------------------------------------

        sample = (
            buffer[i]
            |
            (buffer[i + 1] << 8)
        )

        if sample >= 32768:
            sample -= 65536

        # ----------------------------------------------------
        # High-pass
        # ----------------------------------------------------

        hp = (
            alpha_hp *
            (
                _hp_y +
                sample -
                _hp_x
            )
        )

        _hp_x = sample
        _hp_y = hp

        # ----------------------------------------------------
        # Low-pass
        # ----------------------------------------------------

        lp = (
            _lp_y +
            alpha_lp *
            (hp - _lp_y)
        )

        _lp_y = lp

        output = int(lp)

        # Clip
        if output > 32767:
            output = 32767

        elif output < -32768:
            output = -32768

        # Signed -> unsigned
        if output < 0:
            output += 65536

        buffer[i] = output & 0xFF

        buffer[i + 1] = (
            (output >> 8) & 0xFF
        )


# ============================================================
# RESET FILTER
# ============================================================

def reset_filter():

    global _hp_x
    global _hp_y
    global _lp_y

    _hp_x = 0.0
    _hp_y = 0.0
    _lp_y = 0.0


# ============================================================
# MUSIC THREAD
# ============================================================

def music_thread():

    global _playing
    global _started

    # --------------------------------------------------------
    # Input:
    # 8-bit WAV
    # --------------------------------------------------------

    input_buffer = bytearray(
        BUFFER_SIZE
    )

    # --------------------------------------------------------
    # Output:
    # 16-bit I2S
    #
    # 1 input byte -> 2 output bytes
    # --------------------------------------------------------

    output_buffer = bytearray(
        BUFFER_SIZE * 2
    )

    print("Music started")

    reset_filter()

    while _playing:

        try:

            with open(
                MUSIC_FILE,
                "rb"
            ) as f:

                result = find_data_chunk(f)

                if result is None:

                    print(
                        "ERROR: WAV data not found"
                    )

                    _playing = False
                    break

                data_start = result[0]
                data_size = result[1]

                print(
                    "WAV data:",
                    data_size,
                    "bytes"
                )

                f.seek(data_start)

                remaining = data_size

                while (
                    _playing
                    and
                    remaining > 0
                ):

                    # ------------------------------------------------
                    # Read 8-bit WAV data
                    # ------------------------------------------------

                    amount = min(
                        BUFFER_SIZE,
                        remaining
                    )

                    count = f.readinto(
                        memoryview(
                            input_buffer
                        )[:amount]
                    )

                    if count <= 0:
                        break

                    # ------------------------------------------------
                    # Convert 8-bit -> 16-bit
                    # ------------------------------------------------

                    output_count = (
                        convert_8bit_to_16bit(
                            input_buffer,
                            count,
                            output_buffer
                        )
                    )

                    # ------------------------------------------------
                    # Optional band-pass
                    # ------------------------------------------------

                    if FILTER_ENABLED:

                        filter_audio(
                            output_buffer,
                            output_count
                        )

                    # ------------------------------------------------
                    # Send to MAX98357A
                    # ------------------------------------------------

                    _i2s.write(
                        memoryview(
                            output_buffer
                        )[:output_count]
                    )

                    remaining -= count

            # --------------------------------------------------------
            # LOOP
            # --------------------------------------------------------

            if _playing:

                reset_filter()

                time.sleep_ms(5)

        except Exception as e:

            print(
                "Audio error:",
                e
            )

            time.sleep_ms(500)

    _started = False

    print("Music stopped")


# ============================================================
# PLAY
# ============================================================

def play():

    global _playing
    global _started

    init()

    if _playing:
        return

    _playing = True

    if not _started:

        _started = True

        _thread.start_new_thread(
            music_thread,
            ()
        )

    print("Music ON")


# ============================================================
# STOP
# ============================================================

def stop():

    global _playing

    _playing = False

    print("Music OFF")


# ============================================================
# STATUS
# ============================================================

def is_playing():

    return _playing