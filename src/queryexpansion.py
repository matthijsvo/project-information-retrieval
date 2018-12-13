import math
import lucene
from java.io import StringReader
from org.apache.lucene.index import IndexReader, DirectoryReader, Term, TermsEnum, PostingsEnum, MultiFields
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.analysis.tokenattributes import CharTermAttribute
from org.apache.lucene.util import BytesRefIterator

import indexer


def rocchio(ireader, query, relevantIDs, nonrelevantIDs, maxaddedterms=5, tfidfthresh=0.0, alpha=1.0, beta=0.75, gamma=0.15):
    """
    Performs the Rocchio Query Expansion algorithm to provide additional relevant query terms.

    :param ireader: IndexReader object (you'll probably want to use the one available during search).
    :param query: Query string, the raw string from the user.
    :param relevantIDs: Document IDs of all relevant documents.
    :param nonrelevantIDs: Document IDs of all non-relevant documents.
    :param maxaddedterms: The maximum amount of terms appended to the expanded query (can be combined with tfidfthresh). Default: 5
    :param tfidfthresh: TF-IDF threshold for all query terms (can be combined with maxaddedterms). Default: 0
    :param alpha: Rocchio alpha weight (original query vector). Default: 1.0
    :param beta: Rocchio beta weight (relevant docs query vector). Default: 0.75
    :param gamma: Rocchio gamma weight (non-relevant docs query vector). Default: 0.15
    :return: Query string.

    Weight defaults were sourced from: https://nlp.stanford.edu/IR-book/html/htmledition/the-rocchio71-algorithm-1.html
    """
    # Fetch all relevant documents
    alldocs = []
    for i in relevantIDs + nonrelevantIDs:
        alldocs.append(ireader.document(i))

    # All score vectors we'll be using
    q0 = {}
    drv = {}
    dnrv = {}

    # Process query into tokens
    analyzer = StandardAnalyzer()
    stream = analyzer.tokenStream("", StringReader(query))
    stream.reset()
    tokens = []
    while stream.incrementToken():
        tokens.append(stream.getAttribute(CharTermAttribute.class_).toString())

    # (Re)generate score vector for current query
    q_index = indexer.create_miniindex(alldocs)
    q0 = get_score_vector(q_index, alpha, terms=tokens)

    # Generate score vector for relevant documents
    if relevantIDs:
        dr = alldocs[:len(relevantIDs)]
        dr_index = indexer.create_miniindex(dr)
        drv = get_score_vector(dr_index, beta)
        dr_index.close()

    # Generate score vector for nonrelevant documents
    if nonrelevantIDs:
        dnr = alldocs[-len(nonrelevantIDs):]
        dnr_index = indexer.create_miniindex(dnr)
        dnrv = get_score_vector(dnr_index, gamma)
        dnr_index.close()

    # Merge score vectors
    q1 = q0
    for key, value in drv.items():
        if key in q1:
            q1[key] += value
        else:
            q1[key] = value
    for key, value in dnrv.items():
        if key in q1:
            q1[key] -= value
        else:
            q1[key] = value

    # Return all the best terms
    # Terms are narrowed down using both a TF-IDF threshold and a maximum amount of terms
    # The TF-IDF threshold is 0 (i.e. ignored) by default
    bestterms = sorted([t for t in q1.keys() if q1[t] > tfidfthresh], key=lambda x: q1[x], reverse=True)
    return " ".join(bestterms[:len(tokens)+maxaddedterms])


def tfidf_score(ireader, docID, term, field='text'):
    """
    Provides TF-IDF score of a single term in a single document.

    :param ireader: IndexReader.
    :param docID: Document ID.
    :param term: term string.
    :param field: optional, document field.
    :return: TF-IDF score.
    Currently unused but included because I wasted far too much time on this.
    """
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


def get_score_vector(docIndex, weight, terms=[], field='text'):
    """
    Creates TF-IDF score vector with a certain weight over either the provided terms, or all terms in the given index.

    :param docIndex: index object with documents.
    :param weight: weight for scores, results will be multiplied with this number.
    :param terms: optional list of terms to get a score vector of.
    :param field: optional document field in which terms occur.
    :return: score vector (dict object term -> TF-IDF score).
    """
    ireader = DirectoryReader.open(docIndex)
    scorevector = {}

    # If terms aren't supplied, gather all from index
    if not terms:
        multiterms = MultiFields.getTerms(ireader, field)
        termit = multiterms.iterator()
        it = BytesRefIterator.cast_(termit) # Inheritance apparently doesn't work in PyLucene...
        term = it.next()
        while term:
            terms.append(term.utf8ToString())
            term = it.next()

    # Calculate TF-IDF for every word
    totaldocs = ireader.numDocs()
    for term in terms:
        tf = math.sqrt(ireader.totalTermFreq(Term(field, term)))
        occurences = ireader.docFreq(Term(field, term))
        idf = math.log(totaldocs / (occurences + 1)) + 1
        scorevector[term] = weight * tf * idf

    ireader.close()
    return scorevector
