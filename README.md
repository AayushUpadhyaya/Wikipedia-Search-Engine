# Wikipedia-Search-Engine

This is the repository for the Search engine designed to run on Wikipedia xml data dumps. The data is indexed on 2 levels, and uses a variant of ***tf-idf*** scoring methods to rank the results and return top K results among them.

## Features
  * ***2-Level Indexing*** : Indexing for tokens is done in 2 levels. Level-1 contains all the tokens in sorted order (alphabetically), which are spread across multiple files. Level2 keep track of what range of tokens appear in which file in Level1 to speed up the search process.
  * ***TF-IDF(Term Frequency-Inverse Document Frequency) Scoring*** : To give an order to relevant results, a variant of tf-idf functions are used to rank the documents, which form the part of the result set as a response to search query.
    * ***Sub-Linear TF(Term Frequency) Scaling(W)***: For assigning weights to each term in the search query, we use function f(x)=1+log(tf) (when x > 0) or 0 otherwise, where tf is the frequency of the term occuring in the document.
    * ***Inverse Document Frequency(IDF)*** : For each term in the search query, IDF is calculated as log(N/df) where N is the total documents in the collection and df is document frequency of the term in the collection.
    * ***Term score for document*** : The score of the search term for a document is computed as **W*IDF***.
    * ***Document overall score*** : This is computed as sum of all search term scores that occur in that document.Finally, document with top K scores are returned as result along with document Id and document titles.
  * ***Field search***: We have enabled search also on the fields of the wikipedia articles.These include: ***Title,Body,Infobox,Category,References,External links***, with their field types as t,b,i,c,r,e respectively. To give a field search, just provide fieldtype:query to search. Example, if we want to search for "World cup" in title of the document and "Cricket" in the body of the document, your query would be: "t:World cup b:Cricket".
  
! [Sample image] (/images/Screenshot from 2020-09-06 19-10-23.png)
