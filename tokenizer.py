import numpy as np
from gtts.tokenizer.core import Tokenizer
from gtts.tokenizer import tokenizer_cases
import nltk

MAXCHARS = 100


# helper functions:

def consolidate(token_tags):
    for i,tag in enumerate(token_tags):
        if not isinstance(tag,tuple):
            # consolidate tree into token/tag that inherits tag of last leaf
            token_tags[i] = (' '.join([tup[0] for tup in list(tag)]), tag[-1][1])

def reconstruct(token_tags):
    tokenlist = []
    tmp = list(token_tags)
    if tmp[-1][0] == '.':
        tmp.pop(-1)
    while len(tmp) > 0:
        counts = [len(tup[0])+1 for tup in tmp]
        N = np.count_nonzero(np.cumsum(counts) <= MAXCHARS)
        newtoken = ' '.join([tup[0] for tup in tmp[:N]])
        tokenlist.append(newtoken)
        tmp = tmp[N:]
    return tokenlist


# Setup chunker - the magic is here

grammar = """
NounWithPrepositionalPhrase:
    {(<DT>|<CD>)<JJ>*<NN.?>+<IN><DT>?<JJ.?>*<NN.?>+}
    {<IN>(<DT>|<CD>)?<JJ.?>*(<NN.?>+|<PRP.?>)}
NounPhrase:
    {(<DT>|<CD>)*<JJ.?>*<NN.?>+}
VerbPhrase:
    {<MD>?<RB.?>?<VB.?>+<RB.?>?<JJ.?>*}
    {<TO><RB.?>?<VB.?><RB.?>?<NN.?>+}
"""
chunker = nltk.RegexpParser(grammar)


# tokenizers

tokenizer = Tokenizer([
    tokenizer_cases.tone_marks,  # gTTS default
    tokenizer_cases.period_comma,  # gTTS default
    tokenizer_cases.other_punctuation,  # gTTS default
    #tokenizer_cases.colon,
])

def default_tokenizer(text):
    return tokenizer.run(text)

def MyTokenizer(text,debug=False):
    # first, use the default gTTS tokenizer
    default_tokens = default_tokenizer(text)
    tokens = []
    for i,token in enumerate(default_tokens):
        if len(token) > MAXCHARS:
            if debug:
                print('---')
                print(f'Splitting "{token}"...')
            # first split by ':'
            for phrase in token.split(':'):
                if len(phrase) <= MAXCHARS:
                    # add token if it's short enough
                    tokens.append(phrase)
                    if debug: print(phrase)
                else:
                    # then split into words and tag with parts of speech
                    words = nltk.word_tokenize(phrase)
                    word_tags = nltk.pos_tag(words)
                    # next, chunk what's left
                    chunked = chunker.parse(word_tags)
                    # group words to make sure key phrases don't get broken up
                    consolidate(chunked)
                    if debug:
                        for token_pos in chunked:
                            print(' ',token_pos)
                    # add reconstructed tokens that are within the char limit 
                    tokens += reconstruct(chunked)
            if debug:
                print(f'Result: "{token}"')
        else:
            tokens.append(token)
    return tokens

