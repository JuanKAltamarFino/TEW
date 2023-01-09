from Utility import readDFObjectForTesting,debugging,readObjectForTesting
from GenerateMatches import generateMatchesForShows,generateWrestlerToFight
from TEW_MDB import generateTagTeamsFirstTime,mergeTeams,removeDuplicatesTagTeams
import re
def main():
	#testMergeTeams()
	testGenerateMatchesForShows()
	
def testRemoveDuplicatesTagTeams():
	db_teamsP=readDFObjectForTesting("db_teamsP")
	db_teamsP_=removeDuplicatesTagTeams(db_teamsP)
	print(db_teamsP.shape)
	print(db_teamsP_.shape)
def testGenerateWrestlerToFight():
	db_wrestlers=readDFObjectForTesting("db_wrestlers")
	str_type_match=readObjectForTesting("str_type_match")
	df_rosterDivition=readDFObjectForTesting("df_rosterDivition")
	is_shuffle=readObjectForTesting("is_shuffle")
	dict_matches=readObjectForTesting("dict_matches")
	generateWrestlerToFight(db_wrestlers,str_type_match,df_rosterDivition,is_shuffle,dict_matches)
def testMergeTeams():
	db_teamsP=readDFObjectForTesting("db_teamsP")
	print(db_teamsP.shape)
	db_teamsAEW=readDFObjectForTesting("db_teamsAEW")
	print(db_teamsAEW.shape)
	print(db_teamsP.shape==db_teamsAEW.shape)
	db_teamsP=mergeTeams(db_teamsP,db_teamsAEW)
	print(db_teamsP.shape)
def testGenerateTagTeamsFirstTime():
	dict_wrestling=readObjectForTesting("dict_wrestling")
	print(dict_wrestling)
	db_wrestlersP=readDFObjectForTesting("db_wrestlersP")
	generateTagTeamsFirstTime(dict_wrestling,db_wrestlersP)
	print(dict_wrestling)
def testGenerateMatchesForShows():
	#Generate Matches for shows
	#1- Get list of shows list_shows_preparar
	list_shows_preparar=readObjectForTesting("list_shows_preparar")
	#2- Get Participants for matches shows
	df_participantsForMatchesShows=readDFObjectForTesting("df_participantsForMatchesShows")
	#3- Get the Roster
	db_wrestlers=readObjectForTesting("db_wrestlers")
	#4- Get df_roster_divition
	df_roster_divition=readDFObjectForTesting("df_roster_divition")
	is_shuffle=True
	dict_matches=readObjectForTesting("dict_matches")
	dict_matches=generateMatchesForShows(list_shows_preparar,df_participantsForMatchesShows,db_wrestlers,df_roster_divition,is_shuffle,dict_matches)
	df_participantsForMatchesShows.filter(regex=("W\d|WrestlerName"))
	print(dict_matches)
	print(df_roster_divition)
if __name__ == '__main__':
    main()
	#["Tag Name", 'W1', 'W2', 'EXP', 'Popularity', 'Type', 'Active', 'Gender','Brand', 'WUID1', 'WUID2','UID_TEAM', 'BestRating']