import sys
import sets
from vectorspace import vsm, retrieveDocuments
import json
import os
from preprocess import *
from operator import itemgetter
from math import log10

def suggest(queries, vectorspace, page_rank):
  for q in queries:
    query = q.lower()
    if 'prequelmemes' in query:
      print('A surprise to be sure, but a welcome one!')

    suggested_docs = {}
    docs = []
    results = []
    if 'r/' in query:
      if query[2:] in comment_corpus:
        suggested_docs = retrieveDocuments(comment_corpus[query[2:]], vectorspace[0], vectorspace[1])
    elif '/r/' in query:
      if query[3:] in comment_corpus:
        suggested_docs = retrieveDocuments(comment_corpus[query[3:]], vectorspace[0], vectorspace[1])
    elif query in comment_corpus:
      suggested_docs = retrieveDocuments(comment_corpus[query], vectorspace[0], vectorspace[1])
    else:
      tokenized_query = tokenizeText(query)
      tokenized_query = removeStopwords(tokenized_query)
      tokenized_query = stemWords(tokenized_query)
      suggested_docs = retrieveDocuments(tokenized_query, vectorspace[0], vectorspace[1])

    if suggested_docs == {}:
      print('Sorry, we could not find anything for you')
      print('Please try a more specific query, and in the')
      print('meantime, here are our favorite Subreddits!')
      for x in xrange(10):
        print('--> prequelmemes')
      print('~~~~~~~~~~~~~~~~~~')
      continue

    for key in suggested_docs:
      pair = (key, suggested_docs[key])
      docs.append(pair)
    docs.sort(key=lambda x: x[1], reverse=True)

    for x in xrange(30):
      if x >= len(docs):
        break
      doc_score = docs[x][1]
      if docs[x][0] in page_rank:
        doc_score += log10(float(page_rank[docs[x][0]]))
      weighted_term = (docs[x][0], doc_score)
      results.append(weighted_term)
    results.sort(key=lambda x: x[1], reverse=True)
    print('Query: ' + query)
    if len(results) >= 10:
      for pair in results[0:9]:
        print('--> ' + str(pair[0]) + ' ' + str(pair[1]))
      print('~~~~~~~~~~~~~~~~~~')
    else:
      for pair in results:
        print('--> ' + str(pair[0]) + ' ' + str(pair[1]))
      print('~~~~~~~~~~~~~~~~~~')
  return

page_rank = {}
pr_input = open('redditPagerankings', 'r')
for line in pr_input:
  sub = line.split()[0]
  score = line.split()[1]
  page_rank[sub] = score

tfidf_input = json.load(open('tfidf_index.json', 'r'))
toke_in = json.load(open('toke_freqs.json', 'r'))
vectorspace = [tfidf_input, toke_in]

comment_input = open('comments.json', 'r')
comment_corpus = json.load(comment_input)
if vectorspace == []:
  print('... Preparing tf-idf inverted index ...')
  index = open('tfidf_index.json', 'w')
  tokeF = open('toke_freqs.json', 'w')
  vectorspace = vsm(comment_corpus)
  json.dump(vectorspace[0], index)
  json.dump(vectorspace[1], tokeF)

#If given a file, read in queries from file,
#else, prompt user for a query
queries = []
if len(sys.argv) == 2:
  query_file = open(sys.argv[1], 'r')
  for line in query_file:
    queries.append(line.strip())
  suggest(queries, vectorspace, page_rank)

else:
  while True:
    q = raw_input('Enter Query: ')
    if q.lower() == 'h' or q.lower() == 'help':
      print('Type \'quit\' to exit, or any other term or terms to query a suggestion')
      print('  --crawl  -Start a new crawl of Subreddits to refresh the data')
    elif q.lower() == 'quit':
      exit(1)
    elif q == '--crawl':
      #Crawl over all the Subreddits in the tracked_subreddits file
      #Placing returned json commment trees under the ./r/ directory
      execfile('python commentArchiver.py &')
      #Parse all the comments placed in the ./r/ directory for each
      # subreddit
      execfile('python parseComments.py &')
      #Update the pageRank
      execfile('python RedditRank.py userLinks.txt')

      page_rank = {}
      pr_input = open('redditPagerankings', 'r')
      for line in pr_input:
        sub = line.split()[0]
        score = line.split()[1]
        page_rank[sub] = score

      comment_input = open('comments.json', 'r')
      comment_corpus = json.load(comment_input)

      #update the tf-idf inverted index
      print('... Updating tf-idf inverted index ...')
      vectorspace = vsm(comment_corpus)
    else:
      queries.append(q)
      suggest(queries, vectorspace, page_rank)
      queries = []
