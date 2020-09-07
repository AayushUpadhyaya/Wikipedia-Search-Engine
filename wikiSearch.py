import os
import sys
import re
from Stemmer import Stemmer
from spacy.lang.en.stop_words import STOP_WORDS
from math import log
import operator
import time


fileDirectories=['./InvertedIndex/','./DocumentTitles/']

class WikiSearch:

	def __init__(self):

		self.searchTokens=[]
		self.isfieldQuery=0
		self.fieldTokens=['t','b','c','i','e','r']
		self.searchType=[0,0,0,0,0,0]
		self.tokenDict={}
		self.fieldInputDict={}
		self.termPostingListDict={}
		self.singleTermQuery = 0
		self.termDocIdDict = {}
		self.termIDFDict = {}
		self.termDocIdFreqDict={}
		self.vocabularySize = 0
		self.termDocIdScoreDict = {}
		self.intersectionDocIdList = None
		self.documentScoreDict = {}
		self.topK = 5
		self.handlingFieldQuery = 0
		self.currentFieldType = None
		self.readTotalDocumentVocabCount()
		self.secondaryIndexTermList = None
		self.secondaryTitleIdList = None


	def readTotalDocumentVocabCount(self):
		ifile = open("TotalDocuments.txt",'r')
		line = ifile.readline().strip('\n')
		self.vocabularySize = int(line.strip())


	def provideFieldTokens(self,inputQuery):
		words = re.split(r'^t:|b:|c:|i:|r:|e:',inputQuery)
		fieldDict={}
		for eachWord in words:
			eachWord=eachWord.strip()
			if(len(eachWord)<=1):
				continue
			currIdx=inputQuery.index(eachWord)
			QType=inputQuery[currIdx-2]
			QWords=eachWord
			if QType is not None:
				fieldDict[QType]=QWords
		return fieldDict
			

	def buildSearchTokens(self,searchQueryInput):

		if ":" in searchQueryInput:
			self.isfieldQuery=1

		if self.isfieldQuery == 0 :
			#search is normal
			self.searchTokens+=tokenizeText(searchQueryInput)
			if len(self.searchTokens) == 1 :
				self.singleTermQuery = 1

		else :
			self.fieldInputDict=self.provideFieldTokens(searchQueryInput)


	def findFileNameFromSecIndex(self,termToSearch):
		# SecFile=open(SecIndexFile,"r")
		# termList=[]
		# line=SecFile.readline().strip('\n')
		# while(line):
		# 	termList.append(line.strip())
		# 	line=SecFile.readline().strip('\n')

		# SecFile.close()
		fileIndex=getLoc(self.secondaryIndexTermList,termToSearch)
		return ("index"+str(fileIndex+1)+".txt")

	def getPostingList(self,term,SourceIndexFile):
		Plist = None
		IFile = open(SourceIndexFile,'r')
		line = IFile.readline().strip('\n')
		while (line) :
			currentTerm = line.split(':')[0]
			currentPostingList = line.split(':')[1]
			if currentTerm == term:
				Plist = currentPostingList
				break
			line = IFile.readline().strip('\n')

		IFile.close()
		return Plist

	def getTermPostingList(self,term):
		term=term.lower()
		term=term.strip()
		fileToSearch = self.findFileNameFromSecIndex(term)
		Plist = self.getPostingList(term,fileDirectories[0]+fileToSearch)
		return Plist


	def findTitleFileNameFromTitleIndex(self,docId):
		# tIndex = open("TitleIndex.txt",'r')
		# lowerRange = []
		# line = tIndex.readline().strip('\n')
		# while(line):
		# 	lowerRange.append(int(line.split(' ')[0].strip()))
		# 	line = tIndex.readline().strip('\n')
		# tIndex.close()
		fileNumber = getLoc(self.secondaryTitleIdList,docId)
		return ("titles"+str(fileNumber+1)+".txt"),self.secondaryTitleIdList[fileNumber]

	def getTitleOfDocumentId(self,docId):
		fileName,countStart = self.findTitleFileNameFromTitleIndex(docId)
		iFile = open(fileDirectories[1]+fileName,'r')
		line = iFile.readline().strip('\n')
		titleResult = None
		while(line):
			if countStart == docId:
				titleResult=line
				break
			countStart+=1
			line = iFile.readline().strip('\n')
		iFile.close()
		return titleResult

	def getDocIdPostingListDictFromTermPostingList(self,Plist):
		docIds = re.findall(r'd[0-9]+',Plist)
		docIdPlist = re.split(r'd[0-9]+',Plist)[1:]
		docIdPListDict={}
		for i in range(len(docIds)):
			docIdPListDict[docIds[i]] = docIdPlist[i]
		return docIdPListDict

	def countPart(self,postingList, fieldType):
		if fieldType not in postingList:
			return 0
		part = postingList.split(fieldType)[1]
		cnt = re.split(r'[^0-9]+', part)[0]
		return int(cnt)


	def getTermFreqCountFromDocumentPostingList(self,postingList):
		fcount = 0
		if self.handlingFieldQuery == 0:
			fcount = self.countPart(postingList,'t') + self.countPart(postingList,'b')
		else:
			fcount=self.countPart(postingList,self.currentFieldType)
		return fcount

	def getDocIdTermFrequency(self,termPostingList):
		docIdPosListDict = self.getDocIdPostingListDictFromTermPostingList(termPostingList)
		for eachDocId in docIdPosListDict:
			cvalue = self.getTermFreqCountFromDocumentPostingList(docIdPosListDict[eachDocId])
			docIdPosListDict[eachDocId]=cvalue
		return docIdPosListDict


	def getIDFValueForTerm(self,documentFrequency):
		score = log(self.vocabularySize/documentFrequency)
		return score


	def getSubLinearTFValue(self,termFrequency):
		result = 0
		if termFrequency > 0 :
			result = 1 + log(termFrequency)
		return result

	def getTermDocumentScore(self,tf,idf):
		return (tf * idf)


	def intersection(self,lst1, lst2): 
		return list(set(lst1).intersection(lst2))

	def setunion(self,lst1, lst2): 
		return list(set(lst1).union(lst2))


	def findUnionDocumentIds(self,termDocIdDict):
		finalans = None
		for key in termDocIdDict.keys():
			finalans=termDocIdDict[key]
			break
		for eachterm in termDocIdDict.keys():
			finalans=self.setunion(finalans,termDocIdDict[eachterm])
		return finalans    


	def findInterSectingDocumentIds(self,termDocIdDict):
		finalans = None
		for key in termDocIdDict.keys():
			finalans=termDocIdDict[key]
			break
		for eachterm in termDocIdDict.keys():
			finalans=self.intersection(finalans,termDocIdDict[eachterm])
		return finalans    



	def prepareForTFIDF(self):
		if self.isfieldQuery == 0:
			for eachToken in self.searchTokens:
				#Get the posting list of that term
				currentPostingList = self.getTermPostingList(eachToken)
				if currentPostingList:					
					self.termDocIdDict[eachToken] = re.findall(r'd[0-9]+',currentPostingList) #list of all doc id for that term
					self.termDocIdFreqDict[eachToken] = self.getDocIdTermFrequency(currentPostingList)
					documentFreq = len(self.termDocIdDict[eachToken]) #Number of documents for that token
					self.termIDFDict[eachToken] = self.getIDFValueForTerm(documentFreq)

			self.intersectionDocIdList = self.findInterSectingDocumentIds(self.termDocIdDict)
			if len(self.intersectionDocIdList) < self.topK:
				self.intersectionDocIdList = self.findUnionDocumentIds(self.termDocIdDict)


	def buildDocumentTFIDFScores(self):
		if len(self.intersectionDocIdList) > 0:
			# self.initialzeTermDocIdScoreDict(self.intersectionDocIdList)
			totalScore = 0 #Document total tf-idf score over all query terms
			for eachDocId in self.intersectionDocIdList:
				totalScore = 0
				for eachTerm in self.termDocIdFreqDict.keys():
					if eachDocId in self.termDocIdFreqDict[eachTerm].keys():
						termFreq = self.termDocIdFreqDict[eachTerm][eachDocId]
						tfidfval = self.getSubLinearTFValue(termFreq) * self.termIDFDict[eachTerm]
						# self.termDocIdScoreDict[eachTerm][eachDocId] = tfidfval
						totalScore+=tfidfval

				self.documentScoreDict[eachDocId] = totalScore

	def sortDocumentsByTopScores(self,docScoreDict):
		temp = dict(sorted(docScoreDict.items(), key=operator.itemgetter(1),reverse=True))
		return list(temp.keys())


	def returnTopKDocIdResult(self):
		sortedDocScoreList = self.sortDocumentsByTopScores(self.documentScoreDict)
		if len(sortedDocScoreList) <= self.topK:
			return sortedDocScoreList
		else:
			return sortedDocScoreList[:self.topK]


	def getDocumentTitles(self,docIdList):
		titleList = []
		for eachDocId in docIdList:
			titleList.append(self.getTitleOfDocumentId(int(eachDocId.strip('d'))))
		return titleList

	def getIntersectingDocIdFromMultipleFields(self,totalList):
	    if len(totalList) <= 0:
	        return
	    currentInter = totalList[0]
	    for i in range(1,len(totalList)):
	        currentInter=self.intersection(currentInter,totalList[i])
	    return currentInter

	def getUnionDocIdFromMultipleFields(self,totalList):
	    if len(totalList) <= 0:
	        return
	    currentInter = totalList[0]
	    for i in range(1,len(totalList)):
	        currentInter=self.setunion(currentInter,totalList[i])
	    return currentInter

	def clearInMemoryDataStructures(self):
		self.termPostingListDict={}
		self.termDocIdDict = {}
		self.termIDFDict = {}
		self.termDocIdFreqDict={}
		self.termDocIdScoreDict = {}
		self.intersectionDocIdList = None
		self.documentScoreDict = {}




	def handleFieldSearch(self):
		totalScoredDocIds=[]
		totalScoredTopKDocIds = None

		self.isfieldQuery = 0
		self.handlingFieldQuery=1

		for eachFieldType in self.fieldInputDict.keys():

			self.clearInMemoryDataStructures()
			self.currentFieldType = eachFieldType
			self.buildSearchTokens(self.fieldInputDict[eachFieldType])
			self.prepareForTFIDF()
			self.buildDocumentTFIDFScores()
			docIdListResult = self.returnTopKDocIdResult()
			totalScoredDocIds.append(docIdListResult)


		totalScoredTopKDocIds = self.getIntersectingDocIdFromMultipleFields(totalScoredDocIds)
		if len(totalScoredTopKDocIds) < self.topK:
			totalScoredTopKDocIds=self.getUnionDocIdFromMultipleFields(totalScoredDocIds)

		totalScoredTopKDocIds=totalScoredTopKDocIds[:self.topK]
		totalScoredTopKDocTitles=self.getDocumentTitles(totalScoredTopKDocIds)

		return totalScoredTopKDocIds,totalScoredTopKDocTitles
#Class ends here
def getLoc(numbers,key):
	total=len(numbers)
	start = 0
	end = total - 1
	mid =  (start + end) // 2 
	loc = None
	while (start < end ):
		if numbers[mid] > key:
			end = mid - 1

		elif numbers[mid] < key:
			start = mid+1

		elif mid + 1 <= (total - 1) and ( numbers[mid]<= key and numbers[mid+1] > key):
			loc = mid
			break

		else:
			loc = mid
			break

		mid = (start + end) // 2
	if numbers[mid] == key:
		return mid
	if numbers[mid] < key:
		return mid 
	return mid -1


stemObj=Stemmer('porter')
from nltk.tokenize import RegexpTokenizer
tokenizer = RegexpTokenizer("\w+|\$[\d\.]+|\S+")
# tokenize text
def tokenizeText(textInput):
	normalized=[]
	#textInput=removeURL(textInput)
	#tokens = re.findall(r"\w+(?:'\w+)?|[^\w\s]", textInput)
	tokens=re.split(r'[^A-Za-z0-9]+',textInput)
	#tokens = [x for x in tokens if re.match(r"^[a-z]+$", x.lower())]
	for token in tokens:
		token=token.lower()
		token=token.lstrip('0')
		word=stemObj.stemWord(token)
		if word in STOP_WORDS or len(word)<=1:
			continue
		normalized.append(word)

	return normalized

def writeDocIdTitlesToFile(fileptr,documentIdList,documentTitleList):
	for i in range(0,len(documentIdList)):
		fileptr.write(str(documentIdList[i].strip('d'))+", "+str(documentTitleList[i])+"\n")




def readFullTermSecondaryIndex(fileSrc):
	SecFile=open(fileSrc,"r")
	termList=[]
	line=SecFile.readline().strip('\n')
	while(line):
		termList.append(line.strip())
		line=SecFile.readline().strip('\n')
	return termList

def readFullTitleIdSecondaryIndex(fileSrc):
	tIndex = open(fileSrc,'r')
	lowerRange = []
	line = tIndex.readline().strip('\n')
	while(line):
		lowerRange.append(int(line.split(' ')[0].strip()))
		line = tIndex.readline().strip('\n')
	tIndex.close()
	return lowerRange




QueriesSourceFile = sys.argv[1]
inputQueryFile = open(QueriesSourceFile,'r')
queryOutputFile = open("queries_op.txt",'w')
secondaryIndexTerms = None
secondaryTitleIds = None
secondaryIndexTerms = readFullTermSecondaryIndex(fileDirectories[0]+"secIndex.txt")
secondaryTitleIds = readFullTitleIdSecondaryIndex("TitleIndex.txt")
line = inputQueryFile.readline().strip('\n')
totalTime = 0
totalQueries = 0

while(line):

	topKVal = int(line.split(',')[0].strip())
	currentSearchQuery = line.split(',')[1].strip()
	totalQueries+=1
	line = inputQueryFile.readline().strip('\n')
	startTime = time.time()
	searchObj = WikiSearch()
	searchObj.topK = topKVal
	searchObj.secondaryIndexTermList = secondaryIndexTerms
	searchObj.secondaryTitleIdList = secondaryTitleIds
	searchObj.buildSearchTokens(currentSearchQuery)

	if searchObj.isfieldQuery == 0:
		searchObj.prepareForTFIDF()
		searchObj.buildDocumentTFIDFScores()
		docIdListResult = searchObj.returnTopKDocIdResult()
		docIdTitleResult = searchObj.getDocumentTitles(docIdListResult)
		totalTime+=time.time() - startTime
		writeDocIdTitlesToFile(queryOutputFile,docIdListResult,docIdTitleResult)

	else:
		docIdListResult,docIdTitleResult=searchObj.handleFieldSearch()
		totalTime+=time.time() - startTime
		writeDocIdTitlesToFile(queryOutputFile,docIdListResult,docIdTitleResult)

	del searchObj

inputQueryFile.close()
queryOutputFile.write(str(totalTime)+","+str(totalTime/totalQueries)+"\n")
queryOutputFile.close()