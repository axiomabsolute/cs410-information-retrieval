# from music21 import corpus
# from graders import simple_sum_grader
# from stemmers import index_key_by_pitch
# from models import MemoryIRSystem
# import random

# pieces = list((corpus.parse(piece) for piece in corpus.getComposer('bach')[:10]))

# index_methods = {
#     'By Pitch': index_key_by_pitch
# }

# scorer_methods = {
#     'Simple Sum': simple_sum_grader
# }

# irsystem = MemoryIRSystem(index_methods, scorer_methods, pieces)
# all_snippets = get_snippets_for_pieces(pieces)
# random_snippet = random.choice(all_snippets)
# irsystem.lookup(random_snippet)

# random_snippets = random.sample(all_snippets, 20)
# scores = [irsystem.lookup(s) for s in random_snippets]
# print(list(zip(random_snippets, scores)))

# print("This is where the interactive CLI will live")