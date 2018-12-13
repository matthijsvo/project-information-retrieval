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
    q0 = get_score_vector(ireader, alpha, terms=tokens)

    # Generate score vector for relevant documents
    if relevantIDs:
        drv = get_score_vector(ireader, beta, docs=relevantIDs)

    # Generate score vector for nonrelevant documents
    if nonrelevantIDs:
        dnrv = get_score_vector(ireader, gamma, docs=nonrelevantIDs)

    # Merge score vectors following Rocchio formula. Weights have already been applied
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
    best = bestterms[:len(tokens) + maxaddedterms]
    # print([(t, q1[t]) for t in best])
    return " ".join(best)


def tfidf_score(ireader, docID, term, field='text'):
    """
    Provides TF-IDF score of a single term in a single document.

    :param ireader: IndexReader.
    :param docID: Document ID.
    :param term: term string.
    :param field: optional, document field.
    :return: TF-IDF score.
    """
    # TF
    tf = get_doc_frequency(ireader, docID, term, field)

    # IDF
    occurences = ireader.docFreq(Term(field, term))
    totaldocs = ireader.numDocs()
    idf = math.log10(totaldocs / occurences)

    return tf * idf


def get_doc_frequency(indexReader, docID, term, field='text'):
    """
    Returns frequency of term within a single document

    :param indexReader: IndexReader object of your index
    :param docID: ID of the document
    :param term: string
    :param field: document field term is a part of
    :return:
    """
    termvec = indexReader.getTermVector(docID, field)
    it = termvec.iterator()

    found = it.seekExact(Term(field, term).bytes())
    if not found:
        return 0
    postings = it.postings(None, PostingsEnum.FREQS)
    postings.nextDoc()
    return postings.freq()


def get_terms(indexReader, field='text'):
    """
    Gets all terms in an index.

    :param indexReader: IndexReader object of your index
    :param field: document field from which terms should be counted
    :return: list of terms (strings)
    """
    terms = []
    multiterms = MultiFields.getTerms(indexReader, field)
    termit = multiterms.iterator()
    it = BytesRefIterator.cast_(termit)  # Inheritance apparently doesn't work in PyLucene...
    term = it.next()
    while term:
        terms.append(term.utf8ToString())
        term = it.next()
    return terms


def get_score_vector(ireader, weight, docs=None, terms=None, field='text'):
    """
    Creates TF-IDF score vector with a certain weight over either the provided terms, or all terms in the given index.

    :param ireader: index reader with documents.
    :param weight: weight for scores, results will be multiplied with this number.
    :param docs: optional list of documents to use for term frequencies exclusively, otherwise calculated over all docs in index
    :param terms: optional list of terms to get a score vector of.
    :param field: optional document field in which terms occur.
    :return: score vector (dict object term -> TF-IDF score).
    """
    scorevector = {}

    if not terms:
        # If terms nor specific documents aren't supplied, gather all from index
        if not docs:
            terms = get_terms(ireader, field)
        # If documents are specified, gather all terms in those
        else:
            # This is a very cheat-y way of doing this but it works and is less complicated than using TermEnum iterators
            tempindex = indexer.create_miniindex([ireader.document(i) for i in docs])
            tempreader = DirectoryReader.open(tempindex)
            terms = get_terms(tempreader, field)
            tempreader.close()

    # Calculate TF-IDF for every term
    totaldocs = ireader.numDocs()
    for term in terms:
        tf = 0
        if not docs:
            # If no specific docs are specified, look over all
            tf = math.sqrt(ireader.totalTermFreq(Term(field, term)))
        else:
            tf = math.sqrt(sum([get_doc_frequency(ireader, doc, term) for doc in docs]))

        occurences = ireader.docFreq(Term(field, term))
        idf = math.log((totaldocs + 1.0) / (occurences + 1.0)) + 1.0
        scorevector[term] = weight * tf * idf

    return scorevector
