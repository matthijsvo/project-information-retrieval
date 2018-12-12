import math
import lucene
from java.io import StringReader
from org.apache.lucene.index import IndexReader
from org.apache.lucene.index import Term, PostingsEnum
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.analysis.tokenattributes import CharTermAttribute


def expand_query(ireader, query, relevantIDs, nonrelevantIDs):
    alpha = 1.0
    beta = 0.75
    gamma = 0.15

    # First process query into tokens
    analyzer = StandardAnalyzer()
    stream = analyzer.tokenStream("", StringReader(query))
    stream.reset()
    tokens = []
    while stream.incrementToken():
        tokens.append(stream.getAttribute(CharTermAttribute.class_).toString())

    # Original query vector
    q0 = {}
    for token in tokens:
        q0[token] = alpha # * tfidf_score(ireader, ) # TODO
        pass

    # Relevant docs vector
    dr = get_score_vector(ireader, relevantIDs)

    # Non-relevant docs vector
    dnr = get_score_vector(ireader, nonrelevantIDs)

    # Sum vectors
    queryvec = {}
    for v in (q0, dr, dnr):
        for key, value in v.items():
            if queryvec[key]:
                queryvec[key] += value
            else:
                queryvec[key] = value


def tfidf_score(ireader, docID, term, field='text'):
    # TF
    termvec = ireader.getTermVector(docID, field)
    it = termvec.iterator()

    found = it.seekExact(Term(field, term).bytes())
    if not found:
        raise Exception("Term '{}' not found in document (ID: {})!".format(term, docID))
    postings = it.postings(None, PostingsEnum.FREQS)
    postings.nextDoc()
    tf = postings.freq()

    # IDF
    occurences = ireader.docFreq(Term(field, term))
    totaldocs = ireader.numDocs()
    idf = math.log10(totaldocs / occurences)

    return tf * idf


def get_score_vector(ireader, docIDs):
    return {}


if __name__ == '__main__':
    lucene.initVM()
    expand_query(None, "When the flush of a newborn sun fell first on Eden's green and gold, our father Adam sat under the tree and scratched with a stick in the mould. And the first rude sketch the world had seen was joy to his mighty heart... till the Devil whispered behind the leaves \"It's pretty, but is it art\"")