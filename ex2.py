import music21
from firms.stemmers import get_voice_lines
from firms.models import get_part_details, get_snippets_for_part

piece = music21.corpus.parse("bwv248.9-1.xml")
offset = 1
part_number = 0
part_details = list(get_part_details(piece))
part_snippets = list(get_snippets_for_part(part_details[part_number]))
sample = part_snippets[offset]
print("Before voicing")
print(sample.simple_line())
voices = get_voice_lines(sample.notes)
print("After voicing")
for voice in voices:
    print(voice)