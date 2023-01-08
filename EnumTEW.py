from enum import Enum
 
class MatchesColumns(Enum):
    SHOW_NAME = 'Show'
    TYPE_MATCH = 'TypeOfMatch'
    SUGGESTED_NAME = 'SuggestedName'
    EXPECTED_MINUTES = 'ExpectedMinutes'
    LST_WORKERS_COLUMNS=('W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7', 'W8', 'W9', 'W10')
    DEFEATED='Defeat'
    BEST='Best'
    SUGGESTED_WINNER = 'SuggestedWinner'
    MATCH_AIMS = 'MatchAims'
    EXPECTED_RATING='ExpectedRaiting'
    REAL_RATING='RealRating'
    DIFF_RATING='DiffRating'
class AnglesColumns(Enum):
    SHOW_NAME = 'Show'
    TYPE_ANGLE = 'TypeAngle' #(Freestyle Angle, PENDING)
    SUGGESTED_NAME = 'SuggestedName'
    EXPECTED_MINUTES = 'ExpectedMinutes'
    LST_WORKERS_COLUMNS=('W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7', 'W8')
    LST_SCRIPT_COLUMNS=('S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8')
    LST_RATE_ON_COLUMNS=('RO1', 'RO2', 'RO3', 'RO4', 'RO5', 'RO6', 'RO7', 'RO8')
    LST_STORY_LINE_COLUMNS=('SL1', 'SL2', 'SL3', 'SL4', 'SL5', 'SL6', 'SL7', 'SL8')
    LST_APPEARANCE_COLUMNS=('AP1', 'AP2', 'AP3', 'AP4', 'AP5', 'AP6', 'AP7', 'AP8')
    
class StableColumnsTable(Enum):
    NAME='Name'
    COMPANY_UID='CompanyUID'
    COMPANY_NAME='CompanyName'
    ACTIVE='Active'
    LST_MEMBERS=('Member1','Member2','Member3','Member4','Member5','Member6','Member7','Member8','Member9','Member10','Member11','Member12','Member13','Member14','Member15','Member16','Member17','Member18')

class TriosColumns(Enum):
	NAME='Name'
	LST_MEMBERS=('W1','W2','W3')
	BEST_RAITING='BestRaiting'
	GENDER='Gender'
	BRAND='Brand'
	ACTIVE='Active'
    
class MatchHistoryColumns(Enum):
    COMPANY_INITIALS='CompanyInitiasl'
    MATCH_TYPE='MatchType'
    RATING='Rating'
    WHICH_SIDE_WON='Which_Side_Won'
    EXTRA_NOTES='Extra_Notes'
    WORKER_UID='WorkerUID'
    WHICH_SIDE='Which_Side'
	
class RosterTypes(Enum):
	SINGLE="Single"
	TAG_TEAM="Tag"
	TRIOS="Trios"
            