import openpyxl
import pandas as pd
import sys
from pathlib import Path
from Utility import debugging,writeExcel,saveDFObjectForTesting,saveObjectForTesting,readBasicConfigValuesJson,isSublistInList,filterListElementsByRegex,findingDuplicateItemsInList
from SetUp import readRouteFolderIfExist
import itertools
is_shuffle=False
xlsx_file = Path(readRouteFolderIfExist(), 'Roster.xlsx')
db_wrestlers=pd.read_excel(xlsx_file,None) #Retorna un OrderedDict pero escribirlo en el excel se ve más complicado.
df_singleW=db_wrestlers.get('Single')
db_femaleP=df_singleW.loc[df_singleW['Gender']=='Female']
db_maleP=df_singleW.loc[df_singleW['Gender']=='Male']
db_teamsP=db_wrestlers.get('Tag')
db_triosP=db_wrestlers.get('Trios')
xlsx_matches = Path(readRouteFolderIfExist(), 'Matches.xlsx')

xlsx_matchesResume =Path(readRouteFolderIfExist(), 'MatchResumeExcel.xlsx')
dict_matchesResume=pd.read_excel(xlsx_matchesResume,None)
db_matchesResume=dict_matchesResume.get("MatchResume")

def main():
	dict_matches=pd.read_excel(xlsx_matches,None)
	xlsx_file = Path(readRouteFolderIfExist(), 'Roster.xlsx')
	db_wrestlers=pd.read_excel(xlsx_file,None)
	global db_femaleP
	global db_maleP
	global db_teamsP
	global df_roster_divition
	global db_matchesResume
	read_best_performance_wrestlers_until_now()
	db_femaleP=sortWrestlers(db_femaleP)
	db_maleP=sortWrestlers(db_maleP)
	db_teamsP=sortTagTeams(db_teamsP)
	db_teamsP=db_teamsP.drop_duplicates(subset=list(db_teamsP.columns)[1:3])
	calcPopTagTeams(db_femaleP)    
	calcPopTagTeams(db_maleP)
	calcBestRatingTagTeams(db_maleP)
	calcBestRatingTagTeams(db_femaleP)
	calcGenderTagTeams(db_femaleP,db_maleP)
	calcBrandTagTeams(db_femaleP,db_maleP)
	calcWrestlerUID(db_maleP);
	calcWrestlerUID(db_femaleP);
	inactiveTagTeams(db_femaleP,db_maleP)
	TW=db_femaleP.size+db_maleP.size
	print(f'Proporcion M: {db_maleP.size/TW}')
	print(f'Proporcion F: {db_femaleP.size/TW}')
	dict_division={"Single":{},"Tag":{},"Trios":{}}
	print(f'Male')
	dict_single=dict_division.get("Single")
	dict_single.update({"Male":showDescribe(db_maleP)})
	#dict_division.update({"Single":{"Male":showDescribe(db_maleP)}})
	print(f'Female')
	#showDescribe(db_femaleP)
	dict_single.update({"Female":showDescribe(db_femaleP)})
	print(f'Tag')
	dict_teams=dict_division.get("Tag")
	for gender in ("Male","Female","Mix","All"):
		if gender=="All":
			db_teamsP_gender=db_teamsP
		else:
			db_teamsP_gender=db_teamsP.loc[(db_teamsP["Gender"]==gender)]
		dict_teams.update({gender:showDescribe(db_teamsP_gender)})
	dict_division.update(dict_teams)
	df_singleW=joinFemaleAndMaleWrestlers(db_femaleP,db_maleP)
	dict_single.update({"All":showDescribe(df_singleW)})
	dict_division.update(dict_single)
	print(f'dict_division\n{dict_division}')
	db_wrestlers.update({"Single":df_singleW})
	db_wrestlers.update({"Tag":db_teamsP})
	db_wrestlers.update({"Trios":db_triosP})
	xlsx_file = Path(readRouteFolderIfExist(), 'Roster.xlsx')
	writeExcel(xlsx_file,db_wrestlers)
	#writeWrestlingExcel(db_femaleP,db_maleP,db_teamsP,db_triosP)
	printTypeAndContent(len(db_maleP))
	df_cantPBMT=participantByMatchType(db_parameters.get('ConfMatchType'))
	df_cantMatByShow=db_parameters.get('RosterDivitionShows')
	df_roster_divition=db_parameters.get('RosterDivition')
	df_roster_divition=generateRosterDivition(df_roster_divition,dict_division)
	df_roster_divition=generateCantWrestlersByDivition(df_roster_divition,db_wrestlers)
	print(f'df_roster_divition\n{df_roster_divition}')
	db_parameters.update({'RosterDivition':df_roster_divition})
	xlsx_file2 = Path(readRouteFolderIfExist(), 'Param.xlsx')#ToDo: JuanK Generar método para esto y no duplicar líneas
	writeExcel(xlsx_file2,db_parameters)
	db_wrestlers=generateRosterAvaliableForTheWeek(db_wrestlers)
	list_shows_preparar=generarListaDeShowsAGenerar(db_parameters)
	df_act_roster_divition=generateCantWrestlersByDivition(df_roster_divition.copy(),db_wrestlers)
	data_12 = df_roster_divition.merge(df_act_roster_divition,# Merge DataFrames with indicator
					  indicator = True,
					  how = 'outer')
	data_12_diff = data_12.loc[lambda x : x['_merge'] != 'both']  # Remove shared rows
	#if len(data_12_diff)==0:
		#raise Exception(f'JK Error-Both roster divition are the same')
	updateTheMatchesAlreadyScheduled(dict_matches)
	#Considere include Trios matches
	saveDFObjectForTesting("df_act_roster_divition",df_act_roster_divition)
	saveDFObjectForTesting("df_cantMatByShow",df_cantMatByShow)
	saveObjectForTesting("db_parameters",db_parameters)
	df_cantMatByShow=generarCantidadDeLuchasParaLaSemana(df_cantMatByShow,df_act_roster_divition,db_parameters)
	df_participantsForMatchesShows=generateParticipantsForMatchesShows(list_shows_preparar,df_cantMatByShow,df_cantPBMT)
	#Generate Matches for shows
	#1- Get list of shows list_shows_preparar
	saveObjectForTesting("list_shows_preparar",list_shows_preparar)
	#2- Get Participants for matches shows
	saveDFObjectForTesting("df_participantsForMatchesShows",df_participantsForMatchesShows)
	#3- Get the Roster
	saveObjectForTesting("db_wrestlers",db_wrestlers)
	#4- Get df_roster_divition
	saveDFObjectForTesting("df_roster_divition",df_roster_divition)
	saveObjectForTesting("dict_matches",dict_matches)
	dict_matches=generateMatchesForShows(list_shows_preparar,df_participantsForMatchesShows,db_wrestlers,df_roster_divition,is_shuffle,dict_matches)
	#df_matches_tnt=generateMatchesForShows(list_shows_preparar,df_cantMatByShow,df_cantPBMT)
	dict_matches=orderMatchesByExpectedRaitingAndShow(dict_matches)
	db_maleP=limpiarBaseDeCaraALuchasYaPactadas(db_maleP,"Male",dict_matches)
	db_femaleP=limpiarBaseDeCaraALuchasYaPactadas(db_femaleP,"Female",dict_matches)
	db_teamsP=limpiarBaseDeCaraALuchasYaPactadas(db_teamsP,"Tag",dict_matches)
	printTypeAndContent(len(db_maleP))
	writeWrestlingExcelRest(db_femaleP,db_maleP,db_teamsP,db_triosP)
	writeMatchesExcel(dict_matches)
def read_best_performance_wrestlers_until_now():
    df_best_wrestlers=read_best_wrestlers_until_now(dict_matches)
    write_xlsx_file(df_best_wrestlers,'BestAllTimes.xlsx')
def read_best_wrestlers_until_now(dict_matches):
    df_best_wrestlers=pd.DataFrame([])
    #sinceWeek='202601W1'
    sinceWeek=getSinceWeek()
    for key in dict_matches.keys():
        df=dict_matches[key]
        if len(sinceWeek)>0:
            df=df[df['Week']>=sinceWeek]##-202601W1
        df=df.dropna(subset=['Best'])
        df=df.groupby('Best')
        df=df.size().reset_index(name='counts')
        df_best_wrestlers=df_best_wrestlers.append(df, ignore_index=True)
    df_best_wrestlers=df_best_wrestlers.groupby(['Best'])['counts'].sum().reset_index(name='counts')
    df_best_wrestlers=df_best_wrestlers.sort_values(by=['Best', 'counts'])
    return df_best_wrestlers
def getSinceWeek():
    df_general=db_parameters.get('General')
    sinceWeek=df_general['SinceWeek'].head().item()
    return sinceWeek
def write_xlsx_file(dict_ppv,file_name):
    xlsx_file = Path(readRouteFolderIfExist(), file_name)
    if isinstance(dict_ppv,dict):
        for key in dict_ppv.keys():
            if isinstance(dict_ppv[key],dict):
                dict_ppv2=dict_ppv[key]
                xlsx_file = Path(readRouteFolderIfExist(), key+file_name)
                with pd.ExcelWriter(xlsx_file, engine="openpyxl", mode='w') as writer:
                    for key2 in dict_ppv2.keys():
                        dict_ppv2[key2].to_excel(writer,index=False,sheet_name=key2)
            else:
                with pd.ExcelWriter(xlsx_file, engine="openpyxl", mode='w') as writer:
                    dict_ppv[key].to_excel(writer,index=False,sheet_name=key)
    else:
        with pd.ExcelWriter(xlsx_file, engine="openpyxl", mode='w') as writer:
            dict_ppv.to_excel(writer,index=False,sheet_name='Key')
def sortWrestlers(wrestlers):
    return wrestlers.sort_values(by=['Active','BestRating','Popularity'],ascending=False)
def sortTagTeams(tag_teams):
	v_columns=tag_teams.columns
	sor_tag_columns=['Type','Active','BestRating','Popularity','EXP']
	if isSublistInList(sor_tag_columns,v_columns):
		return tag_teams.sort_values(by=['Type','Active','BestRating','Popularity','EXP'],ascending=False)
	else:
		return tag_teams.sort_values(by=['Active','BestRating'],ascending=False)
def calcPopTagTeams(db_wrestlers):
    rowfind=db_wrestlers.loc[db_wrestlers['WrestlerName'].isin(db_teamsP.get('W1'))|db_wrestlers['WrestlerName'].
                             isin(db_teamsP.get('W2'))]
    tag_name1=db_teamsP.loc[db_teamsP['W1'].isin(rowfind.get('WrestlerName')),['W1','Tag Name']]
    tag_name2=db_teamsP.loc[db_teamsP['W2'].isin(rowfind.get('WrestlerName')),['W2','Tag Name']]
    tag_name=tag_name2.rename(columns={'W2': 'WrestlerName'}).append(tag_name1.rename(columns={'W1': 'WrestlerName'}),
                                                                 ignore_index=True)
    rowfind=rowfind.merge(tag_name)
    rowfind['Popularity']=rowfind['Popularity'].astype(float)
    pop=rowfind.groupby('Tag Name')['Popularity'].mean()
    for key in pop.keys():
        db_teamsP.loc[db_teamsP['Tag Name']==key,['Popularity']]=pop[key]
def calcBestRatingTagTeams(db_wrestlers):
    rowfind=db_wrestlers.loc[db_wrestlers['WrestlerName'].isin(db_teamsP.get('W1'))|db_wrestlers['WrestlerName'].
                             isin(db_teamsP.get('W2'))]
    tag_name1=db_teamsP.loc[db_teamsP['W1'].isin(rowfind.get('WrestlerName')),['W1','Tag Name']]
    tag_name2=db_teamsP.loc[db_teamsP['W2'].isin(rowfind.get('WrestlerName')),['W2','Tag Name']]
    tag_name=tag_name2.rename(columns={'W2': 'WrestlerName'}).append(tag_name1.rename(columns={'W1': 'WrestlerName'}),
                                                                 ignore_index=True)
    rowfind=rowfind.merge(tag_name)
    rowfind['BestRating']=rowfind['BestRating'].astype(float)
    pop=rowfind.groupby('Tag Name')['BestRating'].mean()
    for key in pop.keys():
        db_teamsP.loc[db_teamsP['Tag Name']==key,['BestRating']]=pop[key]  
def calcGenderTagTeams(db_femaleP,db_maleP):
    import numpy as np
    db_teamsP['Gender']=None
    db_teamsP.loc[(db_teamsP['W1']
                  .isin(db_femaleP.get('WrestlerName'))
                  &db_teamsP['W2']
                  .isin(db_femaleP.get('WrestlerName'))),'Gender']='Female'
    db_teamsP.loc[(db_teamsP['W1']
                  .isin(db_maleP.get('WrestlerName'))
                  &db_teamsP['W2']
                  .isin(db_maleP.get('WrestlerName'))),'Gender']='Male'
    db_teamsP.loc[(db_teamsP['Gender'].isnull()),'Gender']='Mix'
def calcBrandTagTeams(db_femaleP,db_maleP):
    set_brand=db_femaleP['Brand'].unique()
    for brand in set_brand:
            brand_female=db_femaleP.loc[db_femaleP['Brand']==brand]
            brand_male=db_maleP.loc[db_maleP['Brand']==brand]
            db_teamsP.loc[(db_teamsP['W1']
                  .isin(brand_female.get('WrestlerName'))
                  &db_teamsP['W2']
                  .isin(brand_female.get('WrestlerName'))),'Brand']=brand
            db_teamsP.loc[(db_teamsP['W1']
                  .isin(brand_male.get('WrestlerName'))
                  &db_teamsP['W2']
                  .isin(brand_male.get('WrestlerName'))),'Brand']=brand
            db_teamsP.loc[(db_teamsP['W1']
                  .isin(brand_female.get('WrestlerName'))
                  &db_teamsP['W2']
                  .isin(brand_male.get('WrestlerName'))),'Brand']=brand
            db_teamsP.loc[(db_teamsP['W1']
                  .isin(brand_male.get('WrestlerName'))
                  &db_teamsP['W2']
                  .isin(brand_female.get('WrestlerName'))),'Brand']=brand
def calcWrestlerUID(db_wrestlers):
    for wrestler_name in db_wrestlers['WrestlerName']:
        db_teamsP.loc[db_teamsP['W1']==wrestler_name,['WUID1']]=db_wrestlers.loc[db_wrestlers['WrestlerName']==wrestler_name,['UID']]['UID'].item()
        db_teamsP.loc[db_teamsP['W2']==wrestler_name,['WUID2']]=db_wrestlers.loc[db_wrestlers['WrestlerName']==wrestler_name,['UID']]['UID'].item()
    #db_teamsP['WUID1']=db_teamsP['W1'].map(lambda x: getWrestlerUID(x, db_wrestlers))
    #db_teamsP['WUID2']=db_teamsP['W2'].map(lambda x: getWrestlerUID(x, db_wrestlers))
def getWrestlerUID(wrestler_name,db_wrestlers):
    finded=db_wrestlers.loc[db_wrestlers['WrestlerName']==wrestler_name,['UID']]
    if not finded.empty:
        return finded['UID'].item()
def inactiveTagTeams(db_femaleP,db_maleP):
    db_femaleP=db_femaleP.loc[(db_femaleP['Active'].isin([1]))]
    db_maleP=db_maleP.loc[(db_maleP['Active'].isin([1]))]
    db_teamsP['Active']=0
    db_teamsP.loc[(db_teamsP['W1']
                  .isin(db_femaleP.get('WrestlerName'))
                  &(db_teamsP['W2']
                  .isin(db_femaleP.get('WrestlerName')))),'Active']=1
    db_teamsP.loc[(db_teamsP['W1']
                  .isin(db_maleP.get('WrestlerName'))
                  &(db_teamsP['W2']
                  .isin(db_maleP.get('WrestlerName')))),'Active']=1
    db_teamsP.loc[(db_teamsP['W1']
                  .isin(db_maleP.get('WrestlerName'))
                  &(db_teamsP['W2']
                  .isin(db_femaleP.get('WrestlerName')))),'Active']=1
    db_teamsP.loc[(db_teamsP['W1']
                  .isin(db_femaleP.get('WrestlerName'))
                  &(db_teamsP['W2']
                  .isin(db_maleP.get('WrestlerName')))),'Active']=1
def showDescribe(db_maleP):
    perc =[1/3, 1/3*2, 1/3*3]
    media = db_maleP["BestRating"].mean()
    mediana = db_maleP["BestRating"].median()
    moda = db_maleP["BestRating"].mode()
    p1 = db_maleP[db_maleP['Active']==1]["BestRating"].quantile(1/3)
    p2 = db_maleP[db_maleP['Active']==1]["BestRating"].quantile(1/3*2)
    p3 = db_maleP[db_maleP['Active']==1]["BestRating"].quantile(1/3*3)
    print(f'p1,p2,p3:\n{p1,p2,p3}')
    dict_describebybrand={}
    dict_describebybrand.update({"All":{"DarkCard":p1,"MidCard":p2,"MainCard":p3}})
    set_brand=db_maleP['Brand'].dropna().unique()
    return showDescribeByBrand(db_maleP,set_brand)
def showDescribeByBrand(db_maleP,set_brand):
    dict_describebybrand={}
    for brand in set_brand:
        print(f'Brand\t{brand}')
        brand_maleP=db_maleP.loc[db_maleP['Brand']==brand]
        perc =[1/3, 1/3*2, 1/3*3]
        media = brand_maleP["BestRating"].mean()
        mediana = brand_maleP["BestRating"].median()
        moda = brand_maleP["BestRating"].mode()
        p1 = brand_maleP[brand_maleP['Active']==1]["BestRating"].quantile(1/3)
        p2 = brand_maleP[brand_maleP['Active']==1]["BestRating"].quantile(1/3*2)
        p3 = brand_maleP[brand_maleP['Active']==1]["BestRating"].quantile(1/3*3)
        print(f'p1,p2,p3:\n{p1,p2,p3}')
        dict_describebybrand.update({brand:{"DarkCard":p1,"MidCard":p2,"MainCard":p3}})
    return dict_describebybrand
def writeWrestlingExcel(db_femaleP,db_maleP,db_teamsP,db_triosP):
	df_singleW=joinFemaleAndMaleWrestlers(db_femaleP,db_maleP)
	with pd.ExcelWriter(xlsx_file, engine="openpyxl", mode='w') as writer:
		df_singleW.to_excel(writer,index=False,sheet_name='Single')
		db_teamsP.to_excel(writer,index=False,sheet_name='Tag')
		db_triosP.to_excel(writer,index=False,sheet_name='Trios')
def joinFemaleAndMaleWrestlers(db_femaleP,db_maleP):
	df_singleW=db_femaleP.append(db_maleP)
	return df_singleW
def writeWrestlingExcelRest(db_femaleP,db_maleP,db_teamsP,db_triosP):
	df_singleW=joinFemaleAndMaleWrestlers(db_femaleP,db_maleP)
	with pd.ExcelWriter(Path(readRouteFolderIfExist(), 'WrestlingRest.xlsx'), engine="openpyxl", mode='w') as writer:
		df_singleW.to_excel(writer,index=False,sheet_name='Single')
		db_teamsP.to_excel(writer,index=False,sheet_name='Tag')
		db_triosP.to_excel(writer,index=False,sheet_name='Trios')
def generateRosterAvaliableForTheWeek(dict_wrestlers):
	df_single=dict_wrestlers.get("Single")
	df_single=inactiveLoosers(df_single)
	db_inactive_single=df_single.loc[df_single.Active==0]
	for key in dict_wrestlers.keys():
		if key!="Single":
			df_group=dict_wrestlers.get(key)
			df_group=df_group.loc[df_group.Active==1]
			df_group=removeGroupsByWrestlers(db_inactive_single,df_group)
			dict_wrestlers.update({key:df_group})
	df_single=df_single.loc[df_single.Active==1]
	dict_wrestlers.update({"Single":df_single})
	return dict_wrestlers
def removeGroupsByWrestlers(db_inactive_single,df_group):
	#df.loc[:, df.columns.str.startswith('alp')]
	list_w=df_group.loc[:,df_group.columns.str.startswith('W')].columns
	for w in list_w:
		if 'W' in w and 'WUID' not in w:
			df_groupFound=df_group.loc[df_group[w].isin(db_inactive_single.get('WrestlerName'))]
			if len(df_groupFound)>0:
				df_group=df_group.drop(index=df_groupFound.index)
	return df_group
def inactiveLoosers(df_single):
    list_db=[df_single]
    for key in dict_matches.keys():
        for db_wrestlers in list_db:
            df=dict_matches[key]
            #db_teamsP['W1'].isin(rowfind.get('WrestlerName')),['W1','Tag Name']
            week=obtainWeekOfGame()
            month=str(week).split('W')[0]
            v_columns=df.columns
            for col_name in v_columns:
                if 'Defeated' in col_name:
                    #print(f'LO:df.get(col_name):\n{df.get(col_name)}')
                    df=df[df['Week'].str.contains(month)]
                    db_findit=db_wrestlers['WrestlerName'].isin(df.get(col_name))
                    #print(f'db_findit:\n{db_findit}')
                    db_wrestlers.loc[db_findit,['Active']]=0                    
                    #print(f'ChangeIt:\n{db_wrestlers}')
    return df_single
def obtainWeekOfGame():
	db_parameters=readParameters()
	v_df_calendar=db_parameters.get('Calendar')
	v_week=v_df_calendar.tail(1).Week.tail(1).item()    
	return v_week
def generarListaDeShowsAGenerar(dict_parameters):
    df_shows=getDFTvShowsActive(dict_parameters)
    df_shows=df_shows['Show']
    print(f'df_shows\n{df_shows}')
    #for key in dict_matches.keys():
    #    df=dict_matches[key]
    #    #db_teamsP['W1'].isin(rowfind.get('WrestlerName')),['W1','Tag Name']
    #    df=df.loc[(df['Week']==obtainWeekOfGame())]
    #    #print(f'df_shows.items():\n{df_shows}')
    #    #.loc[(df.Show.isin(df_shows)),['Tag Name']]
    #    shows_planed=df.loc[(df.Show.isin(df_shows)),['Show']]
    #    #print(df_shows.drop(df_shows[df_shows.isin(df.Show)].index))
    #    return df_shows.drop(df_shows[df_shows.isin(df.Show)].index)
    return df_shows
def getDFTvShowsActive(dict_parameters):
    df_shows=dict_parameters.get("Shows")
    df_shows=df_shows.loc[(df_shows['ShowType']=="TV")]
    return df_shows
def participantByMatchType(dfConfMatchType):
    import random
    dataFrame=pd.DataFrame([])
    for typeMatch in dfConfMatchType.index:
        v_min=dfConfMatchType['Min'][typeMatch]
        v_max=dfConfMatchType['Max'][typeMatch]
        v_maxP=dfConfMatchType['MinP'][typeMatch]
        total=(v_max-v_min+1)
        dif=100
        cEspacios=dif/total
        df_active=pd.DataFrame(0,index=range(v_min,v_max+1),columns=['#'])
        for i in range(total):
            if i<total-1:
                ae=int(cEspacios*v_maxP)
            else:
                ae=cEspacios
            df_active.loc[(v_max-i)]=ae
            dif=dif-ae
            div=(total-(i+1))
            if div>0:
                cEspacios=dif/(div)
        d = pd.DataFrame(0, index=range(1,101),columns=[dfConfMatchType['Match Type'][typeMatch]])
        avalaibleP=list(range(1,101))    
        #print(dfConfMatchType['Match Type'][typeMatch])
        for ind in df_active.index:
            op=int(df_active.loc[ind][0])
            i=0
            while i<op:        
                random_n=random.randint(0,len(avalaibleP)-1)
                if d.loc[avalaibleP[random_n]][0]==0:                
                    d.loc[avalaibleP[random_n]][0]=ind
                    avalaibleP.pop(random_n)
                else:
                    i=i-1
                i=i+1
        if dataFrame.empty:
            #print(f'empty: {d}')
            dataFrame=d
        else:
            dfConfMatchType['Match Type'][typeMatch]
            dataFrame=dataFrame.assign(New_Column=d[dfConfMatchType['Match Type'][typeMatch]])
            dataFrame=dataFrame.rename(columns={'New_Column': dfConfMatchType['Match Type'][typeMatch]})
    #print(dataFrame)
    return dataFrame
def generateRosterDivition(df_roster_divition,dict_division):
	key_divition='Divition'
	setType=set(df_roster_divition['Type'])
	setDivition=set(df_roster_divition[key_divition])
	flag=True
	if len(setDivition)==0:
		dict_basic_values=readBasicConfigValuesJson()
		setDivition=set(dict_basic_values[key_divition])
	if len(setType)==0:
		setType=set(db_wrestlers.keys())
		flag=False
	if flag:
		for v_type in setType:
			dict_gender=dict_division.get(v_type)
			if type(dict_gender) is not dict:
				debugging(dict_division)
			for gender in dict_gender.keys():
				last_value=0
				dict_brand=dict_gender[gender]
				for brand in dict_brand.keys():
					dict_div=dict_brand.get(brand)
					for divition in dict_div.keys():
						df_roster_divition.loc[(df_roster_divition["Type"]==v_type) & (df_roster_divition["Brand"]==brand)&(df_roster_divition["Gender"]==gender)
												   &(df_roster_divition["Divition"]==divition)
												   ,["MinPopularity","MaxPopularity"]]=last_value,dict_div.get(divition)
						last_value=dict_div.get(divition)
	else:
		elementsToCombine=[]
		#elementsToCombine.append(setDivition)
		elementsToCombine.append(setType)
		elementsToCombine.append(("Male","Female","Mix","All"))
		result=list(itertools.product(*elementsToCombine))
		for combination in result:
			v_type=combination[0]
			v_gender=combination[1]
			dict_type=dict_division.get(v_type)
			dict_gender=dict_type.get(v_gender)
			if dict_gender is None:
				continue
			for v_brand in dict_gender.keys():
				dict_brand_div=dict_gender.get(v_brand)
				v_min_popularity=0
				for v_divition in dict_brand_div.keys():
					v_max_popularity=dict_brand_div.get(v_divition)
					v_roster_divition=[]
					v_roster_divition.append(v_divition)
					v_roster_divition.append(0)
					v_roster_divition.append(v_min_popularity)
					v_roster_divition.append(v_max_popularity)
					v_roster_divition.append(v_type)
					v_roster_divition.append(v_gender)
					v_roster_divition.append(v_brand)
					df_roster_divition.loc[len(df_roster_divition)] = v_roster_divition
					v_min_popularity=v_max_popularity
	return df_roster_divition
def generateCantWrestlersByDivition(df_roster_divition,dict_wrestlers):
	c_divition="Divition"
	c_Type="Type"
	c_gender="Gender"
	c_Brand="Brand"
	c_MinPopularity="MinPopularity"
	c_MaxPopularity="MaxPopularity"
	for key,data in df_roster_divition[[c_divition,c_Type,c_gender,c_Brand,c_MinPopularity,c_MaxPopularity]].iterrows():
		v_divition=data.loc[c_divition]
		v_Type=data.loc[c_Type]
		v_Brand=data.loc[c_Brand]
		v_gender=data.loc[c_gender]
		v_MinPopularity=data.loc[c_MinPopularity]
		v_MaxPopularity=data.loc[c_MaxPopularity]
		df_type_roster=dict_wrestlers.get(v_Type)
		if df_type_roster is None:
			continue
		cant=getCantWrestlersByFilter(df_type_roster.loc[(df_type_roster["Gender"]==v_gender)|("All"==v_gender)],v_MinPopularity,v_MaxPopularity,v_Brand)
		print(f"cant:{cant}\v_Type:{v_Type}\ndata:{data}")
		df_roster_divition.loc[(df_roster_divition["Divition"]==v_divition)
						   &(df_roster_divition["Type"]==v_Type)
						   &(df_roster_divition["Brand"]==v_Brand)
						   &(df_roster_divition[c_gender]==v_gender),['Cant']]=cant
		#raise Exception(f'df_roster_divition\n{df_roster_divition}\nv_divition,cant,v_Brand,v_Type\n{v_divition,cant,v_Brand,v_Type}\nv_MinPopularity,v_MaxPopularity\n{v_MinPopularity,v_MaxPopularity}')
	return df_roster_divition
def getCantWrestlersByFilter(db,v_MinPopularity,v_MaxPopularity,v_Brand):
    db_bk=db[(db["BestRating"]>v_MinPopularity)&(db["BestRating"]<=v_MaxPopularity)
                &((db["Brand"]==v_Brand)|(v_Brand=='None'))&(db["Active"]==1)]
    cant=len(db_bk.index)
    #if (v_Brand=='Dynamite'):
    #print(f'v_MinPopularity,v_MaxPopularity,v_Brand,cant\n{v_MinPopularity,v_MaxPopularity,v_Brand,cant}\ndb_bk\n{db_bk}')
        #raise Exception
    return cant
#1- Leer los combates ya pactados que no tengan la columna RosterDivision diligenciada
#2- Calcular el RosterDivision para esas luchas
#3- Actualizar la fila en el diccionario
#4- Cuantificar cuantas luchas por show y por RosterDivision ya fueron pactadas
#4.1- Generar el resultado con la misma estructura de df_cantMatByShow
#5- Restar lo cuantificado a df_cantMatByShow
def updateTheMatchesAlreadyScheduled(dict_matches):
    for key in dict_matches.keys():
        df_matches=dict_matches[key]
        week=obtainWeekOfGame()
        df_matches=df_matches.loc[((df_matches['Week']==week) & 
                                   (pd.isna(df_matches['RosterDivision']))
                                  )]
        v_columns=df_matches.columns
        df_matches=calcularRosterDivision(df_matches,key)
        dict_matches[key].update(df_matches)
        df_matches=dict_matches[key]
def generarCantidadDeLuchasParaLaSemana(df_cantMatByShow,df_rosterDivition,dict_parameters):
    #Use groupBy sum
    #total=sum(df_roster_divition.loc[(df_roster_divition["Brand"]=="TNT"),['Cant']]['Cant'])
    df_distribution=calculateDistributionForFights(df_rosterDivition,dict_parameters)
    df_cantMatByShow=tansform(df_distribution,df_cantMatByShow)    
        #df_cantMatByShow[key][v_Type]=v_cant
    return df_cantMatByShow
def calculateDistributionForFights(df_rosterDivition,dict_parameters):
	#Brand is different to Show, if I have wrestlers with None brand this means the Wrestler can fight in any show
	list_shows_preparar=generarListaDeShowsAGenerar(dict_parameters)
	list_column_names=['TV Show', 'TCant', 'Divition', 'Type', 'Cant', 'Proportion',
	   'IntProportion', 'Proportion-IntProportion', 'Val']
	df_rosterDivitionShows=pd.DataFrame([],columns=list_column_names)
	for show in list_shows_preparar:
		df_sub=filterRosterDivitionByBrand(df_rosterDivition,show)
		while True:
			total=df_sub.loc[df_sub['Gender']!='All'].groupby(['Brand','Divition'])['Cant'].sum().reset_index() #Suma todas las cantidades por brand, pero tenemos un genero all que ya las engloba
			if len(total)==0 or total['Cant'].head(1).item()==0:
				df_sub=filterRosterDivitionByBrand(df_rosterDivition)
			else:
				break
			
		df_rosterDivitionShows=df_rosterDivitionShows.append(generateRosterDivitionShows(total,df_sub,show,dict_parameters))
	return df_rosterDivitionShows
def tansform(df_distribution,df_cantMatByShow):
	list_columns=['TV Show','Divition','Type','Gender','IntProportion']
	isNone=False
	if df_cantMatByShow is None:
		df_cantMatByShow = pd.DataFrame([],columns=list_columns)
		isNone=True
	for key,data in df_distribution[list_columns].iterrows():
		v_tvShow=data[list_columns[0]]
		v_divition=data[list_columns[1]]
		v_type=data[list_columns[2]]
		v_gender=data[list_columns[3]]
		v_IntProportion=data[list_columns[4]]
		if isNone:
			list_=[v_tvShow,v_divition,v_type,v_gender,v_IntProportion]
			df_cantMatByShow.loc[len(df_cantMatByShow)]=list_
		else:
			df_cantMatByShow.loc[((df_cantMatByShow['Show']==v_tvShow))&(df_cantMatByShow['Divition']==v_divition)&(df_cantMatByShow['Type']==v_type)&(df_cantMatByShow['Gender']==v_gender),['IntProportion']]=v_IntProportion
	printTypeAndContent(df_cantMatByShow)
	return df_cantMatByShow
def generateParticipantsForMatchesShows(list_shows_preparar,df_cantMatByShow,df_cantPBMT):
	#Generate Matches for shows
	#1-Get the list of shows
	list_shows_preparar
	#2-Get the amount of matches by type and gender by show
	df_cantMatByShow
	#3-Get the amount of participants by type with all its possibilities
	df_cantPBMT
	#4-Iterate the list of shows
	df_matchesToGenerate=pd.DataFrame([],columns=["Tv Show","Divition","Type", "Gender","Participants"])
	for show in list_shows_preparar:
	#4.1- Get the amount of matches by type and gender by show
		df_cantMathByShow_=df_cantMatByShow.loc[(df_cantMatByShow['TV Show']==show)]
	#4.2- Take the amount of matches by the type
		df_amountOfMatchesByType=df_cantMathByShow_.groupby(['Type','Divition','Gender'])['IntProportion'].sum().reset_index(name='IntProportion')
	#4.3- Get the amount of participants for the amount of matches by type
		for key,data in df_amountOfMatchesByType.iterrows():
			amountOfMatches=data['IntProportion']
			import random
			sr_cantParByType=df_cantPBMT[data['Type']]
			len_cantParticipantsByType=(len(sr_cantParByType))
			for count in range(0,amountOfMatches):
				random_p=random.randint(1,len_cantParticipantsByType-1)
				cant_participants=sr_cantParByType[random_p]
				list_elementsCantMatchByShow=[]
				list_elementsCantMatchByShow.append(show)
				list_elementsCantMatchByShow.append(data['Divition'])
				list_elementsCantMatchByShow.append(data['Type'])
				list_elementsCantMatchByShow.append(data['Gender'])
				list_elementsCantMatchByShow.append(cant_participants)
				df_matchesToGenerate.loc[len(df_matchesToGenerate)]=list_elementsCantMatchByShow
	#4.4- Return a DF with the following structure [Tv Show,Divition,Type, Gender,Participants]
	return df_matchesToGenerate
def generateMatchesForShows(list_shows_preparar,df_participantsForMatchesShows,db_wrestlers,df_roster_divition,is_shuffle,dict_matches):
	#4- Iterate each show
	for show in list_shows_preparar:
	#4.1- Take the rows for the show of Get Participants for matches shows
		df_participantsForMatchesShows_=df_participantsForMatchesShows.loc[df_participantsForMatchesShows["Tv Show"]==show]
		for index, data in df_participantsForMatchesShows_.iterrows():
	#4.2- Take the Divition, Type, Gender, Participants
			v_divition=data["Divition"]
			v_type=data["Type"]
			v_gender=data["Gender"]
			v_participants=data["Participants"]
	#4.3- Take the min and max popularity by Divition
			df_min_max_=df_roster_divition.loc[(df_roster_divition['Divition']==v_divition)&(df_roster_divition['Gender']==v_gender)&(df_roster_divition["Type"]==v_type),['Brand','MinPopularity','MaxPopularity']]
			
	#4.4- Take the Wrestlers by Type Roster, gender and divition (BestRaiting) and allowed to work for that show db_wrestlers,str_type_match,df_rosterDivition
			df_wrestlersByType=db_wrestlers.get(v_type)
			str_type_match=v_type+str(v_participants)
			df_wrestlersByType=df_wrestlersByType.loc[(df_wrestlersByType['Gender']==v_gender)|(v_gender=='All')]
			dict_parameters=readParameters()
			df_tvShows=getDfTvShowByShow(show,dict_parameters)
			v_TVShowType=df_tvShows['TVShowType'].head(1).item()
			if str(v_TVShowType).__contains__("B"):
				if v_type=='Single':
					df_wrestlersByType=generateRosterForDark(df_wrestlersByType)
				else:
					df_single=db_wrestlers.get("Single")
					df_single=generateRosterForDark(df_single)
					df_wrestlersByType=removeGroupsByWrestlers(df_single,df_wrestlersByType)
			if len(df_wrestlersByType.values)==0:
				continue
			df_wrestlerstoFight=generateWrestlerToFight(df_wrestlersByType,str_type_match,df_min_max_,is_shuffle,dict_matches)
			df_wrestlerselected=df_wrestlerstoFight.head(v_participants)
			type_match=str_type_match
			df_match=generateMatch(str_type_match,show,type_match,v_divition,df_wrestlerselected)
			if df_match.empty==False:
				dic_key=str(str_type_match);
				v_dic_k=list(dict_matches.keys())
				if dic_key in v_dic_k:
					dict_matches[dic_key]=dict_matches[dic_key].append(df_match, ignore_index=True)
				else:
					dict_matches[dic_key]=df_match
	#4.5- Take the amount of wrestlers for the match
	#4.7- return the dict matches
	return dict_matches
def orderMatchesByExpectedRaitingAndShow(dict_matches):
	for key in dict_matches.keys():
		df_=dict_matches.get(key)
		df_=df_.sort_values(by=['Week','ExpectedRaiting','Show'],ascending=False)
		dict_matches.update({key:df_})
	return dict_matches
def filterRosterDivitionByShow(df_rosterDivition,show):
	return df_rosterDivition.loc[(df_rosterDivition['Show']==show)]
def filterRosterDivitionByBrand(df_rosterDivition,brand="None"):
    return df_rosterDivition.loc[(df_rosterDivition['Brand']==brand)]
def generateRosterDivitionShows(total,df_roster_divition,show,dict_parameters):
	total_div_type=df_roster_divition.loc[df_roster_divition['Gender']!='All'].groupby(['Brand','Divition','Type','Gender'])['Cant'].sum().reset_index()
	df_rosterDivitionShows=pd.merge(total.rename(columns={'Cant':'TCant'}),total_div_type,on=['Brand','Divition'],  how='right')
	c_total_matches=getMaxCantMachesByShow(show,dict_parameters)
	dict_divitionOfTypeShow=getDictDistributionMatchesByDivitionAndTypeTvShow(show,dict_parameters,c_total_matches)
	df_rosterDivitionShows['Proportion']=0
	df_rosterDivitionShows['TCant']=df_rosterDivitionShows['TCant'].astype(int)
	df_rosterDivitionShows['Cant']=df_rosterDivitionShows['Cant'].astype(int)
	df_rester_div_intergender=df_roster_divition.loc[df_roster_divition['Gender']=='All']
	df_rester_div_intergender['Proportion']=0
	df_rester_div_intergender['TCant']=df_rester_div_intergender['Cant']
	for divition in dict_divitionOfTypeShow.keys():
		condition=df_rosterDivitionShows['Divition']==divition
		c_total_matches=dict_divitionOfTypeShow.get(divition)
		v_serie_cant=df_rosterDivitionShows.loc[condition]['Cant']
		v_serie_tcant=df_rosterDivitionShows.loc[condition]['TCant']
		v_result_div=v_serie_cant.div(v_serie_tcant)
		v_result_mult=v_result_div.mul(c_total_matches)
		df_rosterDivitionShows.loc[condition,['Proportion']]=v_result_mult*0.9
		df_rester_div_intergender.loc[df_rester_div_intergender['Divition']==divition,['Proportion']]=c_total_matches*0.1
	df_rester_div_intergender=df_rester_div_intergender[df_rosterDivitionShows.columns]
	df_rosterDivitionShows=pd.concat([df_rosterDivitionShows,df_rester_div_intergender], axis=0)
	df_rosterDivitionShows['Proportion']=df_rosterDivitionShows['Proportion'].fillna(0)
	df_rosterDivitionShows['IntProportion']=df_rosterDivitionShows['Proportion'].round().astype(int)
	df_rosterDivitionShows['Proportion-IntProportion']=df_rosterDivitionShows['Proportion'].sub(df_rosterDivitionShows['IntProportion'])
	df_rosterDivitionShows['Brand']=show
	#v_test=df_rosterDivitionShows.groupby(['Brand','Divition'])['Proportion'].sum()
	#v_test2=df_rosterDivitionShows.groupby(['Brand','Divition'])['IntProportion'].sum()
	#debugging(f"{v_test}\n{v_test2}")
	u_total_div=df_rosterDivitionShows.groupby(['Brand','Divition'])['Proportion-IntProportion'].sum().reset_index()
	u_total_div_=df_rosterDivitionShows.loc[(df_rosterDivitionShows['IntProportion']==0)].groupby(['Brand','Divition'])['IntProportion'].count().reset_index()
	u_total_div=pd.merge(u_total_div,u_total_div_,on=['Brand','Divition'],  how='right')
	u_total_div['Val']=u_total_div['Proportion-IntProportion'].div(u_total_div['IntProportion'])
	u_total_div['Val']=u_total_div['Val'].round().astype(int)
	u_total_div=u_total_div[['Brand','Divition','Val']]
	df_rosterDivitionShows=pd.merge(df_rosterDivitionShows,u_total_div,on=['Brand','Divition'],  how='left')
	df_rosterDivitionShows.loc[(df_rosterDivitionShows['IntProportion']==0),['IntProportion']]=df_rosterDivitionShows.loc[(df_rosterDivitionShows['IntProportion']==0)]['Val']
	df_rosterDivitionShows=df_rosterDivitionShows.rename(columns={'Brand': 'TV Show'})
	return df_rosterDivitionShows
def getMaxCantMachesByShow(show,dict_parameters):
	df_tvShows=getDfTvShowByShow(show,dict_parameters)
	c_total_matches=df_tvShows['MaxMatches'].head().item()
	return int(c_total_matches)
def getDfTvShowByShow(show,dict_parameters):
	df_tvShows=getDFTvShowsActive(dict_parameters)
	df_tvShows=df_tvShows.loc[(df_tvShows['Show'])==show]
	return df_tvShows
def getDictDistributionMatchesByDivitionAndTypeTvShow(show,dict_parameters,c_total_matches):
	df_tvShows=getDfTvShowByShow(show,dict_parameters)
	dict_=readBasicConfigValuesJson()
	dict_typeTvShow=dict_.get("ProportionMatchesByTypeTvShow")
	dict_divitionOfTypeShow=dict_typeTvShow.get(df_tvShows["TVShowType"].head().item())
	for divition in dict_divitionOfTypeShow.keys():
		v_proportion=dict_divitionOfTypeShow.get(divition)*c_total_matches
		dict_divitionOfTypeShow.update({divition:v_proportion})
	return dict_divitionOfTypeShow
def debugging(data):
    printTypeAndContent(data)
    raise Exception("JuanK is debugging")
def printTypeAndContent(data):
    print(f'printTypeAndContent\n{type(data)}\n{data}')

def calcularRosterDivision(df_matches,type_match):
    type_match,cantParticipant=splitTextFromNumber(type_match)
    v_columns=list([])
    if 'Single' in type_match:
        db_femaleP=db_wrestlers.get('Female')
        db_maleP=db_wrestlers.get('Male')
        v_columns=appendSingleWrestlersColumns(v_columns,1,cantParticipant)
        for index,row in df_matches.iterrows():        
            sum_popularity=0
            df_male=db_maleP.loc[db_maleP['WrestlerName'].isin(row[v_columns]),['BestRating','Brand']]
            sum_popularity+=sum(df_male['BestRating'])
            df_female=db_femaleP.loc[db_femaleP['WrestlerName'].isin(row[v_columns]),['BestRating','Brand']]
            sum_popularity+=sum(df_female['BestRating'])
            av_pop=sum_popularity/cantParticipant
            if len(df_male)>len(df_female):
                df_matches=setRosterDivition(df_matches,df_roster_divition,df_male['Brand'],av_pop,index,'Male')                
            else:
                df_matches=setRosterDivition(df_matches,df_roster_divition,df_female['Brand'],av_pop,index,'Female')
    else:
        df_matches=calcularRosterDivisionTag(df_matches,cantParticipant)
    
    return df_matches
def calcularLuchasFaltantesPorProgramar(df_matches,df_cantMatByShow):
    #TODO
    df_matches=df_matches.loc[(df_matches['Week']==obtainWeekOfGame())]
    return df_cantMatByShow
def calcularRosterDivisionTag(df_matches,cantParticipant):
    v_columns=list([])
    v_columns=appendTagWrestlersColumns(v_columns,1,cantParticipant)
    db_teamsP=db_wrestlers.get('Tag')
    if not db_teamsP.empty:
        for index,row in df_matches.iterrows():
            sum_popularity=0
            df_tag=db_teamsP.loc[db_teamsP['W1'].isin(row[v_columns])]
            df_tag=df_tag.loc[df_tag['W2'].isin(row[v_columns])]
            sum_popularity+=sum(df_tag['BestRating'])
            if len(df_tag)>0:
                av_pop=sum_popularity/len(df_tag)
                df_matches=setRosterDivition(df_matches,df_roster_divition,df_tag['Brand'],av_pop,index,'Tag')
            else:
                av_pop=65.5#Todo: JK This Sceneario si for teams maked by hand so think in a way to solve it.
                df_matches=setRosterDivition(df_matches,df_roster_divition,['All'],av_pop,index,'Tag')
    return df_matches
def setRosterDivition(df_matches,df_roster_divition,df_brand,av_pop,index,p_type):
    df_divition=df_roster_divition.loc[(df_roster_divition['Type']==p_type)
                                                       &(df_roster_divition['MaxPopularity']>=av_pop)
                                                       &(df_roster_divition['MinPopularity']<av_pop)
                                                       &(df_roster_divition['Brand'].isin(df_brand))
                                                       ,['Divition']]
    if len(df_divition)>0:
        #row['RosterDivision']=df_divition.Divition.head().item()
        df_matches.loc[index,['RosterDivision']]=df_divition.Divition.head(1).item()
        #print(f'calcularRosterDivisionTag\n\tRow\n{row}\nTag\n{df_tag}')
        df_matches.loc[index,['ExpectedRaiting']]=av_pop
    else:
        raise Exception(f'JuanK is Debbugging\n{df_roster_divition,df_brand,av_pop,index}')
    return df_matches
def splitTextFromNumber(text):
    import re
    match = re.match(r"([a-z]+)([0-9]+)", text, re.I)
    if match:
        items = match.groups()
    else:
        print(f'text\t{text}')
        items =[text,1]
    return items[0],int(items[1])
# def generateMatchesForShows(list_shows_preparar,df_cantMatByShow,df_cantPBMT):
	# global dict_matches
	# list_columns_cantmatch_generate=['Type','Divition']
	# for elements in list_shows_preparar:
		# print(f'Vamos a armar:\n{elements}')
		# df_CantMatch=df_cantMatByShow.loc[df_cantMatByShow['TV Show']==elements]
		# dict_matches=generateMatches(df_CantMatch.loc[(df_CantMatch['IntProportion']!=0)][list_columns_cantmatch_generate],df_cantPBMT,elements)
	# return dict_matches

def generateMatches(df_cantmatches,df_baloto_singles,str_show):
	import random
	list_columns_cantmatch_types=df_cantmatches['Type'].unique()
	debugging(f"{list_columns_cantmatch_types}\n{df_baloto_singles}")
	
	
	
	
	
	
	
	
	
	for key in list_columns_cantmatch_types:
		cantMatches=df_cantmatches[[key,'Divition']]
		df_rosterDivition=df_roster_divition[(df_roster_divition['Type']==key) 
											 &(df_roster_divition['Divition'].isin(df_cantmatches['Divition']))
											]
		for dkey in df_rosterDivition['Divition'].drop_duplicates():
			v=cantMatches[key][cantMatches['Divition']==dkey]
			#print(f'cantMatches:\n{v,dkey,str_show,key,cantMatches.Divition}')
			cant_iter=int(v+1)            
			for i in range(1,cant_iter):
				#print(f'df_baloto_singles:\n{df_baloto_singles}')
				random_n=random.randint(1,len(df_baloto_singles))
				if key=='Tag':                    
					cantParticipant=df_baloto_singles.Tag.loc[random_n].item()
				else:
					cantParticipant=df_baloto_singles.Single.loc[random_n].item()
				v_brand=getBrandByShow(str_show)
				df_rosterD_BK=df_rosterDivition[(df_rosterDivition['Divition']==dkey)&(df_rosterDivition['Brand']==v_brand)]
				if len(df_rosterD_BK)==0:
					raise Exception(f"Sorry,{df_rosterD_BK} is empty")
				df_match=generateMatch(cantParticipant,key,df_rosterD_BK,
									   str_show,v_brand)
				if df_match.empty==False:
					dic_key=str(df_match.head(1).TypeMatch.item());
					v_dic_k=list(dict_matches.keys())
					if dic_key in v_dic_k:
						dict_matches[dic_key]=dict_matches[dic_key].append(df_match, ignore_index=True)                    
					else:
						dict_matches[dic_key]=df_match
	debugging(dict_matches)
	return dict_matches
def getBrandByShow(show):
    df_tvShows=getDFTvShowsActive()
    df_tvShows=df_tvShows.loc[(df_tvShows['TV Show'])==show]
    if len(df_tvShows)==0:
        raise Exception(f"Sorry,{df_tvShows} is empty when filter by {show}")
    c_brand=df_tvShows['Brand'].head().item()
    return c_brand
def generateMatch(cantParticipant,key,df_rosterDivition,str_show,brand):    
    if (key=='Male') | (key=='Female'):
        return generateSingleMatch(cantParticipant,str_show,df_rosterDivition,key,brand)
    else:
        return generateTagMatch(cantParticipant,str_show,df_rosterDivition,brand)
def generateSingleMatch(cantParticipant,str_show,df_rosterDivition,key,brand):
	global db_femaleP
	global db_maleP
	if key=='Male':
		db_wrestlers=db_maleP.loc[db_maleP['Brand']==brand]
		if len(db_wrestlers)==0:
			db_wrestlers=generateRosterForDark(db_maleP)
	elif key=='Female':
		db_wrestlers=db_femaleP.loc[db_femaleP['Brand']==brand]
		if len(db_wrestlers)==0:
			db_wrestlers=generateRosterForDark(db_femaleP)
	else:
		raise Exception(f"Sorry,{key} is not a valid option")
	str_type_match='Single'
	v_week=obtainWeekOfGame()
	db_wrestlers=removeWrestlersThatCantParticipateInTheShow(str_show,v_week,db_wrestlers,str_type_match)
	df_wrestlerstoFight=generateWrestlerToFight(db_wrestlers,str_type_match,df_rosterDivition)
	df_wrestlerselected=df_wrestlerstoFight.head(cantParticipant)
	if cantParticipant>len(df_wrestlerselected):
		print(f'No tenemos suficientes luchadores para el combate: {cantParticipant,len(df_wrestlerselected),str_type_match}')
		cantParticipant=len(df_wrestlerselected)
	if (cantParticipant<2) :
		if len(db_wrestlers)>0:
			db_wrestlers=limpiarBaseDeCaraALuchasYaPactadas(db_wrestlers,str_type_match)
			print(f'Base de luchadores: {db_wrestlers}')
		else:
			print(f'No hay luchadores')
		return pd.DataFrame([])
	v_columns=getFirstColumnsForMatches()
	v_columns=appendSingleWrestlersColumns(v_columns,1,cantParticipant)        
	v_columns.append('Defeated')
	v_columns.append('Best')
	v_columns.append('SuggestWinner')
	v_columns.append('ExpectedRaiting')
	df_matches=pd.DataFrame([],columns=v_columns)    
	v_row=list([])
	v_row.append(v_week)
	v_row.append(str_show)
	v_row.append(str_type_match+str(cantParticipant))
	v_row.append(df_rosterDivition.Divition.head().item())
	for name_wrestler in df_wrestlerselected.WrestlerName:
		v_row.append(name_wrestler)
	#print(v_row)
	v_row.append(None)
	v_row.append(None)
	v_row.append(getSuggestWinner(df_wrestlerselected,False))
	v_row.append(getExpectedRaiting(df_wrestlerselected,False))
	a_series = pd.Series(v_row, index = v_columns)
	df_matches=df_matches.append(a_series, ignore_index=True)
	#print(f'df_matches:{len(df_matches)}')
	#db_wrestlers=db_wrestlers.drop(index=df_wrestlerselected.index)
	if key=='Male':
		db_maleP=db_maleP.drop(index=df_wrestlerselected.index)
	elif key=='Female':
		db_femaleP=db_femaleP.drop(index=df_wrestlerselected.index)
	return df_matches
def generateRosterForDark(db_wrestlers):
    db_wrestlers=db_wrestlers.loc[db_wrestlers['ExpectedShows']!='No B-TV Or House Shows']
    print(f'ForDark\n{db_wrestlers}')
    return db_wrestlers
def removeWrestlersThatCantParticipateInTheShow(str_show,full_week,df_wrestlers,str_type_match):
	v_year,v_month,v_week=transformFullWeekInTheirParts(full_week)
	df_wCantParticipate=getDfWrestlersCantParticipate()
	df_wCantParticipate=df_wCantParticipate.loc[(df_wCantParticipate['Show']==str_show)&((df_wCantParticipate['Week']==v_week)|(df_wCantParticipate['Week']=='Every'))&((df_wCantParticipate['Month']==v_month)|(df_wCantParticipate['Month']=='Every'))]
	if str_type_match=='Single':
		df_wFound=df_wrestlers.loc[df_wrestlers['WrestlerName'].isin(df_wCantParticipate['WName'])]
		df_wrestlers=df_wrestlers.drop(index=df_wFound.index)
	elif str_type_match=='Tag':
		for w in ['W1','W2']:
			df_wFound=df_wrestlers.loc[df_wrestlers[w].isin(df_wCantParticipate['WName']),['Tag Name']]
			df_wrestlers=df_wrestlers.drop(index=df_wFound.index)
	return df_wrestlers
def getDfWrestlersCantParticipate():
	df_wCantParticipate=db_parameters.get('WCantParticipate')
	return df_wCantParticipate
def transformFullWeekInTheirParts(full_week):
	#Example 202203W1
	v_year=int(str(full_week)[0:4])
	v_month=int(str(full_week)[4:6])
	v_week=str(full_week)[6:8].upper()
	return v_year,v_month,v_week
def generateWrestlerToFight(db_wrestlers,str_type_match,df_rosterDivition,is_shuffle,dict_matches):
	db_wrestlers=limpiarBaseDeCaraALuchasYaPactadas(db_wrestlers,str_type_match,dict_matches)
	if len(db_wrestlers.values)>0:
		try:
			p1=df_rosterDivition.loc[(df_rosterDivition["Brand"].isin(db_wrestlers['Brand'])),['MinPopularity']]['MinPopularity']
			p1=p1.head(1).item()
			#df_rosterDivition['MinPopularity'].item()
			p2=df_rosterDivition.loc[df_rosterDivition["Brand"].isin(db_wrestlers['Brand']),['MaxPopularity']]['MaxPopularity'].head().item()
			#df_rosterDivition.MaxPopularity.item()
			df_wrestlerstoFight=db_wrestlers[(db_wrestlers["BestRating"]>p1)&(db_wrestlers["BestRating"]<=p2) & 
											 (db_wrestlers["Active"]==1)]
		except:
			raise Exception(f'db_wrestlers\n{db_wrestlers}')
		if is_shuffle:
			df_wrestlerstoFight=df_wrestlerstoFight.sample(frac = 1)
		MAX_CANT_PARTICIPANTS_BY_ROSTER=4 #ToDo: JuanK need to read the max cant of participants in matches of BasicConfigValues.json
		list_nameWrestlers=getNameWrestlers(df_wrestlerstoFight.head(MAX_CANT_PARTICIPANTS_BY_ROSTER))
		lst_duplicateWrestlers=findingDuplicateItemsInList(list_nameWrestlers)
		if len(lst_duplicateWrestlers)>0:
			#Get max unique participants
			cant_selected=0
			df_wrestlers_selected=pd.DataFrame([],columns=df_wrestlerstoFight.columns)
			while cant_selected<MAX_CANT_PARTICIPANTS_BY_ROSTER:
				df_head=df_wrestlerstoFight.copy().head(1)
				df_wrestlers_selected=df_wrestlers_selected.append(df_head, ignore_index=True)
				df_wrestlerstoFight=df_wrestlerstoFight.drop(index=df_head.index)
				list_nameWrestlers=getNameWrestlers(df_wrestlers_selected)
				df_ws=retrieveDFOnlyWrestlersNames(df_wrestlerstoFight)
				for column in df_ws.columns:
					df_founded=df_ws.loc[df_ws[column].isin(list_nameWrestlers)]
					if len(df_founded.values)>0:
						df_wrestlerstoFight=df_wrestlerstoFight.drop(index=df_founded.index)
				if df_wrestlerstoFight.empty:
					break
				else:
					cant_selected+=1
			return df_wrestlers_selected
		# df_tag_selected=df_wrestlerstoFight.head(1)
		# df_wrestlerselected=df_wrestlerselected.append(df_tag_selected, ignore_index=True)
		# wreslters_tagTeam=getWrestlersFromTagTeams(df_tag_selected)        
		# df_w=df_wrestlerstoFight.loc[df_wrestlerstoFight['W1'].isin(wreslters_tagTeam)
									# |df_wrestlerstoFight['W2'].isin(wreslters_tagTeam)]
		# df_wrestlerstoFight=df_wrestlerstoFight.drop(index=df_w.index)
		return df_wrestlerstoFight
	else:
		return db_wrestlers
def limpiarBaseDeCaraALuchasYaPactadas(db_wrestlers,str_type_match,dict_matches):
    #global db_wrestlers
    v_dic_k=list(dict_matches.keys())
    if v_dic_k:
        for key in dict_matches.keys():
            df_matches=dict_matches[key]
            #db_teamsP['W1'].isin(rowfind.get('WrestlerName')),['W1','Tag Name']
            df_matches=df_matches.loc[(df_matches['Week']==obtainWeekOfGame())]
            #print(f'df:\n{df}')
            #LimpiarLuchadoresYaPactados            
            db_wrestlers=deleteBookedWrestlers(df_matches,db_wrestlers,str_type_match)                                    
    else:
        print('Primera vez')
    return db_wrestlers
def deleteBookedWrestlers(df_matches,db_wrestlers,str_type_match):
	v_columns=df_matches.columns
	for col_name in v_columns:
		if 'W' in col_name:
			if str_type_match.__contains__('Tag'):
				for w in ['W1','W2']:
					df_w=db_wrestlers.loc[db_wrestlers[w].isin(df_matches.get(col_name)),['Tag Name']]
					db_wrestlers=db_wrestlers.drop(index=df_w.index)
			elif str_type_match.__contains__('Trios'):
				for w in ['W1','W2','W3']:
					df_w=db_wrestlers.loc[db_wrestlers[w].isin(df_matches.get(col_name)),['Name']]
					db_wrestlers=db_wrestlers.drop(index=df_w.index)
			else:
				try:
					df_w=db_wrestlers.loc[db_wrestlers['WrestlerName'].isin(df_matches.get(col_name)),['WrestlerName']]
					#print(f'df_w:\n{df_w}')
					db_wrestlers=db_wrestlers.drop(index=df_w.index)
				except:
					debugging(f"{db_wrestlers}\n{str_type_match}")
	return db_wrestlers
def generateMatch(str_type_match,show,type_match,v_divition,df_wrestlerselected):
	#4.6- Generate the match Depending of the Type its sctructure change
	#4.6.1- Take the structure from BasicConfigValues.json dict matches
	dict_basic_values=readBasicConfigValuesJson()
	v_matches="Matches"
	dict_matchesConf=dict_basic_values.get(v_matches)
	dict_typeMatchConfig=dict_matchesConf.get(str_type_match)
	v_columns=list(dict_typeMatchConfig.keys())
	df_match=pd.DataFrame([],columns=v_columns)
	v_week=obtainWeekOfGame()
	v_row=list([])
	v_row.append(v_week)
	v_row.append(show)
	v_row.append(type_match)
	v_row.append(v_divition)
	list_nameWrestlers=getNameWrestlers(df_wrestlerselected)
	for name_wrestler in list_nameWrestlers:
		v_row.append(name_wrestler)
	patterns=[r"Defeated\d|Defeated"]
	lst_defeat=filterListElementsByRegex(patterns,v_columns)
	for d_col in lst_defeat:
		v_row.append(None)
	v_row.append(None)
	v_row.append(getSuggestWinner(list_nameWrestlers))
	v_row.append(getExpectedRaiting(df_wrestlerselected,False))
	v_row.append(None)
	v_row.append(None)
	if len(df_match.columns)!=len(v_row):
		debugging(f'{len(df_match.columns)}\n{df_match.columns}\n{len(v_row)}')
	df_match.loc[len(df_match)]=v_row
	return df_match
def getNameWrestlers(df_wrestlerSelected):
	v_lenOriginalColumns=len(df_wrestlerSelected.columns)
	df_wrestlerSelected=retrieveDFOnlyWrestlersNames(df_wrestlerSelected)
	v_lenFilteredColumns=len(df_wrestlerSelected.columns)
	if v_lenOriginalColumns==v_lenFilteredColumns:
		debugging(df_wrestlerSelected)
	v_nameWrestlers=[]
	for column in df_wrestlerSelected.columns:
		v_nameWrestlers.extend(df_wrestlerSelected[column].tolist())
	return v_nameWrestlers
def retrieveDFOnlyWrestlersNames(df_wrestler):
	return df_wrestler.filter(regex=("W\d|WrestlerName"))
def getFirstColumnsForMatches():
    v_columns=list(['Week','Show','TypeMatch','RosterDivision'])
    return v_columns
def generateTagMatch(cantParticipant,str_show,df_rosterDivition,brand):
	global db_teamsP
	str_type_match='Tag'
	db_wrestlers=db_teamsP.loc[db_teamsP['Brand']==brand]
	#if len(db_wrestlers)==0:
		#db_wrestlers=generateTagRosterForDark(db_teamsP)
	if len(db_wrestlers)==0:
		print(f'No hay luchadores {str_type_match} para {str_show}\n\tdivisión\n{df_rosterDivition}')
		return pd.DataFrame([])
	v_week=obtainWeekOfGame()
	db_wrestlers=removeWrestlersThatCantParticipateInTheShow(str_show,v_week,db_wrestlers,str_type_match)
	df_wrestlerstoFight=generateWrestlerToFight(db_wrestlers,str_type_match,df_rosterDivition)
	if len(df_wrestlerstoFight)<2:
		print(f'No se generaron luchadores {str_type_match} para {str_show}\n\tdivisión\n{df_rosterDivition}\n{df_wrestlerstoFight}')
		return pd.DataFrame([])
	df_wrestlerselected=pd.DataFrame([],columns=list(db_wrestlers.columns))
	for i in range(1,cantParticipant+1):
		df_tag_selected=df_wrestlerstoFight.head(1)
		df_wrestlerselected=df_wrestlerselected.append(df_tag_selected, ignore_index=True)
		wreslters_tagTeam=getWrestlersFromTagTeams(df_tag_selected)        
		df_w=df_wrestlerstoFight.loc[df_wrestlerstoFight['W1'].isin(wreslters_tagTeam)
									|df_wrestlerstoFight['W2'].isin(wreslters_tagTeam)]
		df_wrestlerstoFight=df_wrestlerstoFight.drop(index=df_w.index)
	if cantParticipant>len(df_wrestlerselected):
		print(f'No tenemos suficientes luchadores {str_type_match} para el combate: {cantParticipant,len(df_wrestlerselected)}')
		print(f'\tdivisión\n{df_rosterDivition}')
		cantParticipant=len(df_wrestlerselected)
	if (cantParticipant<2) :
		if len(df_wrestlerselected)>0:
			print(f'Base de luchadores:\n {df_wrestlerselected}')
		else:
			print(f'No hay luchadores')
		return pd.DataFrame([])
	v_columns=getFirstColumnsForMatches()
	v_columns=appendTagWrestlersColumns(v_columns,1,cantParticipant)
	v_columns.append('Defeated1')
	v_columns.append('Defeated2')
	v_columns.append('Best')
	v_columns.append('SuggestWinner')
	v_columns.append('ExpectedRaiting')
	df_matches=pd.DataFrame([],columns=v_columns)
	v_row=list([])
	v_row.append(v_week)
	v_row.append(str_show)
	v_row.append(str_type_match+str(cantParticipant))
	if isinstance(df_rosterDivition.Divition, pd.Series):
		v_row.append(df_rosterDivition.Divition.head().item())
	else:
		v_row.append(df_rosterDivition.Divition.head())
	for team_index in df_wrestlerselected.index:
		v_row.append(df_wrestlerselected.loc[team_index].W1)
		v_row.append(df_wrestlerselected.loc[team_index].W2)
	v_row.append(None)
	v_row.append(None)
	v_row.append(None)
	v_row.append(getSuggestWinner(df_wrestlerselected))
	v_row.append(getExpectedRaiting(df_wrestlerselected))
	#print(f'v_row:{v_row}')
	#print(f'v_columns:{v_columns}')
	a_series = pd.Series(v_row, index = v_columns)
	df_matches=df_matches.append(a_series, ignore_index=True)
	#print(f'df_wrestlerselected\n{df_wrestlerselected}\ndb_wrestlers\n{db_wrestlers}')
	db_find=db_wrestlers.loc[db_wrestlers['Tag Name'].isin(df_wrestlerselected['Tag Name'])]
	#db_wrestlers=db_wrestlers.drop(index=db_find.index)
	db_teamsP=db_teamsP.drop(index=db_find.index)
	return df_matches
def generateTagRosterForDark(db_teamsP):
    global db_femaleP
    global db_maleP
    db_wrestlers_maleP=generateRosterForDark(db_maleP)
    db_wrestlers_femaleP=generateRosterForDark(db_femaleP)
    list_df=[db_wrestlers_maleP,db_wrestlers_femaleP]
    db_wrestlers=removeTagsByWrestlers(list_df,db_teamsP)
    return db_wrestlers
def getWrestlersFromTagTeams(df_tag):
    wreslters_tagTeam=list(df_tag.loc[:,'W1'])
    wreslters_tagTeam2=list(df_tag.loc[:,'W2'])
    wreslters_tagTeam=wreslters_tagTeam+(wreslters_tagTeam2)
    return wreslters_tagTeam
def checkScheduleMatch(db_wrestlers,df_wrestlerselected,str_type_match):
    ##ToDo
    return df_wrestlerselected
def appendSingleWrestlersColumns(v_columns,ini,until):
    for i in range(ini,until+1):
        v_columns.append('W'+str(i))
    return v_columns
def appendTagWrestlersColumns(v_columns,ini,until):
    for i in range(ini,until+1):
        v_columns.append('T'+str(i)+'W1')
        v_columns.append('T'+str(i)+'W2')
    return v_columns
def getSuggestWinner(list_nameWrestlers):
	import random
	wrestler="Me"
	if len(db_matchesResume.values)>0:
		db_l_matchesResume=db_matchesResume.loc[(db_matchesResume['WorkerName'].isin(list_nameWrestlers))]
		try:
			if bool(random.getrandbits(1)):
				index=db_l_matchesResume['Percentage'].idxmin()
			else:
				index=db_l_matchesResume['Percentage'].idxmax()
			wrestler=db_l_matchesResume['WorkerName'][index]
		except BaseException:
			print("No hay matchesResume")
	else:
		index=random.randint(0,len(list_nameWrestlers)-1)
		wrestler=list_nameWrestlers[index]
	return wrestler
def getExpectedRaiting(df_wrestlerselected,isTeam=True):
    expectedRaiting=0
    if isTeam:
        expectedRaiting=df_wrestlerselected['BestRating'].mean()
    else:
        expectedRaiting=df_wrestlerselected['BestRating'].mean()
    print(f'getExpectedRaiting\t{expectedRaiting}')
    return expectedRaiting
def writeMatchesExcel(dict_matches):
	xlsx_file = Path(readRouteFolderIfExist(), 'Matches.xlsx')
	writeExcel(xlsx_file,dict_matches)    
def readParameters():
    xlsx_file = Path(readRouteFolderIfExist(), 'Param.xlsx')
    db_parameters=pd.read_excel(xlsx_file,None)
    return db_parameters
if __name__ == '__main__':
	db_parameters=readParameters()
	dict_matches=pd.read_excel(xlsx_matches,None)
	main()