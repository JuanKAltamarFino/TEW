from Utility import readDFObjectForTesting,debugging,readObjectForTesting
from GenerateMatches import generateMatchesForShows
from TEW_MDB import generateTagTeamsFirstTime
import re
def main():
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