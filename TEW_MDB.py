import csv, pyodbc
import pandas as pd
import numpy as np
from pathlib import Path
from pywinauto.application import Application
import pywinauto
import psutil
import cv2
import pyautogui
import pytesseract
from EnumTEW import StableColumnsTable
from EnumTEW import MatchHistoryColumns
from EnumTEW import TriosColumns
from EnumTEW import RosterTypes
from itertools import combinations
from Utility import debugging,getLen,writeExcel,saveDFObjectForTesting,saveObjectForTesting
from SetUp import readRouteFolderIfExist
pytesseract.pytesseract.tesseract_cmd = r"J:\Program Files\Tesseract-OCR\tesseract.exe"        
c_key_whereMyWrestlersWorks='WhereWorkMyWrestlers'
def main():
	v_companyInitials=getCompanyInitials()
	con=getConnection()
	cur = getCursor(con)
	v_table_name=list([])
	#for table_info in cur.tables(tableType='TABLE'):
	#    table=table_info.table_name
	#    v_table_name.append(table)
	#    #print(table_info.column_name)
	#for table in v_table_name:
	#    print(table)
	#    for row in cur.columns(table=table):
	#        #print(f'\t{row.column_name}')
	# run a query and get the results
	db_wrestlersP=getSingleWrestlers(cur)
	Face='Face'
	Heel='Heel'
	valor='0'
	SQL = f'select CLng(ps.Held_Year & IIf(getLen(ps.Held_Month)<2, 0&ps.Held_Month, ps.Held_Month) & ps.Held_Week),ps.* from Companies c,Previous_Shows ps WHERE c.Initials = ? and ps.CompanyUID=c.UID  order by CLng(ps.Held_Year & IIf(getLen(ps.Held_Month)<2, 0&ps.Held_Month, ps.Held_Month) & ps.Held_Week);' # your query goes here  
	#rows = cur.execute(SQLMatchHistories,'AEW','None').fetchall()
	db_inactive=inactive_wrestlers(cur)
	db_teamsAEW=generateDbTeamsAEW(cur)
	dict_staff=generateStaffAWE(cur)
	df_stables=getActiveStablesInCompany(cur)
	#Generate a MatchResume by Single, Tag and Trio matches
	df_matchHistory=getMatchHistory(cur)
	dict_matchResume=generateMatchResume(cur)
	dict_champions=generateActualChampions(cur)
	dict_childcompany_wrestlers={}
	dict_childcompany_wrestlers.update(generateChildCompanyWrestlers(cur))
	dict_childcompany_wrestlers.update(generateChildCompanyWrestlersToFollow(cur))        
	dict_childcompanies=generateChildCompanies(cur)
	dict_childcompany_wrestlers.update(getWhereWorkMyWrestlers(cur))    	
	cur.close()
	con.close()
	#Begin of the program to ban wrestler for shows
	df_whereMyWrestlersWorks=dict_childcompany_wrestlers.get(c_key_whereMyWrestlersWorks)
	df_whereMyWrestlersWorks2=readWhereWorkMyWrestlersFromChildCompanyWrestlers()
	#Here we can generate a program based in the whereMyWrestlersWork to find their priority
	app=getApplicationTEW2020()
	#First drop the rows with the AEW (Initials of our compay-Must be a parameter)
	df_whereMyWrestlersWorks = df_whereMyWrestlersWorks.reset_index(drop=True)
	df_whereMyWrestlersWorks2 = df_whereMyWrestlersWorks2.reset_index(drop=True)
	if df_whereMyWrestlersWorks.shape==df_whereMyWrestlersWorks2.shape:
		differences=df_whereMyWrestlersWorks.compare(df_whereMyWrestlersWorks2)
	else:
		differences=df_whereMyWrestlersWorks
	if getLen(differences)>0 & (not (df_whereMyWrestlersWorks.equals(df_whereMyWrestlersWorks2))):
	#not (df_whereMyWrestlersWorks.equals(df_whereMyWrestlersWorks2)):
		df_worksForMy=df_whereMyWrestlersWorks.loc[df_whereMyWrestlersWorks['Company']==v_companyInitials]
		df_whereMyWrestlersWorks=df_whereMyWrestlersWorks.drop(index=df_worksForMy.index)
		df_priorityFound=getWrestlersWithMajorPriority(app,df_whereMyWrestlersWorks,v_companyInitials)
	else:
		df_priorityFound=readPriorityFoundFromChieldCompanyWrestlers()
	#8 put the DF in the Dict dict_childcompany_wrestlers with the key wrestlersWithOtherPriority
	dict_childcompany_wrestlers.update({'wrestlersWithOtherPriority':df_priorityFound})
	set_InitialsCompanies=df_priorityFound['Company'].unique()
	df_companyShows=generateDfCompanyShows(app,set_InitialsCompanies)
	u_total_div=pd.merge(df_priorityFound,df_companyShows,on=['Company'],  how='right')
	df_wrestlersCompromises=u_total_div.groupby(['WName','Company','DayOfWeek','Week','Month']).size().reset_index(name='count')
	print(f"JuanK is working...\n{df_wrestlersCompromises}")
	df_ourShows=getDfOurShows()
	df_wrestlersCantWrestle=generateDfWrestlersCantWrestle(df_wrestlersCompromises,df_ourShows)
	addOrReplaceParameter('WCantParticipate',df_wrestlersCantWrestle)
	db_wrestlersP=calculatePopularity(db_wrestlersP)
	db_wrestlersP=calculateInRingAction(db_wrestlersP)
	db_wrestlersP=calculateBestRating(db_wrestlersP)
	db_wrestlersP=calculateRateOn(db_wrestlersP)
	dict_wrestling=consult_dict_wrestling()
	db_wrestlersP.loc[(db_wrestlersP['Disposition']=='False'),'Disposition']='Heel'
	db_wrestlersP.loc[(db_wrestlersP['Disposition']=='True'),'Disposition']='Face'
	db_wrestlersP=inactivate_wrestlers(db_inactive,db_wrestlersP)
	db_wrestlersP=changeColumnsPosition(db_wrestlersP)
	saveObjectForTesting("dict_wrestling",dict_wrestling)
	saveDFObjectForTesting("db_wrestlersP",db_wrestlersP)
	generateTagTeamsFirstTime(dict_wrestling,db_wrestlersP)
	db_teamsP=dict_wrestling.get(RosterTypes.TAG_TEAM.value)
	saveDFObjectForTesting("db_teamsP",db_teamsP)
	saveDFObjectForTesting("db_teamsAEW",db_teamsAEW)
	db_teamsP=mergeTeams(db_teamsP,db_teamsAEW)
	#db_teamsP=put_experience(db_teamsP,db_teamsAEW)
	db_trios=generateTriosBasedOnStables(df_stables,db_wrestlersP)
	dict_wrestling.update({"Tag":db_teamsP})
	dict_wrestling.update({"Single":db_wrestlersP})
	dict_wrestling.update({"Trios":db_trios})
	writeWrestlingExcel(dict_wrestling)
	writeStaffExcel(dict_staff)
	writeMatchResumeExcel(dict_matchResume)
	writeChampionsExcel(dict_champions)
	writeChildCompanyWrestlersExcel(dict_childcompany_wrestlers)
	writeChildCompaniesExcel(dict_childcompanies)
def getCompanyInitials():
    dict_param=readParameters()
    df_general=dict_param.get('General')
    v_companyInitials=df_general['CompanyInitials'].head().item()
    if v_companyInitials:
        print(f'Loading v_companyInitials {v_companyInitials}')
    else:
        raise Exception(f'Fail to obtain the MDB file route\n{df_general}')
    return v_companyInitials
def getMDBActualRoute():
    dict_param=readParameters()
    df_general=dict_param.get('General')
    MDB=df_general['MDBFileRoute'].head().item()
    if MDB:
        print(f'Loading MDB route file {MDB}')
    else:
        raise Exception(f'Fail to obtain the MDB file route\n{df_general}')
    return MDB
def getConnection():
	MDB = getMDBActualRoute()
	DRV = '{Microsoft Access Driver (*.mdb, *.accdb)}'
	PWD = ''
	# connect to db
	con = pyodbc.connect(r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=E:\Program Files (x86)\GDS\TEW2020\Databases\AEW_2026\SaveGames\AEW\MDBFiles\AEW.mdb;')
	con = pyodbc.connect('DRIVER={};DBQ={};PWD={}'.format(DRV,MDB,PWD))
	return con
def getCursor(con):
	cur = con.cursor()
	return cur
def getSingleWrestlers(cursor):
	v_columns=generate_wrestlers_columns(cursor)
	db_wrestlersP=generate_dataframes(v_columns)
	r_wrestlers=consultSingleWrestlers(cursor,getCompanyInitials())
	for wrestler in r_wrestlers:
		if wrestler[10]==True:
			wrestler[10]='Male'
		else:
			wrestler[10]='Female'
		#print(f'{len(wrestler)},{wrestler}')
		#print(f'{len(v_columns)},\n{v_columns}')
		a_series = pd.Series(wrestler, index = v_columns)
		db_wrestlersP=db_wrestlersP.append(a_series, ignore_index=True)
	return db_wrestlersP
def consultSingleWrestlers(cursor, companyInitials):
	SQLWrestlers = f'SELECT ct.Perception,ct.Brand,ct.ExpectedShows,ct.Babyface,ct.Name,w.* FROM Companies c, Contracts ct, Workers w WHERE c.Initials = ? and ct.CompanyUID = c.UID and w.UID = ct.WorkerUID and ct.Wrestler=True;' # your query goes here  
	rows = cursor.execute(SQLWrestlers,companyInitials).fetchall()
	return rows
def readParameters():
    xlsx_file = getPathFileParameters()
    db_parameters=pd.read_excel(xlsx_file,None)
    return db_parameters
def getPathFileParameters():
	routeFolder=readRouteFolderIfExist()
	xlsx_file = Path(routeFolder, 'Param.xlsx')
	return xlsx_file
def generate_wrestlers_columns(cur):
    v_columns=list(['Perception','Brand','ExpectedShows','Disposition','WrestlerName'])
    for row in cur.columns(table='Workers'):
        #v_columns.append(row.column_name.replace("South_East", "Popularity"))
        v_columns.append(row.column_name.replace("Male","Gender"))
    #v_columns.append("RateOn")
    return v_columns
def calculatePopularity(db):
    v_columns=getLocationsNames()
    #db['Popularity']=db.loc[:, ['Great_Lakes','Mid_Atlantic']].mean(1)
    db[v_columns] = db[v_columns].apply(pd.to_numeric, errors='coerce', axis=1)
    db['Popularity'] =db[v_columns].mean(1) #db[v_columns].mean(1)
    return db
def getLocationsNames():
    listLocations=['Great_Lakes','Mid_Atlantic','Mid_South','Mid_West','New_England','North_West','South_East','South_West','Tri_State','Puerto_Rico','Hawaii','Maritimes','Quebec','Ontario','Alberta','Saskatchewan','Manitoba','British_Columbia','Noreste','Noroccidente','Sureste','Sur','Centro','Occidente','Midlands','Northern_England','Scotland','Southern_England','Ireland','Wales','Tohoku','Kanto','Chubu','Kinki','Chugoku','Shikoku','Kyushu','Hokkaido','Northern_Europe','Iberia','Southern_Med','Southern_Europe','Central_Europe','Scandinavia','Eastern_Europe','Russia','New_South_Wales','Queensland','South_Australia','Victoria','Western_Australia','Tasmania','New_Zealand','North_India','Central_India','South_India']
    return listLocations
def calculateInRingAction(df):
    v_columns=getInRingSkillNames()
    df[v_columns] = df[v_columns].apply(pd.to_numeric, errors='coerce', axis=1)
    df['InRingAction'] =df[v_columns].mean(1)
    return df
def getInRingSkillNames():
    listSkillNames=['Brawling','Aerial','Technical','Selling','Consistency','Puroresu','Flashiness','Hardcore','Safety']
    return listSkillNames
def calculateBestRating(df):
    df_temp=df.copy()
    df_temp['BestRatingOp1']=(df['InRingAction']*0.4+df['Popularity']*0.6)
    df_temp['BestRatingOp2']=(df['InRingAction']*0.7+df['Popularity']*0.3)
    df['BestRating'] =df_temp[['BestRatingOp1','BestRatingOp2']].max(axis=1)
    return df
def calculateRateOn(df):
    df_temp=df.copy()
    df_temp=calculateRateOnCharisma(df_temp)    
    df_temp=calculateRateOnMicrophone(df_temp)
    df_temp=calculateRateOnFighting(df_temp)
    df_temp=calculateRateOnEntertainment(df_temp)
    df_temp=calculateRateOnSelling(df_temp)
    df_temp=calculateRateOnStarQuality(df_temp)
    df_temp=calculateRateOnSexAppeal(df_temp)
    df_temp=calculateRateOnMenace(df_temp)
    df_temp=calculateRateOnOverness(df_temp)
    df_temp=calculateRateOnActing(df_temp)
    #ActionRateOn Entertainment, Microphone, Acting, Selling, or Fighting
    v_columns_passiveRateOn=['RateOnCharisma','RateOnStarQuality','RateOnSexAppeal','RateOnMenace','RateOnOverness']
    v_columns_activeRateOn=['RateOnMicrophone','RateOnFighting','RateOnEntertainment','RateOnSelling','RateOnActing']
    max_value=0
    df['RateOnPassive']=df_temp[v_columns_passiveRateOn].idxmax(axis=1)
    df['RateOnActive']=df_temp[v_columns_activeRateOn].idxmax(axis=1)
    return df
def calculateRateOnCharisma(df):
    #Calculate the RateOn for Charisma
    #40% Charisma 60% Popularity
    #Recieve an adjust by Sex Appeal, Acting and Star Quality
    v_columns=['Charisma','Popularity']
    df[v_columns] = df[v_columns].apply(pd.to_numeric, errors='coerce', axis=1)
    df['RateOnCharisma']=(df['Charisma']*0.4+df['Popularity']*0.6)
    return df
def calculateRateOnMicrophone(df):
    #Microphone
    #40% the talking rating and 60% their popularity
    #talking=80% of the Microphone skills and 20% of their Charisma
    #adjusted by comparing it to their Star Quality. How?
    v_columns=['Microphone','Charisma','Popularity']
    df[v_columns] = df[v_columns].apply(pd.to_numeric, errors='coerce', axis=1)
    df['Talking']=(df['Microphone']*0.8+df['Charisma']*0.2)
    df['RateOnMicrophone']=(df['Talking']*0.4+df['Popularity']*0.6)
    return df
def calculateRateOnFighting(df):
    # 40% their fighting rating and 60% their popularity
    #fighting is the highest rating they have for Brawling, Puroresu, or Hardcore.
    v_columns=['Brawling','Puroresu','Hardcore']
    df[v_columns] = df[v_columns].apply(pd.to_numeric, errors='coerce', axis=1)
    df['Fighting']=(df[v_columns].max(axis=1))
    df['RateOnFighting']=(df['Fighting']*0.4+df['Popularity']*0.6)
    return df
def calculateRateOnEntertainment(df):
    #40% entertainment rating and 60% their popularity
    #Microphone Skills and Charisma (the ration can be up to 70:30 in either direction; whatever makes the highest rating is chosen)
    #then further adjusted by comparing it to their Acting, Sex Appeal, and Star Quality.?
    v_columns=['Microphone','Charisma','Popularity']
    df[v_columns] = df[v_columns].apply(pd.to_numeric, errors='coerce', axis=1)
    for ratio in range(30,71):
        ratio_m=ratio
        ratio_c=100-ratio
        df['Entertainment'+str(ratio)]=(df['Microphone']*(ratio_m/100)+df['Charisma']*(ratio_c/100))
    v_entertainment_columns=[]
    for column_name in df.columns:
        if str(column_name).__contains__('Entertainment'):
            v_entertainment_columns.append(column_name)
    df['Entertainment']=(df[v_entertainment_columns].max(axis=1))
    df['RateOnEntertainment']=(df['Fighting']*0.4+df['Popularity']*0.6)
    return df
def calculateRateOnSelling(df):
    #25% their Selling skill and 75% their popularity.
    v_columns=['Selling','Popularity']
    df[v_columns] = df[v_columns].apply(pd.to_numeric, errors='coerce', axis=1)
    df['RateOnSelling']=(df['Selling']*0.25+df['Popularity']*0.75)
    return df
def calculateRateOnStarQuality(df):
    #30% their Star Quality and 70% their popularity
    #adjusted by comparing it to their Charisma; a higher Charisma can lift the rating slightly.
    v_columns=['Star_Quality','Popularity']
    df[v_columns] = df[v_columns].apply(pd.to_numeric, errors='coerce', axis=1)
    df['RateOnStarQuality']=(df['Star_Quality']*0.30+df['Popularity']*0.70)
    return df
def calculateRateOnSexAppeal(df):
    #30% their Sex Appeal and 70% their popularity
    #a higher Star Quality can lift the rating slightly.
    v_columns=['Looks','Popularity']
    df[v_columns] = df[v_columns].apply(pd.to_numeric, errors='coerce', axis=1)
    df['RateOnSexAppeal']=(df['Looks']*0.30+df['Popularity']*0.70)
    return df
def calculateRateOnMenace(df):
    #30% their Menace and 70% their popularity
    v_columns=['Menace','Popularity']
    df[v_columns] = df[v_columns].apply(pd.to_numeric, errors='coerce', axis=1)
    df['RateOnMenace']=(df['Menace']*0.30+df['Popularity']*0.70)
    return df
def calculateRateOnOverness(df):
    #her popularity - this effectively means that they're not doing anything at all.
    df['RateOnOverness']=(df['Popularity'])
    return df
def calculateRateOnActing(df):
    #25% their Acting skill and 75% their popularity.
    v_columns=['Acting','Popularity']
    df[v_columns] = df[v_columns].apply(pd.to_numeric, errors='coerce', axis=1)
    df['RateOnActing']=(df['Acting']*0.25+df['Popularity']*0.70)
    return df
def consult_dict_wrestling():
    dict_wrestling=read_file('Roster.xlsx') #Retorna un OrderedDict pero escribirlo en el excel se ve más complicado.
    return dict_wrestling
def read_file(file_name):
    xlsx_file = Path(readRouteFolderIfExist(), file_name)
    dict_wrestling=pd.read_excel(xlsx_file,None) #Retorna un OrderedDict pero escribirlo en el excel se ve más complicado.
    return dict_wrestling
def generate_dataframes(v_columns):
    db_wrestlers=pd.DataFrame([],columns=v_columns)
    return db_wrestlers
def inactive_wrestlers(cur):
    SQLWAbsences = 'SELECT ct.Name,ih.* FROM Worker_Absences ih,Companies c, Contracts ct, Workers w WHERE c.Initials = ? and ct.CompanyUID = c.UID and w.UID = ct.WorkerUID and ih.WorkerUID=w.UID;' # your query goes here
    rows = cur.execute(SQLWAbsences,'AEW').fetchall()
    v_columns=generate_absence_columns(cur)
    db_inactive=pd.DataFrame([],columns=v_columns)
    for wrestler in rows:
        a_series = pd.Series(wrestler, index = v_columns)
        db_inactive=db_inactive.append(a_series, ignore_index=True)
    return db_inactive
def generate_absence_columns(cur):
    v_columns=list(['WrestlerName'])
    for row in cur.columns(table='Worker_Absences'):
        v_columns.append(row.column_name)
    return v_columns
def generateTagTeamsFirstTime(dict_wrestling,db_wrestlers):
	df_wrestlers=dict_wrestling.get("Single")
	str_key="Tag"
	df_teams=dict_wrestling.get(str_key)
	if (getLen(df_wrestlers)<1)|(getLen(df_teams)<1):
		debugging(f"getLen(df_wrestlers): {getLen(df_wrestlers)}\ngetLen(df_teams): {getLen(df_teams)}")
		list_wrestlers=db_wrestlers['WrestlerName'].tolist()
		df_teams=generateTagTeamsByWrestlers(list_wrestlers,df_teams.columns)
	dict_wrestling.update({str_key:df_teams})
def generateTagTeamsByWrestlers(list_wrestlers,tag_teams_columns):
	
	v_combination=combinations(list_wrestlers,2)#Tag teams
	df_teams=pd.DataFrame([],columns=tag_teams_columns)
	for tagMembers in v_combination:
		v_tagTeams=[]
		v_tagMembers=list(tagMembers)
		tagName=str(v_tagMembers[0])+" & "+str(v_tagMembers[1])
		v_tagTeams.append(tagName)
		v_tagTeams.extend(v_tagMembers)
		v_tagTeams.append(0)
		v_tagTeams.append(0)
		v_tagTeams.append(0)
		v_tagTeams.append(None)
		v_tagTeams.append(None)
		v_tagTeams.append(None)
		v_tagTeams.append(None)
		v_tagTeams.append(None)
		v_tagTeams.append(None)
		v_tagTeams.append(0) #BestRating
		df_teams.loc[len(df_teams)] = v_tagTeams
	return df_teams
def inactivate_wrestlers(db_inactive,db_wrestler):
    db_wrestler['Active']=1
    db_wrestler.loc[(db_wrestler['WrestlerName']
                  .isin(db_inactive.get('WrestlerName'))),'Active']=0
    return db_wrestler
def generateDbTeamsAEW(cur):
    #complement1=', (Select ct.Name from Companies c1,Contracts ct where c1.Initials =\'AEW\' and ct.CompanyUID = c1.UID and tt.Worker1=ct.WorkerUID) WrestlerName1'
    #complement2=', (Select ct.Name from Companies c1,Contracts ct where c1.Initials =\'AEW\' and ct.CompanyUID = c1.UID and tt.Worker2=ct.WorkerUID) WrestlerName2'
    SQL = f'select distinct tt.* from Companies c,Tag_Teams tt WHERE c.Initials = ? and tt.CompanyUID=c.UID and tt.Team_Type not like \'Inactive%\';' # your query goes here  
    #SQL = f'select distinct tt.* {complement1} {complement2} from Companies c,Tag_Teams tt WHERE c.Initials = ? and tt.CompanyUID=c.UID and tt.Team_Type not like \'Inactive%\';' # your query goes here  
    rows = cur.execute(SQL,'AEW').fetchall()
    v_columns=generate_tagteams_columns(cur)
    db_teamsAEW=pd.DataFrame([],columns=v_columns)
    for wrestler in rows:
        a_series = pd.Series(wrestler, index = v_columns)
        db_teamsAEW=db_teamsAEW.append(a_series, ignore_index=True)
    return db_teamsAEW
def generate_tagteams_columns(cur):
    v_columns=list([])
    for row in cur.columns(table='Tag_Teams'):
        v_columns.append(row.column_name)
    return v_columns
def generateStaffAWE(cur):
    dict_staff={}
    db_road_agents=generateRoadAgents(cur)
    db_referees=generateReferees(cur)
    db_interviewers=generateInterviewers(cur)
    dict_staff['RoadAgents']=(db_road_agents)
    dict_staff['Referees']=(db_referees)
    dict_staff['Interviewers']=(db_interviewers)
    return dict_staff
def generateRoadAgents(cur):
    v_columns=generate_road_agents_columns()
    db_road_agents=pd.DataFrame([],columns=v_columns)
    db_road_agents=consultRoadAgents(cur,db_road_agents)
    db_road_agents=orderRoadAgents(db_road_agents)
    return db_road_agents
def generate_road_agents_columns():
    v_columns=list(['WorkerUID','WorkerName','Perception','Quality','Psychology','Experience','Respect'])
    return v_columns
def consultRoadAgents(cur,db_road_agents):
    SQL = f'select ct.WorkerUID,ct.Name,ct.Perception,(w.Psychology*0.45+w.Experience*0.45+w.Respect*0.1),w.Psychology,w.Experience,w.Respect from Companies c,Contracts ct,Workers w WHERE c.Initials = ? and ct.CompanyUID=c.UID and ct.Road_Agent=True and w.UID=ct.WorkerUID;' # your query goes here  
    rows = cur.execute(SQL,'AEW').fetchall()
    for roadAgents in rows:
        a_series = pd.Series(roadAgents, index = list(db_road_agents.columns))
        db_road_agents=db_road_agents.append(a_series, ignore_index=True)
    return db_road_agents
def orderRoadAgents(db_road_agents):
    return sortBy(db_road_agents,['Quality'])
def generateReferees(cur):
    v_columns=generate_referees_columns()
    db_referees=pd.DataFrame([],columns=v_columns)
    db_referees=consultReferees(cur,db_referees)
    db_referees=orderReferees(db_referees)
    return db_referees
def generate_referees_columns():
    v_columns=list(['WorkerUID','WorkerName','Perception','Refereeing'])
    return v_columns
def consultReferees(cur,db_referees):
    SQL = f'select ct.WorkerUID,ct.Name,ct.Perception,w.Refereeing from Companies c,Contracts ct,Workers w WHERE c.Initials = ? and ct.CompanyUID=c.UID and ct.Referee=True and w.UID=ct.WorkerUID;' # your query goes here  
    rows = cur.execute(SQL,'AEW').fetchall()
    for referees in rows:
        a_series = pd.Series(referees, index = list(db_referees.columns))
        db_referees=db_referees.append(a_series, ignore_index=True)
    return db_referees
def orderReferees(db_referees):
    return sortBy(db_referees,['Refereeing'])
def generateInterviewers(cur):
    v_columns=generate_interviewers_columns()
    db_interviewers=pd.DataFrame([],columns=v_columns)
    db_interviewers=consultInterviewers(cur,db_interviewers)
    db_interviewers=orderInterviewers(db_interviewers)
    return db_interviewers
def generate_interviewers_columns():
    v_columns=list(['WorkerUID','WorkerName','Perception','Microphone','Charisma','Acting','South_East'])
    return v_columns
def consultInterviewers(cur,db_interviewers):
    SQL = f'select ct.WorkerUID,ct.Name,ct.Perception,w.Microphone,w.Charisma,w.Acting,w.South_East from Companies c,Contracts ct,Workers w WHERE c.Initials = ? and ct.CompanyUID=c.UID and (ct.On_Screen_Personality=True or ct.Colour_Commentator=True) and ct.Wrestler=False and w.UID=ct.WorkerUID;' # your query goes here  
    return consult(cur,SQL,db_interviewers)
def consult(cur,SQL,db,paraByDefault=True):
    if paraByDefault:
        rows = cur.execute(SQL,getCompanyInitials()).fetchall()
    else:        
        rows =cur.execute(SQL).fetchall()
    for elements in rows:
        a_series = pd.Series(elements, index = list(db.columns))
        db=db.append(a_series, ignore_index=True)
    return db
def orderInterviewers(db_interviewers):
    return sortBy(db_interviewers,['South_East','Microphone','Charisma','Acting'])
def getActiveStablesInCompany(cur):
	v_columns=generate_stables_columns()
	df_stables=pd.DataFrame([],columns=v_columns)
	df_stables=consultStables(cur,df_stables)
	print(f'getActiveStablesInCompany\n{df_stables}')
	return df_stables
def generate_stables_columns():
	v_columns=[StableColumnsTable.NAME.value,StableColumnsTable.COMPANY_UID.value,StableColumnsTable.COMPANY_NAME.value,StableColumnsTable.ACTIVE.value]
	v_columns.extend(StableColumnsTable.LST_MEMBERS.value)
	return v_columns
def consultStables(cur,df_stables):
    SQL="""
    SELECT s.Name, s.CompanyUID,s.CompanyName,s.Active,s.Member1
    ,s.Member2
    ,s.Member3
    ,s.Member4
    ,s.Member5
    ,s.Member6
    ,s.Member7
    ,s.Member8
    ,s.Member9
    ,s.Member10
    ,s.Member11
    ,s.Member12
    ,s.Member13
    ,s.Member14
    ,s.Member15
    ,s.Member16
    ,s.Member17
    ,s.Member18
    FROM Stables s, Companies c
    WHERE c.UID=s.CompanyUID
    and c.Initials = ?;
    """
    return consult(cur,SQL,df_stables)
def getMatchHistory(cur):
    v_columns=generate_matchHistory_columns()
    df_matchHistory=pd.DataFrame([],columns=v_columns)
    df_matchHistory=consultMatchHistory(cur,df_matchHistory)
    return df_matchHistory
def generate_matchHistory_columns():
    v_columns=[column_.value for column_ in MatchHistoryColumns]
    return v_columns
def consultMatchHistory(cur,df_matchHistory):
    SQL="""
    SELECT c.Initials,mh.Match_Type,mh.Rating,mh.Which_Side_Won,mh.Extra_Notes,mhw.WorkerUID,mhw.Which_Side
    FROM Match_Histories mh, Match_Histories_Wrestlers mhw, Companies c
    WHERE mh.CompanyUID=c.UID
    and mh.UID=mhw.MatchHistoryUID
    and c.Initials = ?;
    """
    return consult(cur,SQL,df_matchHistory)
def generateMatchResume(cur):
    dict_matchResume={}
    v_columns=generate_matchResume_columns()
    db_matchResume=pd.DataFrame([],columns=v_columns)
    db_matchResume=consultMatchResume(cur,db_matchResume)
    db_matchResume['Victories']=pd.to_numeric(db_matchResume['Victories'])
    db_matchResume['Losses']=pd.to_numeric(db_matchResume['Losses'])
    db_matchResume['Percentage']=pd.to_numeric(db_matchResume['Percentage'])
    db_matchResume=orderMatchResume(db_matchResume)
    dict_matchResume['MatchResume']=(db_matchResume)
    return dict_matchResume
def generate_matchResume_columns():
    v_columns=list(['WorkerUID','WorkerName','Victories','Losses','Percentage'])
    return v_columns
def consultMatchResume(cur,db_matchResume):
    Company="\'AEW\'"
    params = ({'company':Company})
    SQL="""
    SELECT w.UID,ct.Name,sum(IIF(mhw.Which_Side=mh.Which_Side_Won, 1, 0)) as victories, 
    sum(IIF(mhw.Which_Side=mh.Which_Side_Won, 0, 1)) as loses, sum(IIF(mhw.Which_Side=mh.Which_Side_Won, 1, 0))/count(1) as percentage
    FROM Companies c,Match_Histories mh,Match_Histories_Wrestlers mhw, Previous_Shows ps, Workers w,Contracts ct
    WHERE c.Initials = %(company)s and mh.CompanyUID=c.UID and mhw.MatchHistoryUID=mh.UID and ct.CompanyUID=c.UID
    and ps.UID=mh.PreviousShowUID and w.UID=mhw.WorkerUID and ct.WorkerUID=w.UID 
    and mh.Match_Type Is not Null and mh.Match_Type <> 'None'    
    group by w.UID,ct.Name    
    ;    
    """%params
    return consult(cur,SQL,db_matchResume,False)
def orderMatchResume(db_matchResume):
    return sortBy(db_matchResume,['Victories','Losses','WorkerName'])
def generateActualChampions(cur):
	dict_actualChampions={}
	v_columns=generate_actualChampions_columns()
	db_actualChampions=pd.DataFrame([],columns=v_columns)
	db_actualChampions=consultActualChampions(cur,db_actualChampions)
	db_actualChampions['Prestige']=db_actualChampions['Prestige'].astype(int)
	db_actualChampions['TitleUID']=db_actualChampions['TitleUID'].astype(int)
	db_actualChampions['Active']=db_actualChampions['Active'].astype(bool)
	db_actualChampions['Holder1']=db_actualChampions['Holder1'].astype(int)
	db_actualChampions['Holder2']=db_actualChampions['Holder2'].astype(int)
	db_actualChampions['Holder3']=db_actualChampions['Holder3'].astype(int)
	dict_actualChampions['Titles']=db_actualChampions
	return dict_actualChampions
def generate_actualChampions_columns():
    v_columns=list(['TitleUID','TitleName','BeltStyle','BeltLevel', 'Prestige'
                    , 'Function', 'Active', 'Gender_Limits'
    , 'Brand','Holder1','HolderName1', 'Holder2','HolderName2', 'Holder3','HolderName3'])
    return v_columns
def consultActualChampions(cur,dict_actualChampions):
	Company="\'AEW\'"
	params = ({'company':Company})
	SQL = """
	select tb.UID, tb.Name, tb.BeltStyle, tb.BeltLevel, tb.Prestige, tb.Function, tb.Active, tb.Gender_Limits
	, tb.Brand,tb.Holder1,(SELECT ct.Name
	FROM Contracts ct
	Where ct.CompanyUID = tb.CompanyUID and  tb.Holder1= ct.WorkerUID) as HolderName1, tb.Holder2,(SELECT ct.Name
	FROM Contracts ct
	Where ct.CompanyUID = tb.CompanyUID and  tb.Holder2= ct.WorkerUID) as HolderName2, tb.Holder3,(SELECT ct.Name
	FROM Contracts ct
	Where ct.CompanyUID = tb.CompanyUID and  tb.Holder3= ct.WorkerUID) as HolderName3
	from Title_Belts tb 
	where 
		(tb.Holder1 in (select ct.WorkerUID 
					from Companies c,Contracts ct,Workers w 
					WHERE c.Initials = %(company)s and ct.CompanyUID=c.UID and w.UID=ct.WorkerUID) 
		or 
		tb.Holder2 in (select ct.WorkerUID 
					from Companies c,Contracts ct,Workers w 
					WHERE c.Initials = %(company)s and ct.CompanyUID=c.UID and w.UID=ct.WorkerUID)
		or
		tb.Holder3 in (select ct.WorkerUID 
					from Companies c,Contracts ct,Workers w 
					WHERE c.Initials = %(company)s and ct.CompanyUID=c.UID and w.UID=ct.WorkerUID))
				and tb.CompanyUID in (select c.UID from Companies c WHERE c.Initials = %(company)s);
	"""%params
	return consult(cur,SQL,dict_actualChampions,False)
def generateChildCompanyWrestlers(cur):
	dict_childcompany_wrestlers={}
	v_columns=generate_childcompany_wrestlers_columns(cur)
	db=pd.DataFrame([],columns=v_columns)
	db=consultChildCompanyWrestlers(cur,db)
	db=calculatePopularity(db)
	db=calculateInRingAction(db)
	db=calculateBestRating(db)
	db=changeColumnsPosition(db)
	db=db.T.drop_duplicates().T
	dict_childcompany_wrestlers['Wrestlers']=db
	return dict_childcompany_wrestlers
def generateChildCompanyWrestlersToFollow(cur):
    dict_childcompany_wrestlers={}
    v_columns=generate_childcompany_wrestlers_columns(cur)
    db=pd.DataFrame([],columns=v_columns)
    db=consultChildCompanyWrestlersToFollow(cur,db)
    db=calculatePopularity(db)
    db=calculateInRingAction(db)
    db=calculateBestRating(db)
    db=changeColumnsPosition(db)
    dict_childcompany_wrestlers['WrestlersToFollow']=db
    return dict_childcompany_wrestlers
def generate_childcompany_wrestlers_columns(cur):
    v_columns=list(['CompanyName','Perception','Brand','ExpectedShows','Babyface','WorkerName'])
    for row in cur.columns(table='Workers'):
        v_columns.append(row.column_name)
    return v_columns
def consultChildCompanyWrestlers(cur,db):
    SQL = """
    SELECT ct.CompanyName,ct.Perception,ct.Brand,ct.ExpectedShows,ct.Babyface,ct.Name,w.* FROM Companies c, 
    Contracts ct, Workers w 
    WHERE ct.CompanyUID in (24,381,5,46,186) and ct.CompanyUID = c.UID and w.UID = ct.WorkerUID and ct.Wrestler=True
    and w.Birth_Year>1990
    """
    return consult(cur,SQL,db,False)
def mergeTeams(db_teamsP,db_teamsAEW):
	v_columns=db_teamsP.columns
	df_copy=db_teamsAEW.copy()
	df_copy=df_copy.rename(columns={'Name': 'Tag Name','Worker1':'WUID1','Worker2':'WUID2','WorkerName1':'W1','WorkerName2':'W2','Experience':'EXP'})
	dict_types={'Individuals':1,'Unit':2,'Permanent Unit':3}
	for key in dict_types.keys():
		df_copy.loc[df_copy['Team_Type']==key,['Type']]=dict_types.get(key)
	df_copy['UID_TEAM']=db_teamsAEW.agg(lambda x:""+str(x['Worker1'])+"_"+str(x['Worker2']), axis=1)
	df_copy['Popularity']=0
	df_copy['BestRating']=0
	df_copy['Gender']=None
	df_copy['Brand']=None
	df_copy=df_copy[v_columns]
	#Sync the types of each columns
	for index, value in db_teamsP.dtypes.items():
		df_copy[index]=df_copy[index].astype(value)
	for index,data in df_copy.iterrows():
		df_found=db_teamsP.loc[((db_teamsP['W1']==data['W1'])&(db_teamsP['W2']==data['W2']))|((db_teamsP['W2']==data['W1'])&(db_teamsP['W1']==data['W2']))]
		len_found=getLen(df_found)
		if len_found==0:
			pd.concat([db_teamsP, data], ignore_index=True)
		else:
			if len_found>1:
				df_found=df_found.drop(index=df_found.head(len_found-1).index)
			df_found['EXP']=data['EXP']
			df_found['Tag Name']=data['Tag Name']
			df_found['Type']=data['Type']
	#db_teamsP=pd.merge(df_copy,db_teamsP,on=list(v_columns),  how='outer')
	return db_teamsP
def put_experience(db_teamsP,db_teamsAEW):
	db_teamsAEW.Worker1=db_teamsAEW.Worker1.astype(float)
	db_teamsAEW.Worker2=db_teamsAEW.Worker2.astype(float)
	db_teamsAEW['UID_TEAM']=db_teamsAEW.agg(lambda x:""+str(x['Worker1'])+"_"+str(x['Worker2']), axis=1)
	db_teamsP.WUID1=db_teamsP.WUID1.astype(float)
	db_teamsP.WUID2=db_teamsP.WUID2.astype(float)
	#db_teamsAEW=db_teamsAEW.merge(db_teamsP,how='inner', left_on=['Worker1','Worker2'], right_on=['WUID1','WUID2'])    
	db_teamsp_bk=db_teamsP
	db_teamsp_bk['UID_TEAM']=db_teamsp_bk.agg(lambda x:str(x['WUID1'])+"_"+str(x['WUID2']), axis=1)    
	db_teamsp_bk=db_teamsp_bk.loc[db_teamsp_bk['UID_TEAM'].isin(db_teamsAEW['UID_TEAM'])]
	db_teamsAEW=db_teamsAEW.loc[db_teamsAEW['UID_TEAM'].isin(db_teamsp_bk['UID_TEAM'])]
	db_teamsp_bk=db_teamsp_bk.sort_values(by=['UID_TEAM'],ascending=False)
	db_teamsAEW=db_teamsAEW.sort_values(by=['UID_TEAM'],ascending=False)
	db_teamsAEW=db_teamsAEW.drop_duplicates()
	db_teamsp_bk=db_teamsp_bk.drop_duplicates()
	db_teamsp_bk['EXP'] = np.where(db_teamsp_bk['UID_TEAM'].values == db_teamsAEW['UID_TEAM'].values, db_teamsAEW['Experience'].astype(int), 0)
	db_teamsp_bk['Tag Name'] = np.where(db_teamsp_bk['UID_TEAM'].values == db_teamsAEW['UID_TEAM'].values, db_teamsAEW['Name'], db_teamsp_bk['Tag Name'])
	dict_types={'Individuals':1,'Unit':2,'Permanent Unit':3}
	for key in dict_types.keys():
		db_teamsAEW.loc[db_teamsAEW['Team_Type']==key,['Type']]=dict_types.get(key)
	db_teamsp_bk['Type'] = np.where(db_teamsp_bk['UID_TEAM'].values == db_teamsAEW['UID_TEAM'].values, db_teamsAEW['Type'],0)
	#db_teamsp_bk['EXP']=db_teamsAEW['Experience'].astype(int)
	#print(f'Size_db_teamsAEW\t{db_teamsAEW.shape}\nSize_db_teamsP\t{db_teamsp_bk.shape}')
	#print(f'db_teamsp_bk\n{db_teamsp_bk}')
	#print(f'db_teamsp_bk\n{db_teamsAEW}')    
	db_teamsP.update(db_teamsp_bk)
	return db_teamsP
def changeColumnsPosition(df):
	v_columns=df.columns.tolist()
	len_columns=getLen(v_columns)
	wn_list = list(filter(lambda x: v_columns[x] == 'WrestlerName', range(len_columns)))
	p_list = list(filter(lambda x: v_columns[x] == 'Perception', range(len_columns)))
	pop_list = list(filter(lambda x: v_columns[x] == 'BestRating', range(len_columns)))
	uid_list = list(filter(lambda x: v_columns[x] == 'UID', range(len_columns)))
	
	prof_list = list(filter(lambda x: v_columns[x] == 'Profile', range(len_columns)))
	nm_list = list(filter(lambda x: v_columns[x] == 'Name', range(len_columns)))
	rop_list = list(filter(lambda x: v_columns[x] == 'RateOnPassive', range(len_columns)))
	roa_list = list(filter(lambda x: v_columns[x] == 'RateOnActive', range(len_columns)))
	
	gender_list = list(filter(lambda x: v_columns[x] == 'Gender', range(len_columns)))
	user_list = list(filter(lambda x: v_columns[x] == 'User', range(len_columns)))
	if(getLen(wn_list)>0):#Because ChildCompanyWrestlers
		v_columns[p_list[0]], v_columns[wn_list[0]] = v_columns[wn_list[0]], v_columns[p_list[0]]
	v_columns[uid_list[0]], v_columns[pop_list[0]] = v_columns[pop_list[0]], v_columns[uid_list[0]]
	if (getLen(rop_list)>0):#Because ChildCompanyWrestlers
		v_columns[prof_list[0]], v_columns[rop_list[0]] = v_columns[rop_list[0]], v_columns[prof_list[0]]
		v_columns[nm_list[0]], v_columns[roa_list[0]] = v_columns[roa_list[0]], v_columns[nm_list[0]]
		v_columns[gender_list[0]], v_columns[user_list[0]] = v_columns[user_list[0]], v_columns[gender_list[0]]
	df=df[v_columns]
	return df
def consultChildCompanyWrestlersToFollow(cur,db):
    SQL = """
    SELECT ct.CompanyName,ct.Perception,ct.Brand,ct.ExpectedShows,ct.Babyface,ct.Name,w.* 
    FROM ((Workers w 
    LEFT JOIN Contracts ct ON w.UID = ct.WorkerUID)
    LEFT JOIN Companies c ON ct.CompanyUID = c.UID)
    WHERE ct.Wrestler=True
    and w.Birth_Year>1990
    """
    return consult(cur,SQL,db,False)
def generateChildCompanies(cur):
    dict_childcompany={}
    v_columns=generate_childcompany_columns(cur)
    db=pd.DataFrame([],columns=v_columns)
    db=consultChildCompanies(cur,db)
    db=calculatePopularity(db)
    db=changeColumnPositionChildCompanies(db)
    sort_columns=['Prestige','Popularity','Ranking','Size']
    db['Prestige']=db['Prestige'].astype(int)
    db=sortBy(db,sort_columns)
    dict_childcompany['Companies']=db
    return dict_childcompany
def generate_childcompany_columns(cur):
    v_columns=[]
    for row in cur.columns(table='Companies'):
        v_columns.append(row.column_name)
    return v_columns
def consultChildCompanies(cur,db):
    SQL = """
    SELECT c.* 
    FROM Companies c 
    WHERE c.UID in (24,381,5,46,186,338)
    """
    return consult(cur,SQL,db,False)
def changeColumnPositionChildCompanies(df):
    v_columns=df.columns.tolist()
    uid_list = list(filter(lambda x: v_columns[x] == 'UID', range(getLen(v_columns))))
    pop_list = list(filter(lambda x: v_columns[x] == 'Popularity', range(getLen(v_columns))))
    pro_list = list(filter(lambda x: v_columns[x] == 'Profile', range(getLen(v_columns))))
    size_list = list(filter(lambda x: v_columns[x] == 'Size', range(getLen(v_columns))))
    url_list = list(filter(lambda x: v_columns[x] == 'URL', range(getLen(v_columns))))
    rank_list = list(filter(lambda x: v_columns[x] == 'Ranking', range(getLen(v_columns))))
    v_columns[uid_list[0]], v_columns[pop_list[0]] = v_columns[pop_list[0]], v_columns[uid_list[0]]
    v_columns[pro_list[0]], v_columns[size_list[0]] = v_columns[size_list[0]], v_columns[pro_list[0]]
    v_columns[url_list[0]], v_columns[rank_list[0]] = v_columns[rank_list[0]], v_columns[url_list[0]]
    df=df[v_columns]
    return df
def getWhereWorkMyWrestlers(cur):
    dict_childcompany={}
    v_columns=generate_whereWorkMyWrestlersColumns()
    db=pd.DataFrame([],columns=v_columns)
    db=consultWhereWorkMyWrestlers(cur,db).drop_duplicates()
    #sort_columns=['WName','UID','Company']
    db=sortBy(db,v_columns)
    db['UID']=db['UID'].astype(int)
    dict_childcompany['WhereWorkMyWrestlers']=db
    return dict_childcompany
def generate_whereWorkMyWrestlersColumns():
    v_columns=['WName','UID','Company']
    return v_columns
def consultWhereWorkMyWrestlers(cur,df):
    Company="\'AEW\'"
    params = ({'company':Company})
    SQL = """
    SELECT wk.WName,c.UID,c.Initials
    FROM 
    ((((SELECT w.UID,ct.Name as WName FROM (((TV_Shows tvs 
    Inner join Companies c on c.UID=tvs.CompanyUID)
    Inner join Contracts ct on ct.CompanyUID=c.UID)
    Inner join Workers w on ct.WorkerUID=w.UID)
    where c.Initials = %(company)s and ct.Wrestler=True) wk
    inner join Workers w on w.UID=wk.UID)
    inner join Contracts ct on ct.WorkerUID=w.UID)
    inner join Companies c on ct.CompanyUID=c.UID)
    """%params
    return consult(cur,SQL,df,False)
def sortBy(db,sort_columns):
	db=db.sort_values(by=sort_columns,ascending=False)
	return db
def readWhereWorkMyWrestlersFromChildCompanyWrestlers():
	try:
		dict_=read_file('ChildCompanyWrestlers.xlsx') #Retorna un OrderedDict pero escribirlo en el excel se ve más complicado.
		df_whereMyWrestlersWorks=dict_.get(c_key_whereMyWrestlersWorks)
	except:
		df_whereMyWrestlersWorks=pd.DataFrame([])
	return df_whereMyWrestlersWorks
def getApplicationTEW2020():
    try:
        for proc in psutil.process_iter():
            if proc.name() == "TEW2020.exe":
                print(pywinauto.findwindows.find_windows(process=proc.pid))
                #app = Application(backend='uia').connect(handle=1250060)
                app = Application(backend='uia').connect(process=proc.pid)
    except:
        #We need Administrator role to do this part, so first run python with this role
        app = Application(backend="uia").start(r"E:\Program Files (x86)\GDS\TEW2020\TEW2020.exe")
    return app
def getWrestlersWithMajorPriority(app,df_whereMyWrestlersWorks,v_companyInitials):
	#2 take all the unique name of wrestlers
	set_wrestlersWorkForAnotherCompany=df_whereMyWrestlersWorks['WName'].unique()
	#3 Focus in the main screen of the game        
	dlg = app.top_window()
	dlg.set_focus()
	gray_screen = captureGrayScreen(dlg)    
	#4 Locate the image of the button Roster
	#4.1 Get the location
	top_left,bottom_right=getLocalizationOfTheButtonRoster(gray_screen)    
	#4.2 Click on it
	clickOn(top_left,bottom_right)
	#5 Iterate each name
	#5.0 Before begin the iteration create a DF to store the wrestler with other priority
	df_priorityFound=pd.DataFrame([])
	for workerName in set_wrestlersWorkForAnotherCompany:
	#5.1 send the name by keytext or sendmessage or the option found
		pyautogui.write(workerName)
	#5.2 search for the active icon for wrestler
		dlg = app.top_window()
		dlg.set_focus()
		gray_screen = captureGrayScreen(dlg)
		top_left,bottom_right=getLocalizationOfTheWrestlerIcon(gray_screen)
	#5.3 do the click action over the active icon for wrestler
		clickOn(top_left,bottom_right)        
	#5.4 Find the location of the image of Priority word
		dlg = app.top_window()
		gray_screen = captureGrayScreen(dlg)
		top_left,bottom_right=getLocalizationOfThePriorityWord(gray_screen)        
	#5.5 Adjust the coordinates to take a picture of the Priority's section weight 451px by height 71px
		v_rectangle=getPriorityRectangle(top_left,bottom_right)
		gray_screen = captureGrayScreen(dlg,v_rectangle)
	#5.6 transform the picture to text
		text=pytesseract.image_to_string(gray_screen)        
		##print(f'{text}')
	#5.7 transform the text to a list splited by space in blank
		text=str(text).replace('\n',' ').replace(',','').replace('.','').replace('‘','')        
		if text.__contains__('My pri '):
			#cv2.imshow("Image Input", gray_screen)
			#cv2.waitKey(0)
			#dlg.set_focus()
			text=str(text).replace('My pri ','My pri are with ')
		lst_words=text.split(' ')
	#5.8 Get the index of the initials of our compay
		try:
			v_index=lst_words.index(v_companyInitials)
		except:
			cv2.imshow("Image Input", gray_screen)
			cv2.waitKey(0)
	#5.9 If the index is greather than 12, you aren't the priority
		if v_index>12:        
		#5.9.1 Take the rows for that wname with the initials of the others companies
		#5.9.2 send those rows to the DF
			df_tmp=df_whereMyWrestlersWorks.loc[(df_whereMyWrestlersWorks['WName']==workerName)]
			lst_priorCompanies=[]
			for vcompany in df_tmp['Company'].unique():
				try:
					v_index2=lst_words.index(vcompany)
					##print(f'{v_index2,v_index}\t{vcompany}')
					if v_index2<v_index:
						lst_priorCompanies.append(lst_words[v_index2])
				except:
					print(f'We could not found {vcompany} company for {workerName} ')
			df_priorityFound=df_priorityFound.append(df_tmp.loc[(df_tmp['Company'].isin(lst_priorCompanies))])
	#5.10 find the closer close icon to the image of Priority word
		dlg = app.top_window()
		gray_screen = captureGrayScreen(dlg)
		top_left,bottom_right=getLocalizationOfTheCloseIcon(gray_screen)
	#5.11 close the window
	#5.12 repeat since 5.1 until 5.11 until finish each row
		clickOn(top_left,bottom_right)        
	#6 close the actual window
	dlg = app.top_window()
	gray_screen = captureGrayScreen(dlg)
	top_left,bottom_right=getLocalizationOfTheCloseIcon(gray_screen)
	clickOn(top_left,bottom_right)
	#7 return the DF
	return df_priorityFound
def getLocalizationOfTheButtonRoster(gray_screen):    
    route_searched_image_name=".\Images\Buttons\Roster.png"    
    top_left,bottom_right=getLocatiozationOfImage(route_searched_image_name,gray_screen)
    #print(f'getLocalizationOfTheButtonRoster\t{top_left,bottom_right}')
    return top_left,bottom_right
def getLocatiozationOfImage(route_searched_image_name,gray_screen,print_max_val=False):
    np_image = cv2.imread(route_searched_image_name)
    gray_image = cv2.cvtColor(np_image, cv2.COLOR_BGR2GRAY)
    matches = cv2.matchTemplate(gray_screen, gray_image, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(matches)
    top_left = max_loc
    w, h = gray_image.shape[::-1]
    bottom_right = (top_left[0] + w, top_left[1] + h)
    if print_max_val:
        print(f'{max_val}')
    if max_val<0.98:
        return (-1,-1),(-1,-1)
    return top_left,bottom_right
def clickOn(top_left,bottom_right):
    pyautogui.moveTo((top_left[0]+bottom_right[0])/2,(top_left[1]+bottom_right[1])/2)
    pyautogui.click()
def captureGrayScreen(dlg,rectangle=None):
    if rectangle is None:
        screen=dlg.capture_as_image()
    else:
        screen=dlg.capture_as_image(rectangle)
    np_screen = np.array(screen, dtype = np.uint8)
    gray_screen = cv2.cvtColor(np_screen, cv2.COLOR_BGR2GRAY)
    return gray_screen
def getLocalizationOfTheWrestlerIcon(gray_screen):
    route_searched_image_name=".\Images\Buttons\WrestlerIcon.png"    
    top_left,bottom_right=getLocatiozationOfImage(route_searched_image_name,gray_screen)
    #print(f'getLocalizationOfTheWrestlerIcon\t{top_left,bottom_right}')
    return top_left,bottom_right
def getLocalizationOfThePriorityWord(gray_screen):
    route_searched_image_name=".\Images\Screenshots\PriorityWord.png"    
    top_left,bottom_right=getLocatiozationOfImage(route_searched_image_name,gray_screen)
    #print(f'getLocalizationOfThePriorityWord\t{top_left,bottom_right}')
    return top_left,bottom_right
def getPriorityRectangle(top_left,bottom_right):
    from pywinauto import win32structures
    expected_rect = win32structures.RECT()
    expected_rect.left = top_left[0]
    expected_rect.top = bottom_right[1]
    expected_rect.right = top_left[0]+444
    expected_rect.bottom = bottom_right[1]+46
    return expected_rect
def getLocalizationOfTheCloseIcon(gray_screen):
    route_searched_image_name=".\Images\Buttons\CloseIcon.png"
    top_left,bottom_right=getLocatiozationOfImage(route_searched_image_name,gray_screen)
    #print(f'getLocalizationOfTheCloseIcon\t{top_left,bottom_right}')
    return top_left,bottom_right
def readPriorityFoundFromChieldCompanyWrestlers():
    dict_=read_file('ChildCompanyWrestlers.xlsx') #Retorna un OrderedDict pero escribirlo en el excel se ve más complicado.
    df_priorityFound=dict_.get('wrestlersWithOtherPriority')
    return df_priorityFound
def generateDfCompanyShows(app,set_InitialsCompanies):
	dlg=putInCompanySumary(app)
	#13 Clean memory of the screen shots
	#14 Iterate each name of company founded
	#14.P1 We must have the list of our shows
	#14.P2 We must have a DF with the following columns ['Company','Show','ShowType','DayOfWeek','Month','Week']
	df_companyShows=pd.DataFrame([],columns=['Company','Show','ShowType','DayOfWeek','Week','Month','MaxMatches','Brand','ShowTime','PreShowTime','TimeMatch','TimeDarkMatch','TVShowType'])
	#14.P3 The allowed values for:
	#14.P3.1  'ShowType' are (Event,TV)
	#14.P3.2  'DayOfWeek' are (Monday,Tuesday,Wednesday,Thursday,Friday,Saturday,Sunday,Every)
	#14.P3.3  'Month' are (January,February,March,April,May,June,July,August,September,October,November,December,Every)    
	for initials in set_InitialsCompanies:        
	#14.1 send the name by keytext or sendmessage or the option founded
		pyautogui.write(initials)
	#14.2 Take a screen shot and Find the coordinates of the QuickJump button and click on it
		gray_screen = captureGrayScreen(dlg)
		top_left,bottom_right=getLocalizationOfTheQuickJumpButton(gray_screen)
		#cv2.imshow("Image Input", gray_screen)
		#cv2.waitKey(0)
		#dlg.set_focus()
		clickOn(top_left,bottom_right)
		dlg = app.top_window()
	#14.3 Take a screen shot and Find the coordinates of the EventsAndTV button and click on it
		gray_screen = captureGrayScreen(dlg)
		top_left,bottom_right=getLocalizationOfTheEventsAndTVButton(gray_screen)
		clickOn(top_left,bottom_right)
	#14.4 Take a screen shot and Find the coordinates of blue circle icon
		dlg = app.top_window()
		gray_screen = captureGrayScreen(dlg)
		blueCircleIcon_top_left,blueCircleIcon_bottom_right=getLocalizationOfTheBlueCircleIcon(gray_screen)
		lastShow=None
		while True:
		#14.5 Take a screen shot beginin in the end x and the beginin of y. weight 490px by height 241px
			v_rectangle=getBlueCircleIconRectangle(blueCircleIcon_top_left,blueCircleIcon_bottom_right)
			gray_screen = captureGrayScreen(dlg,v_rectangle)
		#14.6 Transform the picture to text
			text=pytesseract.image_to_string(gray_screen)
		#14.7 Split the text by keywords like \n, Company's Initials, 'Event,' word, 'TV,' word
			lst_lines=text.split('\n')                
		#14.7.1 For Event word split we can split by colon (,) we will obtain DayOfWeek(Sunda,Friday,etc),Week #(# is 1,2,3), Month
			s_companyEvent = list(filter(lambda line: (str(line).__contains__('Event,')), lst_lines))
			#print(f'{type(s_companyEvent)}\n{s_companyEvent}')
			lst_detailsPerEvent=list(map(lambda line:str(str(line).split('Event,')[1]).replace(' ','').replace('Week','W')
										 .replace('|','')
										 .replace('=»','')
										 .replace('=','')
										 .split(',')
										 ,s_companyEvent))        
		#14.7.2 For 'TV,' word split we can split by blank space ( ) we will obtain the word Every with an space and followed by DayOfWeek
			s_companyShow= list(filter(lambda line: (str(line).__contains__(initials)), lst_lines))
			s_companyTVShow= list(filter(lambda line: (str(line).__contains__('TV,')), lst_lines))
			#print(f'{type(s_companyShow)}\n{s_companyShow}')
			#print(f'{type(s_companyTVShow)}\n{s_companyTVShow}')
			lst_detailsPerTvShow=list(map(lambda line:str(str(line).split('TV,')[1]).replace(':','').split(' '),s_companyTVShow))
			cant_shows=getLen(s_companyShow)
			cant_tvShows=getLen(s_companyTVShow)
			cant_event=getLen(s_companyEvent)
			pos_tvDayOfWeek=2
			for num in range(0,cant_tvShows):
				lst_fullCompanyShow=[initials]
				lst_fullCompanyShow.append(s_companyShow[num])
				lst_fullCompanyShow.append('TV')
				print(lst_detailsPerTvShow[num])
				lst_fullCompanyShow.append(lst_detailsPerTvShow[num][pos_tvDayOfWeek].capitalize())
				lst_fullCompanyShow.append(lst_detailsPerTvShow[num][(pos_tvDayOfWeek-1)].capitalize())
				lst_fullCompanyShow.append(lst_detailsPerTvShow[num][(pos_tvDayOfWeek-1)].capitalize())
				#pos_tvDayOfWeek=pos_tvDayOfWeek+2
				lst_fullCompanyShow.extend([None,None,None,None,None,None])
				print(lst_fullCompanyShow)
				a_series = pd.Series(lst_fullCompanyShow, index = df_companyShows.columns)
				df_companyShows=df_companyShows.append(a_series, ignore_index=True)
				print(df_companyShows)
			pos_tvDayOfWeek=0
			pos_month=3
			for num in range(cant_tvShows,cant_shows):
				lst_fullCompanyShow=[initials]
				try:
					lst_fullCompanyShow.append(s_companyShow[num])
				except:
					debugging(print(f"{s_companyShow}\n{num}\n{cant_tvShows}\n{cant_event+cant_tvShows}"))
				lst_fullCompanyShow.append('Event')
				try:
					lst_tmp=lst_detailsPerEvent[num-cant_tvShows][pos_tvDayOfWeek:(pos_month+1)]
				except:
					raise Exception(f'list index out of range\n{lst_detailsPerEvent}')
				lst_fullCompanyShow.extend(list(map(lambda word:getNumberOfMonth(word),lst_tmp)))
				#pos_tvDayOfWeek=pos_month+1
				#pos_month=pos_month+3
				lst_fullCompanyShow.extend([None,None,None,None,None,None,None])
				print(lst_fullCompanyShow)
				a_series = pd.Series(lst_fullCompanyShow, index = df_companyShows.columns)
				df_companyShows=df_companyShows.append(a_series, ignore_index=True)
			#14.7.3 Verify if exist the ScroollUp icon
			gray_screen = captureGrayScreen(dlg)
			top_left,bottom_right=getLocalizationOfTheScroollUpIcon(gray_screen)
			if top_left==(-1,-1):
				break
			else:                
			#14.7.3.1 If exist we need to execute 14 pagedown action and reapeat from the step number 14.5
				#print(f'14.7.3.1\n{(lastShow)}\n{df_companyShows.tail(2)}')
				if lastShow is None:
					lastShow=df_companyShows.tail(2)
				else:
					df_copy=df_companyShows.tail(2).reset_index(drop=True)
					lastShow=lastShow.reset_index(drop=True)
					if not (lastShow.equals(df_copy)):
						lastShow=df_copy                    
					else:
						#print(f'Break\t{lastShow}\n{df_copy}')
						break
				for i in range(0,39):
					pyautogui.press('pagedown')
				#print(f'{lastShow}')
				#break
		#list(map(lambda argument:expression,cant_tvShows))
	#14.8 Fill the DF with the information recollected
	#14.9 find the closer close icon to the image of blue circle icon
		gray_screen = captureGrayScreen(dlg)
		top_left,bottom_right=getLocalizationOfTheCloseIcon(gray_screen)
		clickOn(top_left,bottom_right)
		dlg = app.top_window()
	#14.10 Clean memory
	#14.11 Take a screen shot and Find the coordinates of the ListBox and click on it
		gray_screen = captureGrayScreen(dlg)
		top_left,bottom_right=getLocalizationOfTheListBox(gray_screen)
		clickOn(top_left,bottom_right)
		clickOn(top_left,bottom_right)
		#dlg = app.top_window()
	#14.12 repeat 14.1 until 14.11
	#15 find the closer close icon to the image of ListBox and click on it
	gray_screen = captureGrayScreen(dlg)
	top_left,bottom_right=getLocalizationOfTheCloseIcon(gray_screen)
	clickOn(top_left,bottom_right)
	dlg = app.top_window()
	#16 Clean memory	
	#17 Return the DF
	return df_companyShows
def putInCompanySumary(app):
	#9 Read that DF
    #10 Take a screen shot
    dlg = app.top_window()
    dlg.set_focus()
    gray_screen = captureGrayScreen(dlg)
    #11 Find the coordinates of the office's icon and click on it
    top_left,bottom_right=getLocalizationOfTheOfficeIcon(gray_screen)
    clickOn(top_left,bottom_right)
    dlg = app.top_window()
    #12 Find the coordinates of the company's logo and click on it
    gray_screen = captureGrayScreen(dlg)
    top_left,bottom_right=getLocalizationOfTheCompanysLogo(gray_screen)
    clickOn(top_left,bottom_right)
    dlg = app.top_window()
    return dlg
def getLocalizationOfTheOfficeIcon(gray_screen):
    route_searched_image_name=".\Images\Buttons\Office.png"
    top_left,bottom_right=getLocatiozationOfImage(route_searched_image_name,gray_screen)
    #print(f'getLocalizationOfTheOfficeIcon\t{top_left,bottom_right}')
    return top_left,bottom_right
def getLocalizationOfTheCompanysLogo(gray_screen):
    route_searched_image_name="E:\Program Files (x86)\GDS\TEW2020\Pictures\Default\Logos\AEW.jpg"
    #ToDo: Param the route of Companies Logos
    top_left,bottom_right=getLocatiozationOfImage(route_searched_image_name,gray_screen)
    #print(f'getLocalizationOfTheCompanysLogo\t{top_left,bottom_right}')
    return top_left,bottom_right
def getLocalizationOfTheQuickJumpButton(gray_screen):
    route_searched_image_name=".\Images\Buttons\QuickJump.png"
    top_left,bottom_right=getLocatiozationOfImage(route_searched_image_name,gray_screen)
    #print(f'getLocalizationOfTheQuickJumpButton\t{top_left,bottom_right}')
    return top_left,bottom_right
def getLocalizationOfTheEventsAndTVButton(gray_screen):
    route_searched_image_name=".\Images\Buttons\EventsAndTV.png"
    top_left,bottom_right=getLocatiozationOfImage(route_searched_image_name,gray_screen)
    #print(f'getLocalizationOfTheEventsAndTVButton\t{top_left,bottom_right}')
    return top_left,bottom_right
def getLocalizationOfTheBlueCircleIcon(gray_screen):
    route_searched_image_name=".\Images\Screenshots\BlueCircleButton.png"
    top_left,bottom_right=getLocatiozationOfImage(route_searched_image_name,gray_screen)
    #print(f'getLocalizationOfTheBlueCircleIcon\t{top_left,bottom_right}')
    return top_left,bottom_right
def getLocalizationOfTheScroollUpIcon(gray_screen):
    lst_route_searched_image_name=[r".\Images\Buttons\ScrollUpIcon.png",
                                  r".\Images\Buttons\ScrollUpIcon2.png",
                                  r".\Images\Buttons\ScrollUpIcon3.png"]
    for route_searched_image_name in lst_route_searched_image_name:
        top_left,bottom_right=getLocatiozationOfImage(route_searched_image_name,gray_screen,True)
        if top_left==(-1,-1):
            continue
        else:
            break
    #print(f'getLocalizationOfTheScroollUpIcon\t{top_left,bottom_right}')
    return top_left,bottom_right
def getBlueCircleIconRectangle(top_left,bottom_right):
    from pywinauto import win32structures
    expected_rect = win32structures.RECT()
    expected_rect.left = bottom_right[0]+5
    expected_rect.top = top_left[1]
    expected_rect.right = expected_rect.left+490
    expected_rect.bottom = top_left[1]+624
    return expected_rect
def getLocalizationOfTheListBox(gray_screen):
    #ToDo: JK
    route_searched_image_name=".\Images\Buttons\ListBox.png"
    top_left,bottom_right=getLocatiozationOfImage(route_searched_image_name,gray_screen)
    #print(f'getLocalizationOfTheListBox\t{top_left,bottom_right}')
    return top_left,bottom_right
def getNumberOfMonth(month):
    t_months=('January','February','March','April','May','June','July','August','September','October','November','December')
    try:
        index=t_months.index(month)
        return (index+1)
    except:
        return month
def getDfOurShows():
	v_key='Shows'
	dict_param=readParameters()
	df_ourShows=dict_param.get(v_key)
	if df_ourShows is None or len(df_ourShows)==0:
		v_companyInitials=getCompanyInitials()
		set_InitialsCompanies=[v_companyInitials]
		app=getApplicationTEW2020()
		df_ourShows=generateDfCompanyShows(app,set_InitialsCompanies)
		addOrReplaceParameter(v_key,df_ourShows)
	return df_ourShows
def addOrReplaceParameter(key,df):
	dict_parameters=readParameters()
	dict_parameters.update({key:df})
	writeExcel(getPathFileParameters(),dict_parameters)
def generateDfWrestlersCantWrestle(df_wrestlersCompromises,df_ourShows):
	#1 Take df_wrestlersCompromises
	#2 Take df_ourShows
	#3 Filter df_wrestlersCompromises by the DayOfWeek,Week,Month of the shows of our company
	keys = ['DayOfWeek','Week','Month']
	df_wrestlersCantWrestle=filterDfByAnotherByKeys(df_wrestlersCompromises,df_ourShows,keys)
	df_ourShowsEvery=df_ourShows.loc[(df_ourShows[keys[1]]=='Every')&(df_ourShows[keys[2]]=='Every')]
	df_wrestlersCompromisesEvery=df_wrestlersCompromises.loc[(df_wrestlersCompromises[keys[1]]=='Every')&(df_wrestlersCompromises[keys[2]]=='Every')]
	df_wrestlersCantWrestle=df_wrestlersCantWrestle.append(filterDfByAnotherByKeys(df_wrestlersCompromises,df_ourShowsEvery,[keys[0]]))
	
	df_wrestlersCantWrestle=df_wrestlersCantWrestle.append(filterDfByAnotherByKeys(df_wrestlersCompromisesEvery,df_ourShows,[keys[0]]))
	df_wrestlersCantWrestle=pd.merge(df_wrestlersCantWrestle,df_ourShows,on=['DayOfWeek','Week','Month'],  how='left')
	df_wrestlersCantWrestle=df_wrestlersCantWrestle.rename(columns={'Company_y': 'Company'})
	df_wrestlersCantWrestle=df_wrestlersCantWrestle[['WName', 'DayOfWeek', 'Week', 'Month', 'count',
       'Company', 'Show', 'ShowType']]
	print(f"df_wrestlersCantWrestle\n{df_wrestlersCantWrestle}\n{getLen(df_wrestlersCantWrestle)}\n{df_wrestlersCantWrestle[keys[0]].unique()}\n{df_wrestlersCantWrestle.columns}")
	df_wrestlersCantWrestle2=df_wrestlersCantWrestle.loc[(df_wrestlersCantWrestle['Company'].isna()),['WName', 'DayOfWeek', 'Week', 'Month', 'count']]
	df_wrestlersCantWrestle=df_wrestlersCantWrestle.drop(index=df_wrestlersCantWrestle2.index)
	df_wrestlersCantWrestle2=pd.merge(df_wrestlersCantWrestle2,df_ourShows,on=['DayOfWeek'],  how='left')
	df_wrestlersCantWrestle2=df_wrestlersCantWrestle2.rename(columns={'Week_x':'Week','Month_x':'Month'})
	print(f"df_wrestlersCantWrestle2\n{df_wrestlersCantWrestle2}\n{getLen(df_wrestlersCantWrestle2)}\n{df_wrestlersCantWrestle2[keys[0]].unique()}\n{df_wrestlersCantWrestle2.columns}")
	df_wrestlersCantWrestle=df_wrestlersCantWrestle.append(df_wrestlersCantWrestle2)
	print(f"df_wrestlersCantWrestle\n{df_wrestlersCantWrestle}\n{getLen(df_wrestlersCantWrestle)}\n{df_wrestlersCantWrestle[keys[0]].unique()}\n{df_wrestlersCantWrestle.columns}")
	df_wrestlersCantWrestle=df_wrestlersCantWrestle[['WName','Show','ShowType','Week', 'Month']]
	return df_wrestlersCantWrestle.drop_duplicates()
def filterDfByAnotherByKeys(df_1,df_2,keys):
	i_1 = df_1.set_index(keys).index
	i_2 = df_2.set_index(keys).index
	df_filtered=df_1[i_1.isin(i_2)]
	return df_filtered
def generateTriosBasedOnStables(df_stables,db_wrestlers):
	v_columns=generateTrioColumns()
	df_trios=pd.DataFrame([],columns=v_columns)
	v_w_columns=['WrestlerName','BestRating','Gender','Brand']
	#1. Get the members of the stables that are Wrestlers
	dict_stables={}
	for index_,value in df_stables.iterrows():
		v_wrestlers=[]
		for memberStableColumn in StableColumnsTable.LST_MEMBERS.value:
			df_result=db_wrestlers.loc[(value[memberStableColumn] is not None)&(db_wrestlers['WrestlerName']==(value[memberStableColumn]))]
			if(getLen(df_result)>0):
				v_wrestlers.append(df_result[v_w_columns].squeeze().tolist())
		#v_wrestlers = list(filter(None, v_wrestlers))
		#2. Count how many wrestlers you found.
		#2.1 if the cantWrestlers is less than 3 remove it or ommit that stables
		#2.2 else begin to generate the posible triosColumn
		if getLen(v_wrestlers)>2:
			dict_stables.update({value[StableColumnsTable.NAME.value]:v_wrestlers})
	#2.2.1 generate the combinations for the members of the stables
	for key in dict_stables.keys():
		v_wrestlers=dict_stables.get(key)
		lst_trios = list(combinations(v_wrestlers, 3))
		count=1
		for trio in lst_trios:
			v_trios=[]
			#2.2.2 Generate a Name for the Trio plus a number based in the amount of trios generated by Stable
			v_trios.append(str(key)+" "+str(count))
			for members in trio:
				v_trios.extend(members)
			best_rating=calculateBestRatingForTrios(v_trios)
			final_gender=calculateGenderForTrios(v_trios)
			final_brand=calculateBrandForTrios(v_trios)
			v_trios.append(best_rating)
			v_trios.append(final_gender)
			v_trios.append(final_brand)
			v_trios.append(1)
			count=count+1
			a_series = pd.Series(v_trios, index = v_columns)
			df_trios=df_trios.append(a_series, ignore_index=True)
	return df_trios
def generateTrioColumns():
    v_columns=[]
    for triosColumn in TriosColumns:
        if type(triosColumn.value) is tuple:
            v_columns.extend(triosColumn.value)
        else:
            v_columns.append(triosColumn.value)
    return v_columns
def calculateBestRatingForTrios(v_trios):
    bestRaiting1=v_trios[2]
    bestRaiting2=v_trios[6]
    bestRaiting3=v_trios[10]
    best_rating=bestRaiting1+bestRaiting2+bestRaiting3
    best_rating=int(best_rating/3)
    utRemoveElementFromList(v_trios,bestRaiting1)
    utRemoveElementFromList(v_trios,bestRaiting2)
    utRemoveElementFromList(v_trios,bestRaiting3)
    return best_rating
def utRemoveElementFromList(list_,element):
    if list_.count(element)>0:
        list_.remove(element)
def calculateGenderForTrios(v_trios):
    gender1=v_trios[2]
    gender2=v_trios[5]
    gender3=v_trios[8]
    if (gender1==gender2) & (gender2==gender3):
        final_gender=gender1
    else:
        final_gender='Mix'
    utRemoveElementFromList(v_trios,gender1)
    utRemoveElementFromList(v_trios,gender2)
    utRemoveElementFromList(v_trios,gender3)
    return final_gender
def calculateBrandForTrios(v_trios):
    brand_1=v_trios[2]
    brand_2=v_trios[4]
    brand_3=v_trios[6]
    if brand_1==brand_2:
        if (brand_2==brand_3) | (brand_3=='None'):
            brand=brand_1
        else:
            brand=None
    elif brand_2==brand_3:
        if brand_1=='None':
            brand=brand_2
        else:
            brand=None
    elif brand_1==brand_3:
        if brand_2=='None':
            brand=brand_1
        else:
            brand=None
    utRemoveElementFromList(v_trios,brand_1)
    utRemoveElementFromList(v_trios,brand_2)
    utRemoveElementFromList(v_trios,brand_3)
    return brand
def writeWrestlingExcel(dict_data):
	xlsx_file = Path(readRouteFolderIfExist(), 'Roster.xlsx')
	writeExcel(xlsx_file,dict_data)
def writeStaffExcel(dict_staff):
    xlsx_file = Path(readRouteFolderIfExist(), 'Staff.xlsx')
    writeExcel(xlsx_file,dict_staff)
def writeMatchResumeExcel(dict_MatchResume):
    xlsx_file = Path(readRouteFolderIfExist(), 'MatchResumeExcel.xlsx')    
    writeExcel(xlsx_file,dict_MatchResume)
def writeChampionsExcel(dict_ActualChampions):
    xlsx_file = Path(readRouteFolderIfExist(), 'ActualChampions.xlsx')
    writeExcel(xlsx_file,dict_ActualChampions)
    print('writeChampionsExcel\n',dict_ActualChampions)
def writeChildCompanyWrestlersExcel(dict_childcompany_wrestlers):
	xlsx_file = Path(readRouteFolderIfExist(), 'ChildCompanyWrestlers.xlsx')
	writeExcel(xlsx_file,dict_childcompany_wrestlers)
def writeChildCompaniesExcel(dict_childcompanies):
    xlsx_file = Path(readRouteFolderIfExist(), 'ChildCompanies.xlsx')
    writeExcel(xlsx_file,dict_childcompanies)
if __name__ == '__main__':
    main()
    print('Done')