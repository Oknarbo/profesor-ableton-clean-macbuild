try:
    from mido import Message, MidiFile, MidiTrack  # type: ignore
except ImportError as e:
    print(f"Error: Missing mido package - {e}")
    print("Install with: pip install mido")
    exit(1)

# Create MIDI file for C major chord
mid = MidiFile()
track = MidiTrack()
mid.tracks.append(track)

# Add C major chord (C4, E4, G4 = 60, 64, 67)
track.append(Message("note_on", note=60, velocity=100, time=0))
track.append(Message("note_on", note=64, velocity=100, time=0))
track.append(Message("note_on", note=67, velocity=100, time=0))
track.append(Message("note_off", note=60, velocity=100, time=480))  # 480 ticks = 1 beat
track.append(Message("note_off", note=64, velocity=100, time=0))
track.append(Message("note_off", note=67, velocity=100, time=0))

mid.save("c_major_chord.mid")
print("C major chord saved! Import to Ableton later.")