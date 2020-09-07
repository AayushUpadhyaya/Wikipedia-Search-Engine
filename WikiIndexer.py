import sys
import bisect
import time
import re
from collections import defaultdict
import math
import os
import xml.sax
from spacy.lang.en.stop_words import STOP_WORDS
from Stemmer import Stemmer

startTime = time.time()
articleThreshold = 10000
termThreshold = 10000
fileDirectories = ['./InvertedIndex','./DocumentTitles']
oldTitleStart=1
endTitle=0


class WikiXMLHandler(xml.sax.ContentHandler):
	totalDocuments=0;totalIndexFiles=0;
	totalIndexTokens = 0 ; totalDocumentTokens = 0;
	def __init__(self):
		xml.sax.handler.ContentHandler.__init__(self)
		self.fileCount=1
		self.pageCount=0
		self.wordDict={}
		self.titles=[]
		self.buffer=''


	def characters(self,content):
		self.buffer+=content


	def startElement(self,tag,attributes):
		self.buffer=''


	def endElement(self,tag):
		if tag == 'title':
			self.title=self.buffer
			self.buffer=''
		elif tag == 'text':
			self.text=self.buffer
			self.buffer=''
		elif tag == 'mediawiki':
			#self.pageCount+=1
			dumpPostingListToDisk(self.fileCount,self.wordDict)
			writeTitles(self.titles,self.fileCount,self.pageCount)
			WikiXMLHandler.totalDocuments=self.pageCount
			self.buffer=''
			self.wordDict={}
			self.Titles=[]
			WikiXMLHandler.totalIndexFiles=self.fileCount
			self.fileCount+=1
			print('Parsing Complete')

		elif tag == 'page':
			self.pageCount+=1
			WikiXMLHandler.totalDocuments=self.pageCount
			(self.titles).append(self.title)
			constructPostingList(self.title,self.pageCount,self.wordDict,self.text)			
			

			if len(self.wordDict.keys()) % articleThreshold == 0:
				WikiXMLHandler.totalDocumentTokens+=len(self.wordDict.keys())
				dumpPostingListToDisk(self.fileCount,self.wordDict)
				writeTitles(self.titles,self.fileCount,self.pageCount)
				self.wordDict={}
				self.titles=[]
				self.buffer=''
				WikiXMLHandler.totalIndexFiles+=1
				self.fileCount+=1			
			
			
def removeURL(inputText):
	returnText=re.sub(r'http\S+','',inputText)
	returnText=re.sub(r'url=','',returnText)
	return returnText


def removeNewLine(textInput):
	textInput = textInput.replace('\'', '')
	textInput = textInput.strip()
	return textInput.replace('\n', ' ')



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
		WikiXMLHandler.totalDocumentTokens+=1
		normalized.append(word)

	return normalized

#find category tokens
def getCategory(textInput):
	#Look for all Category tags that start with [[Category
	catTokens=re.findall(r"\[\[Category:(.*)\]\]",textInput)
	#We also need to tokenize all categories Tokens
	catList=[] # Refers to the list of category tokens
	for token in catTokens:
		token=tokenizeText(token)
		catList+=token
	return catList



# find infobox tokens
def getInfoboxText(textInput):
	infoTex = textInput.split("{{Infobox")
	infoboxText = []
	if len(infoTex) <= 1:
		return []
	braceCount=1
	for index in range(1,len(infoTex)):
		filterd = infoTex[index].split("\n")
		for lines in filterd:
			if "{{" in lines:
				braceCount+=1
			if "}}" in lines:
				braceCount-=1
			if lines == "}}" and braceCount == 0:
				break
			if "[[Category" in lines:
				continue
			infoboxText += tokenizeText(lines)
	return infoboxText
# To perform some cleaning on the raw data
def cleanText(inputText):
	re1 = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',re.DOTALL)
	re2 = re.compile(r'{\|(.*?)\|}',re.DOTALL)
	re3 = re.compile(r'{{v?cite(.*?)}}',re.DOTALL)
	re4 = re.compile(r'<(.*?)>',re.DOTALL)
	inputText = inputText.lower()
	inputText = re1.sub(' ', inputText)
	inputText = re2.sub(' ', inputText)
	inputText = re3.sub(' ', inputText)
	inputText = re4.sub(' ', inputText)
	inputText = removeNewLine(inputText)
	return inputText

def replaceSquareBrackets(text):
	text = text.replace('[', ' ')
	text = text.replace(']', ' ')
	return text

def getReferences(inputText):
	inputText=removeURL(inputText)
	splitTokens=inputText.split("==References==")
	if(len(splitTokens)<=1):
		return []
	newLinesTokens=splitTokens[1].split("\n")
	resultList=[]
	for eachLine in newLinesTokens:
		if ("[[Category" in eachLine) or ("==" in eachLine):
			break
		eachLine=tokenizeText(eachLine)
		if(len(eachLine)>0):
			if("Reflist" in eachLine):
				eachLine.remove("Reflist")
			resultList+=eachLine
	return resultList


def getExternalLinks(inputText):
	inputText=removeURL(inputText)
	splitTokens=inputText.split("==External links==")
	if(len(splitTokens)<=1):
		return []
	returnList=[]
	newLinks=splitTokens[1].split("\n")
	for token in newLinks:
		token=token.strip()
		if  token and token[0] == '*':
			token1=tokenizeText(token)
			returnList+=token1
	return returnList


import shutil
def setupDirectories(dirList):
	for eachDir in dirList:
		if(os.path.isdir(eachDir)):
			try:
				shutil.rmtree(eachDir)
			except OSError as e:
				print("Error: %s : %s" % (dir_path, e.strerror))
		os.mkdir(eachDir)


def writeTitles(titles,fileCount,pageCount):
	titleFile=open(fileDirectories[1]+"/titles"+str(fileCount)+".txt","w")
	global endTitle
	global oldTitleStart
	endTitle=pageCount
	Tcount=0
	for eachTitle in titles:
		Tcount+=1
		titleFile.write(eachTitle+"\n")
	titleFile.close()
	if Tcount:
		titleSecIndex.write(str(oldTitleStart)+" "+str(endTitle)+"\n")
	oldTitleStart=pageCount+1


def dumpPostingListToDisk(fileCount,wordDict):
	catType=['t','b','i','c','e','r']
	postingFile=open(fileDirectories[0]+"index"+str(fileCount)+".txt","w")
	for term in sorted(wordDict.keys()):
		WikiXMLHandler.totalIndexTokens+=1
		postingDict=wordDict[term]
		postingFile.write(term+":")
		for docId in sorted(postingDict.keys()):
			postingFile.write("d"+str(docId))
			for index,frequency in enumerate(postingDict[docId]):
				if(frequency):
					postingFile.write(catType[index]+str(frequency))
		postingFile.write("\n")
	postingFile.close()


def buildPosting(docId,inputTokens,wordDict,fieldTypeIndex):
	for eachToken in inputTokens:
		catFreq=[0,0,0,0,0,0] #'''[Title,Body,Infobox,Categories,ExternalLinks,References]'''
		if eachToken in wordDict:

			if docId in wordDict[eachToken]:
				oldFreqList=wordDict[eachToken][docId]
				oldFreqList[fieldTypeIndex]+=1
				wordDict[eachToken][docId]=oldFreqList

			else:
				catFreq[fieldTypeIndex]+=1
				wordDict[eachToken][docId]=catFreq

		else:
			wordDict[eachToken]={}
			catFreq[fieldTypeIndex]+=1
			wordDict[eachToken][docId]=catFreq





	

def constructPostingList(title,docId,wordDict,text):
	titleTokens=tokenizeText(title)
	bodyTokens=tokenizeText(text)
	infoboxTokens=getInfoboxText(text)
	categoriesTokens=getCategory(text)
	externalLinkTokens=getExternalLinks(text)
	referencesTokens=getReferences(text)
	tokensType=[titleTokens,bodyTokens,infoboxTokens,categoriesTokens,externalLinkTokens,referencesTokens]

	for index in range(len(tokensType)):
		buildPosting(docId,tokensType[index],wordDict,index)



def mergeFiles(fileSource1,fileSource2,mergerName,indexFileDir):
	if fileSource1 == fileSource2 :
		return

	indexFile1=open(fileSource1,'r')
	indexFile2=open(fileSource2,'r')
	temporaryFile=open(indexFileDir+"/temp.txt",'w')
	file1Line=indexFile1.readline().strip('\n')
	file2Line=indexFile2.readline().strip('\n')
	while(file1Line and file2Line):
		term1=file1Line.split(":")[0]
		term2=file2Line.split(":")[0]

		if term1 < term2 :
			temporaryFile.write(file1Line+"\n")
			file1Line=indexFile1.readline().strip('\n')

		elif term2 < term1 :
			temporaryFile.write(file2Line+"\n")
			file2Line=indexFile2.readline().strip('\n')

		else :
			combinedPostingList=file1Line.strip().split(":")[1]+file2Line.strip().split(":")[1]
			temporaryFile.write(term1+":"+combinedPostingList+"\n")
			file1Line=indexFile1.readline().strip('\n')
			file2Line=indexFile2.readline().strip('\n')

	while(file1Line):
		temporaryFile.write(file1Line.strip()+"\n")
		file1Line=indexFile1.readline().strip('\n')

	while(file2Line):
		temporaryFile.write(file2Line.strip()+"\n")
		file2Line=indexFile2.readline().strip('\n')
	indexFile1.close()
	indexFile2.close()
	temporaryFile.close()
	os.remove(fileSource1)
	os.remove(fileSource2)
	os.rename(indexFileDir+"/temp.txt",indexFileDir+"/"+mergerName)



def mergeIndexFiles(indexFileDir,totalFiles):
	#Check if index file directory exists
	if os.path.isdir(indexFileDir):
		#Atleast 2 index files must be present
		indexFileList=sorted(os.listdir(indexFileDir))
		while len(indexFileList) >=2 :
			for i in range(0,len(indexFileList),2):
				if ( i + 1 ) >= len(indexFileList):
					break
				mergeFiles(indexFileDir+"/"+indexFileList[i],indexFileDir+"/"+indexFileList[i+1],indexFileList[i],indexFileDir)
			indexFileList=sorted(os.listdir(indexFileDir))

		os.rename(indexFileDir+"/"+os.listdir(indexFileDir)[0],indexFileDir+"/FullInvertedIndex.txt")



def splitSingleLargeIndexFile(indexFileSrc,indexFileDir,secondaryIndexFile):
	totalLines=0;totalActiveLines=0
	counter=1
	inputFileSource=open(indexFileSrc,'r')
	secIndex=open(indexFileDir+"/"+secondaryIndexFile,"w")
	inputLines=[]
	currentLine=inputFileSource.readline().strip('\n')
	while ( len(currentLine.strip()) > 0 ):
		inputLines.append(currentLine)
		totalLines+=1
		totalActiveLines+=1

		if(totalLines % termThreshold == 0):
			secIndex.write(inputLines[0].split(":")[0].strip()+"\n")
			outputFile=open(indexFileDir+"/index"+str(counter)+".txt",'w')
			for eachLine in inputLines:
				outputFile.write(eachLine+"\n")
			outputFile.close()
			inputLines=[]
			counter+=1
		currentLine=inputFileSource.readline().strip('\n')

	if(len(inputLines) > 0):
		outputFile=open(indexFileDir+"/index"+str(counter)+".txt",'w')
		secIndex.write(inputLines[0].split(":")[0].strip()+"\n")
		for eachLine in inputLines:
			outputFile.write(eachLine+"\n")
		outputFile.close()
		
	inputFileSource.close()
	secIndex.close()
	return totalLines




def writeIndexStatisticsFile(Wikiobj,StatFile):
	file1=open(StatFile,"w")
	file1.write(str(Wikiobj.totalDocumentTokens)+"\n")
	file1.write(str(Wikiobj.totalIndexTokens)+"\n")
	file1.close()

def writeTotalDocCount(Wikiobj,FileDest):
	file1=open(FileDest,"w")
	file1.write(str(Wikiobj.pageCount)+"\n")
	file1.close()



# Program starts here
# Take Index location from the argument 2
titleSecIndex = open("./TitleIndex.txt","w")
fileDirectories[0]=sys.argv[2]
setupDirectories(fileDirectories)
inputSourceFile=sys.argv[1] #inputSourceDirectory
parser = xml.sax.make_parser()
parser.setFeature(xml.sax.handler.feature_namespaces, 0)
wikiXMLhandlerObj = WikiXMLHandler()
parser.setContentHandler( wikiXMLhandlerObj )
c = 0
for eachFile in os.listdir(inputSourceFile):
	c+=1
	print("InputFile: ",eachFile)
	parser.parse(inputSourceFile+eachFile)
	# if c >=3:
	# 	break
print("Finished with "+str(c)+" files")
writeIndexStatisticsFile(wikiXMLhandlerObj,sys.argv[3])
print('Merging and Splitting Index...')
mergeIndexFiles(fileDirectories[0],wikiXMLhandlerObj.totalIndexFiles)
splitSingleLargeIndexFile(fileDirectories[0]+"/FullInvertedIndex.txt",fileDirectories[0],"secIndex.txt")
os.remove(fileDirectories[0]+"/FullInvertedIndex.txt")
writeTotalDocCount(wikiXMLhandlerObj,"TotalDocuments.txt")
titleSecIndex.close()
print('Total time(in s): %s',(time.time()-startTime))



	



