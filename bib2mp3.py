#!/usr/bin/env python
import os
import numpy as np
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode

class BibtexLibrary(object):
    """Class that processes bibtex file"""
    def __init__(self,
                 bibfile,
                 mp3dir=os.path.join(os.environ['HOME'],'Music'),
                ):
        parser = BibTexParser(common_strings=True)
        parser.customization = convert_to_unicode
        with open(bibfile) as bib:
            bibdata = bibtexparser.load(bib, parser=parser)
        self.lib = bibdata.entries
        self.mp3dir = mp3dir
        os.makedirs(mp3dir,exist_ok=True)
        self._process_bib_data()

    def _process_bib_data(self):
        self.keys = [article['ID'] for article in self.lib]
        assert len(self.keys) == len(set(self.keys)),\
                'article keys are not unique!'
        self._process_bib_authors()
        self._process_bib_titles()
        self._process_bib_dates()
        self._process_bib_pubnames()
        self._process_bib_keywords()
        self._process_bib_abstracts()

    def _process_bib_authors(self):
        self.author = {}
        for key,article in zip(self.keys,self.lib):
            authorstr = article['author']
            #print(key,authorstr)
            authorlist = [author.strip() for author in authorstr.split(' and ')]
            #print(key,authorlist)
            authorlist_firstlast = []
            for author in authorlist:
                # if "lastname, first", split by comma and reverse
                firstlast = [s.strip() for s in author.split(',')]
                assert (len(firstlast) <= 2) # should be 2 or 1
                firstlast = ' '.join(firstlast[::-1])
                authorlist_firstlast.append(firstlast)
            #print(key,authorlist_firstlast)
            if len(authorlist_firstlast) == 1:
                authorstr = authorlist_firstlast[0]
            elif len(authorlist_firstlast) == 2:
                authorstr = '{:s} and {:s}'.format(*authorlist_firstlast)
            elif len(authorlist_firstlast) == 3:
                authorstr = '{:s}, {:s}, and {:s}'.format(*authorlist_firstlast)
            else:
                authorstr = '{:s} et al'.format(authorlist_firstlast[0])
            #print(key,authorstr)
            self.author[key] = authorstr

    def _process_bib_titles(self):
        self.title = {}
        for key,article in zip(self.keys,self.lib):
            self.title[key] = article['title']

    def _process_bib_dates(self):
        self.date = {}
        for key,article in zip(self.keys,self.lib):
            year = article.get('year',None)
            if year is None:
                self.date[key] = None
            else:
                self.date[key] = year
            month = article.get('month',None)
            if month is not None:
                self.date[key] = '{:s} {:s}'.format(month,year)
        num_missing_dates = np.count_nonzero(
            [(d is None) for _,d in self.date.items()]
        )
        if num_missing_dates > 0:
            print('Note:',
                  num_missing_dates,'/',len(self.lib),
                  'articles are missing dates')

    def _process_bib_pubnames(self):
        self.publication = {}
        for key,article in zip(self.keys,self.lib):
            if article['ENTRYTYPE'] == 'article':
                self.publication[key] = article['journal']
            else:
                self.publication[key] = article.get('booktitle',None)
        num_missing_pubnames = np.count_nonzero(
            [(n is None) for _,n in self.publication.items()]
        )
        if num_missing_pubnames > 0:
            print('Note:',
                  num_missing_pubnames,'/',len(self.lib),
                  'articles are missing publication names')


    def _process_bib_keywords(self):
        self.keywords = {}
        for key,article in zip(self.keys,self.lib):
            self.keywords[key] = article.get('keywords',None)
        num_missing_keywords = np.count_nonzero(
            [(kw is None) for _,kw in self.keywords.items()]
        )
        if num_missing_keywords > 0:
            print('Note:',
                  num_missing_keywords,'/',len(self.lib),
                  'articles are missing keywords')

    def _process_bib_abstracts(self):
        self.abstract = {}
        for key,article in zip(self.keys,self.lib):
            self.abstract[key] = article.get('abstract',None)
        num_missing_abstracts = np.count_nonzero(
            [(ab is None) for _,ab in self.abstract.items()]
        )
        if num_missing_abstracts > 0:
            print('Note:',
                  num_missing_abstracts,'/',len(self.lib),
                  'articles are missing abstracts')


    def generate_descriptions(self):
        self.description = {}
        # minimal information: author, title
        for key in self.keys:
            if self.date[key]:
                desc = 'In {:s}, '.format(self.date[key])
            else:
                desc = ''
            desc += '{:s} published "{:s}"'.format(self.author[key],
                                                   self.title[key])
            if self.publication[key]:
                desc += ' in {:s}.'.format(self.publication[key])
            if self.keywords[key]:
                desc += ' This publication has the following keywords: '
                kwlist = [kw.strip() for kw in self.keywords[key].split(',')]
                if kwlist == 1:
                    kwstr = kwlist[0]
                elif kwlist == 2:
                    kwstr = '{:s} and {:s}'.format(*kwlist)
                else:
                    kwlist[-1] = 'and '+kwlist[-1]
                    kwstr = ', '.join(kwlist)
                desc += kwstr + '.'
            if self.abstract[key]:
                desc += 'The abstract reads: ' + self.abstract[key]
            self.description[key] = desc
            print(desc)


#==============================================================================
if __name__ == '__main__':
    import sys
    if len(sys.argv) <= 1:
        sys.exit('Specify bib file')
    bib = BibtexLibrary(sys.argv[1])
    bib.generate_descriptions()