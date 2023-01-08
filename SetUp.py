import tkinter as tk
from tkinter import filedialog
from Utility import *
class SetUpUI(tk.Frame):
	def __init__(self, parent):		
		super().__init__(parent)
		#Label Description "Please introduce the route folder\nwhere the files will be create"
		text_=f"Please introduce the route folder\nwhere the files will be create"
		self.setLabelDescription(text_)
		#Label Folder "Folder"
		self.setLabelFolder("Folder")
		self.folder_route_var = tk.StringVar()
		#Entry	FolderRoute
		self.setEntryFolderRoute()
		#Button Explore
		self.setButtonExplore()
		#Button GenerateFiles
		self.setButtonGenerateFiles()
	def setLabelDescription(self,text_):
		self.description = tk.Label(self, text=text_)
		self.description.grid(row=1, column=1)
	def setLabelFolder(self,text_):
		self.Folder = tk.Label(self, text=text_)
		self.Folder.grid(row=2, column=0)
	def setEntryFolderRoute(self):
		self.folder_route_entry = tk.Entry(self, textvariable=self.folder_route_var, width=30)
		self.folder_route_entry.grid(row=2, column=1, sticky=tk.NSEW)
	def setButtonExplore(self):
		self.explore_button = tk.Button(self, text='Explore', command=self.actionExplore)
		self.explore_button.grid(row=2, column=3, padx=10)
	def setButtonGenerateFiles(self):
		self.generate_files_button = tk.Button(self, text='Generate Files', command=self.actionGenerateFiles)
		self.generate_files_button.grid(row=3, column=1, padx=10)	
	def actionExplore(self):
		filepath=filedialog.askdirectory(initialdir=r".",
									title="Dialog box")
		self.folder_route_var.set(filepath)
	def actionGenerateFiles(self):
		createFiles(self.folder_route_var.get())
def main():
	createWindowToSetUpTEW()
def createWindowToSetUpTEW():
	appWindow=getWindow()
	view=SetUpUI(appWindow)
	view.grid(row=0, column=0, padx=10, pady=10)
	routeFolder=readRouteFolderIfExist()
	view.folder_route_var.set(routeFolder)
	appWindow.mainloop()
def getWindow():
	appWindow = tk.Tk()
	appWindow.title("SetUp TEW2020")
	appWindow.minsize(500, 0)
	appWindow.resizable(False, False)
	return appWindow
def readRouteFolderIfExist():
	v_folder="./"
	v_file_name="Config.json"
	dict_config=readJsonFile(v_folder,v_file_name)
	routeFolder=dict_config.get("RouteFolderFiles","")	
	return routeFolder
def createFiles(routeFolder):
	updateConfigRouteFolder(routeFolder)
	createParamFile(routeFolder)
	createMatchesFile(routeFolder)
	createRosterFile(routeFolder)
	createAnglesFile(routeFolder)
	createStorylinesFile(routeFolder)
def updateConfigRouteFolder(routeFolder):
	v_folder="./"
	v_file_name="Config.json"
	dict_config=readJsonFile(v_folder,v_file_name)
	dict_config.update({"RouteFolderFiles":routeFolder})
	writeJson(dict_config,v_folder,v_file_name)
def createParamFile(routeFolder):
	dict_param={}
	df_calendar=generateCalendarDF()
	df_shows=generateShowsDF()
	df_roster_divition=generateRosterDivition()
	df_conf_match_type=generateConfMatchType()
	df_general=generateGeneralDF()
	dict_param.update({'Calendar':df_calendar})
	dict_param.update({'Shows':df_shows})
	dict_param.update({'RosterDivition':df_roster_divition})
	dict_param.update({'ConfMatchType':df_conf_match_type})
	dict_param.update({'General':df_general})
	writeExcel(routeFolder+"/"+"Param.xlsx",dict_param)
def generateCalendarDF():
	df_calendar=createDF([],['Week'])
	return df_calendar
def generateShowsDF():
	df_shows=createDF([],['Company','Show','ShowType','DayOfWeek','Week','Month','MaxMatches','Brand','ShowTime','PreShowTime','TimeMatch','TimeDarkMatch','TVShowType'])
	return df_shows
def generateRosterDivition():
	df_roster_divition=createDF([],['Divition','Cant','MinPopularity','MaxPopularity','Type','Gender','Brand'])
	return df_roster_divition
def generateConfMatchType():
	df_conf_match_type=createDF([],['Match Type','Min','Max','MinP','MaxP'])
	v_folder="./"
	v_file_name="BasicConfigValues.json"
	dict_basic_values=readJsonFile(v_folder,v_file_name)
	df_=dictToDataFrameByKey(dict_basic_values,"ConfMatchType")
	df_conf_match_type = pd.concat([df_conf_match_type, df_], ignore_index=True)
	return df_conf_match_type
def generateGeneralDF():
	df_general=createDF([],['SinceWeek','MDBFileRoute','CompanyInitials'])
	return df_general
def createMatchesFile(routeFolder):
	v_folder="./"
	v_file_name="BasicConfigValues.json"
	dict_basic_values=readJsonFile(v_folder,v_file_name)
	dict_matches=dictToDictOfDataFrame(dict_basic_values["Matches"])
	writeExcel(routeFolder+"/"+"Matches.xlsx",dict_matches)
def createRosterFile(routeFolder):
	v_folder="./"
	v_file_name="BasicConfigValues.json"
	dict_basic_values=readJsonFile(v_folder,v_file_name)
	dict_matches=dictToDictOfDataFrame(dict_basic_values["Roster"])
	writeExcel(routeFolder+"/"+"Roster.xlsx",dict_matches)
def createAnglesFile(routeFolder):
	createFileBasedInJsonBasicConfig(routeFolder,"Angles","Angles.xlsx")
def createStorylinesFile(routeFolder):
	createFileBasedInJsonBasicConfig(routeFolder,"StoryLinesAndDevelopment","StoryLinesAndDevelopment.xlsx")
def createFileBasedInJsonBasicConfig(routeFolder,dic_key,file):
	dict_basic_values=readBasicConfigValuesJson()
	dict_matches=dictToDictOfDataFrame(dict_basic_values[dic_key])
	writeExcel(routeFolder+"/"+str(file),dict_matches)
if __name__ == '__main__':
	main()
	print('Done')