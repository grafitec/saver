import maya.cmds as cmds
import maya.mel as mel

import os
import shutil
import time
from datetime import datetime
import __main__
import core.utility.mail as mail

import core.handler.data as data
import core.utility.interface as interface
from core.handler import browser
import core.validityChecker.validityCheck as vc

import core.handler.componentHandling.model as model
import core.handler.componentHandling.dev as dev
import core.handler.componentHandling.rig as rig
import core.handler.componentHandling.groom as groom
import core.handler.componentHandling.matchmove as matchmove
import core.handler.componentHandling.animation as animation
import core.handler.componentHandling.techAnim as techAnim
import core.handler.componentHandling.groomSim as groomSim
import core.handler.componentHandling.lookdev as lookdev
import core.handler.componentHandling.lighting as lighting
import core.handler.componentHandling.render as render

from core.metaData import metaData
reload(metaData)
reload(vc)
reload(browser)
reload(mail)
reload(data)
reload(interface)
reload(model)
reload(dev)
reload(rig)
reload(groom)
reload(matchmove)
reload(animation)
reload(techAnim)
reload(groomSim)
reload(lookdev)
reload(lighting)
reload(render)

class Saver():
	def __init__(self):
		windowState = cmds.window('saver_window', q=True, exists=True) 
		if windowState:
			cmds.deleteUI('saver_window')
		
		self.firstRun = True
		self.description = ''
		self.activeUser = '%s %s' %(__main__.activeUser.firstName, __main__.activeUser.lastName)
		
		# Load the standard UI file
		mayaUI = cmds.loadUI(uiFile=data.Constants().toolPath() + '/core/handler/saver/saver.ui')
		
		# Find the tab parent layout and create the actual tab layout
		tabParentLayout = cmds.button('saverFindLayout_button', q=True, parent=True)
		cmds.deleteUI('saverFindLayout_button') # Delete button after finding its layout
		self.saverTabLayout = cmds.tabLayout('saverTabs_tab', p=tabParentLayout)
		
		# Hook up functions
		cmds.radioButton('saverWork_radio', e=True, onc=self.loadWorkTabs, ofc=self.deleteTabContent)
		cmds.radioButton('saverSandbox_radio', e=True, onc=self.loadSandboxTabs, ofc=self.deleteTabContent)
		cmds.radioButton('saverPublish_radio', e=True, onc=self.loadPublishTabs, ofc=self.deleteTabContent)
		cmds.button('saverInitiate_button', e=True, c=self.initiate)
		
		# Initiate default setting - work tabs
		self.loadWorkTabs()
		
		# Set data
		self.activeUser  = '%s %s' %(__main__.activeUser.firstName, __main__.activeUser.lastName)
		sceneName = cmds.file(q=True, sn=True)
		if not sceneName:
			cmds.text('saverFilepath_label', e=True, l='Unsaved Scene')
		else:
			cmds.text('saverFilepath_label', e=True, l=sceneName)
		
		cmds.text('saverArtist_label', e=True, l=self.activeUser)
		cmds.text('saverCurrentStatus_label', e=True, l=__main__.activeComponent.status)
		
		try:
			modifiedTime = os.path.getmtime(sceneName)
			saveTime = datetime.fromtimestamp(modifiedTime).strftime("%d %b %Y, %H:%M:%S")
			cmds.text('saverLastSaved_label', e=True, l=saveTime)
		except:
			cmds.text('saverLastSaved_label', e=True, l='Never')
		
		pubPath = __main__.activeBasePath + '/published'
		files = os.listdir(pubPath)
		if files:
			latestFile = max(files)
			modifiedTime = os.path.getmtime(pubPath + '/' + latestFile)
			saveTime = datetime.fromtimestamp(modifiedTime).strftime("%d %b %Y, %H:%M:%S")
			cmds.text('saver_lastPublished', e=True, l=saveTime)
		else:
			cmds.text('saver_lastPublished', e=True, l='Never')
		
		'''
		imagePath = 'https://s3-eu-west-1.amazonaws.com/kove-files/fable/projects/1001_ERK/sequences/sq010/shots/sh210/sh210_largethumb.jpg'
		
		imageLayout = cmds.button('saverFindImageLayout_button', q=True, parent=True)
		cmds.deleteUI('saverFindImageLayout_button')
		cmds.image(image=imagePath, parent=imageLayout)
		http://www.hdwallpapersimages.com/wp-content/uploads/2014/01/Winter-Tiger-Wild-Cat-Images.jpg
		'''
		
		# Show the Window
		cmds.showWindow(mayaUI)
		
	def deleteTabContent(self, *args):
		self.description = cmds.scrollField('saverGeneralComment_text', q=True, text=True)
		for activeUi in self.activeTabs:
			cmds.deleteUI(activeUi)
		
	def setGeneralTabDefaults(self):
		cmds.optionMenu('saverGeneralStatus_optionMenu', e=True, v=__main__.activeComponent.status)
		cmds.intSlider('saverGeneralProgress_slider', e=True, v=int(__main__.activeComponent.percentage))
		cmds.text('saverGeneralProgress_label', e=True, l=__main__.activeComponent.percentage)
		cmds.progressBar('saverProgress_progressBar', e=True, min=0, max=1)
		cmds.progressBar('saverProgress_progressBar', e=True, min=0, max=100)
		if self.firstRun:
			cmds.progressBar('saverProgress_progressBar', e=True, s=int(__main__.activeComponent.percentage))
		else:
			cmds.progressBar('saverProgress_progressBar', e=True, s=int(int(__main__.activeComponent.percentage)+1))
		self.firstRun = False
		
	def runPreScripts(self, type):
		if type == 'pre':
			melCode = cmds.textField('saverGeneralPreSaveMel_lineEdit', q=True, tx=True)
			pythonCode = cmds.textField('saverGeneralPreSavePython_lineEdit', q=True, tx=True)
		elif type == 'post':
			melCode = cmds.textField('saverGeneralPostSaveMel_lineEdit', q=True, tx=True)
			pythonCode = cmds.textField('saverGeneralPostSavePython_lineEdit', q=True, tx=True)
		
		if melCode:
			mel.eval(melCode)
		if pythonCode:
			exec pythonCode
		
	def loadWorkTabs(self, *args):
		self.activeTabs = []
		
		generalTab = cmds.paneLayout('General', parent=self.saverTabLayout)
		generalWidget = cmds.loadUI(uiFile=data.Constants().toolPath() + '/core/handler/saver/general.ui')
		cmds.control(generalWidget, e=True, p=generalTab)
		self.setGeneralTabDefaults()
		
		# Edit data
		cmds.deleteUI('saverSandboxFilename_label')
		cmds.deleteUI('saverSandboxFilename_lineEdit')
		
		self.activeTabs.append(generalTab)
		cmds.scrollField('saverGeneralComment_text', e=True, text=self.description)
		
	def loadSandboxTabs(self, *args):
		self.activeTabs = []
		
		generalTab = cmds.paneLayout('General', parent=self.saverTabLayout)
		generalWidget = cmds.loadUI(uiFile=data.Constants().toolPath() + '/core/handler/saver/general.ui')
		cmds.control(generalWidget, e=True, p=generalTab)
		self.setGeneralTabDefaults()
		
		self.activeTabs.append(generalTab)
		cmds.scrollField('saverGeneralComment_text', e=True, text=self.description)
		
	def loadPublishTabs(self, *args):
		self.activeTabs = []
		generalTab = cmds.paneLayout('General', parent=self.saverTabLayout)
		generalWidget = cmds.loadUI(uiFile=data.Constants().toolPath() + '/core/handler/saver/general.ui')
		cmds.control(generalWidget, e=True, p=generalTab)
		self.setGeneralTabDefaults()
		
		self.activeTabs.append(generalTab)
		
		# Place render publisher at the very end
		activeSets = cmds.ls(type='objectSet')
		if 'publishRender' in activeSets:
			activeSets = activeSets + [activeSets.pop(activeSets.index('publishRender'))]
		
		for activeSet in activeSets:
			if activeSet[:7] == 'publish':
				publisher = activeSet[7:]
				#if data.Constants().departments()[publisher.lower()] == __main__.activeType or data.Constants().departments()[publisher.lower()] == 'all':
				publisherTab = cmds.paneLayout(publisher, parent=self.saverTabLayout)
				uiLocation = '%s/core/handler/saver/%s.ui' %(data.Constants().toolPath(), publisher.lower())
				publisherWidget = cmds.loadUI(uiFile=uiLocation)
				cmds.control(publisherWidget, e=True, p=publisherTab)
				
				self.activeTabs.append(publisherTab)
				
				# Load default settings
				if publisher.lower() == 'animation':
					animation.Animation().publishSettings()
				elif publisher.lower() == 'matchmove':
					matchmove.Matchmove().publishSettings()
				elif publisher.lower() == 'groomsim':
					groomSim.GroomSim().publishSettings()
				elif publisher.lower() == 'techanim':
					techAnim.TechAnim().publishSettings()
				elif publisher.lower() == 'render':
					render.Render().publishSettings()
				
		# Edit data
		cmds.deleteUI('saverSandboxFilename_label')
		cmds.deleteUI('saverSandboxFilename_lineEdit')
		cmds.scrollField('saverGeneralComment_text', e=True, text=self.description)
		
	def initiate(self, *args):
		if cmds.radioButton('saverWork_radio', q=True, sl=True):
			self.versionUp()
		elif cmds.radioButton('saverSandbox_radio', q=True, sl=True):
			self.sandbox()
		elif cmds.radioButton('saverPublish_radio', q=True, sl=True):
			self.publishValidity()
		
	def generateLatestVersionName(self, workDir, customComponent=None):
		versions = []
		for file in os.listdir(workDir):
			if file.endswith('ma'):
				if file.split('_')[3].split('.')[0][:1] == 'v':
					continue
				else:
					versions.append(file.split('_')[3].split('.')[0])
		
		try:
			newVerShort = int(max(versions)) + 1
		except:
			newVerShort = 1
		numLen = len(str(newVerShort))
		
		if numLen == 1:
			newVersion = '00%s' %(newVerShort)
		elif numLen == 2:
			newVersion = '0%s' %(newVerShort)
		else:
			newVersion = newVerShort
		
		if customComponent:
			newFilename = '%s_%s_%s_%s.ma' %(__main__.activeGroup.name, __main__.activeItem.name, customComponent, newVersion)
		else:
			newFilename = '%s_%s_%s_%s.ma' %(__main__.activeGroup.name, __main__.activeItem.name, __main__.activeComponent.name, newVersion)
			__main__.activeFileVersion = newVersion
		newPath = '%s/%s' %(workDir, newFilename)
		
		return newPath, newFilename, newVersion
		
	def versionUp(self, runScripts=True, deleteUi=True):
		
		if cmds.file(q=True, sn=True) == '':
			cmds.file(rename=__main__.activeFilePath)
		
		if runScripts:
			self.runPreScripts(type='pre')
		
		workDir = '%s/work/%s' %(__main__.activeBasePath, __main__.activeApplication)
		__main__.activeFilePath = self.generateLatestVersionName(workDir)[0]
		cmds.file(rename=__main__.activeFilePath)
		cmds.file(save=True, type='mayaAscii')
				
		
		__main__.activeFile = __main__.activeFilePath.split('/')[-1]
		#__main__.activeFile = cmds.file(q=True, sceneName=True, shn=True)
		
		
		if runScripts:
			self.runPreScripts(type='post')
		
		afterProcess = cmds.optionMenu('saverGeneralAfterProcess_comboBox', q=True, value=True)
		if afterProcess == 'Exit Maya':
			cmds.quit(force=True)
		elif afterProcess == 'New Task':
			browser.Browser()
		
		# fileInfo file
		
		
		comment = cmds.scrollField('saverGeneralComment_text', q=True, text=True)
		name = self.activeUser
		
		fileName = __main__.activeBasePath+"/work/maya/fileInfo.py"
		if not os.path.isfile(fileName):  
			pathFile = os.popen('attrib +h ' + fileName)
			pathFile = open(fileName, 'w') 
		else:
			pathFile = open(fileName, 'a')
		pathFile.write(__main__.activeFile+'|'+comment+'|'+name+'\n')
		pathFile.close()
		# thumbnail
		thumbnail()
		
		
		# update browserUI
		filePath = __main__.activeFilePath
		tmp = filePath.split('/')[-1]
		path = filePath.split(tmp)[0]
		
		try:
			cmds.textScrollList('file_listWidget', e=True, ra=True)
			cmds.textScrollList('file_listWidget', e=True, append='Create initial work file')
			cmds.textScrollList('file_listWidget', e=True, append='Set to active task')
			cmds.textScrollList('file_listWidget', e=True, append='Latest file')
			cmds.textScrollList('file_listWidget', e=True, append='-----')
			sortedList = sorted(os.listdir(path))
			if sortedList:
				for file in sortedList:
						if file.endswith('ma'):
							cmds.textScrollList('file_listWidget', e=True, append=file)
		except:
			pass
			
		
		if deleteUi:
			cmds.deleteUI('saver_window')
		
		# Start save timer
		#__main__.saveTimer.stop()
		#__main__.saveTimer.start()
		
	def sandbox(self, *args):
		self.runPreScripts(type='pre')
		filename = cmds.textField('saverSandboxFilename_lineEdit', q=True, tx=True)
		if not filename:
			cmds.warning('core: Could NOT save file, please enter a filename to proceed')
			return
		
		newPath = '%s/sandbox/%s' %(__main__.activeBasePath, filename)
		cmds.file(rename=newPath)
		cmds.file(save=True, type='mayaAscii')
		cmds.deleteUI('saver_window')
		
		# Update main
		__main__.activeFileVersion = 'None'
		__main__.activeFile = filename
		
		#self.updateKove()
		self.runPreScripts(type='post')
		
	def publishValidity(self, *args):
		self.runPreScripts(type='pre')
		if cmds.checkBox('saverGeneralComment_checkBox', q=True, v=True):
			__main__.saveDescription = cmds.scrollField('saverGeneralComment_text', q=True, text=True)
			if not __main__.saveDescription:
				cmds.warning('core: Could NOT publish file, please enter a description to proceed')
				return
		else:
			__main__.saveDescription = 'No comment specified..'
		
		# Check to see if we have render component, if we do. Do we have a place to publish?
		if 'Render' in cmds.tabLayout('saverTabs_tab', q=True, tli=True):
			publishComponent = cmds.optionMenu('saverRenderPublishUnder_combo', q=True, value=True)
			if not publishComponent:
				cmds.warning('core: You must specify a component container for render publish')
				return
		
		# Launch Validity
		vc.ValidityCheck(buttonName='Re-test', publishSequence=True, publishCommand=self.publish).start()
		cmds.window('saver_window', e=True, vis=False)
		
	def publish(self, *args):
		cmds.deleteUI('validityCheck_window')
		
		publishProgressWindow = cmds.window('Publish progress')
		cmds.columnLayout()
		progressControl = cmds.progressBar(minValue=0, maxValue=100, step=11, width=300)
		cmds.showWindow(publishProgressWindow)
		
		publishTypes = cmds.tabLayout('saverTabs_tab', q=True, tli=True)
		if len(publishTypes) == 1: # WE NEED TO ABORT
			cmds.deleteUI('saver_window')
			interface.Dialog().warning('MISSING PUBLISH SET', 'Aborted publish due to missing publish set/-s')
			cmds.warning('core: Aborted publish due to missing publish set/-s')
			return
		
		if __main__.activeFileVersion == 'None':
			self.versionUp(deleteUi=False)
		print 'steg1'
		progressValue = (70 / (len(publishTypes)-1)) / 2
		for publishType in publishTypes:
			cmds.progressBar(progressControl, edit=True, step=progressValue)
			if not publishType == 'General':
				if cmds.checkBox('saver' + publishType + 'Enabled_checkBox', q=True, v=True):
					if publishType.lower() == __main__.activeComponent.name.lower():
						print 'publishType.lower():', publishType.lower()
						publishDirectory = '%s/published/%s' %(__main__.activeBasePath, __main__.activeFile.split('.')[0])
						publishFilePath = '%s/%s' %(publishDirectory, __main__.activeFile)
						filename = __main__.activeFile

					elif publishType.lower() == 'render':
						publishComponent = cmds.optionMenu('saverRenderPublishUnder_combo', q=True, value=True)
						setBasePath = '%s/%s/%s/%s/%s/%s' %(data.Constants().projectPath(), __main__.activeProject.name, __main__.activeType, __main__.activeGroup.name, __main__.activeItem.name, publishComponent.lower())
						publishDirectory = '%s/published/render' %(setBasePath)
						publishFilePath = '%s/%s' %(publishDirectory, __main__.activeFile)

					else: 
						# Publish outside of active component
						setBasePath = '%s/%s/%s/%s/%s/%s' %(data.Constants().projectPath(), __main__.activeProject.name, __main__.activeType, __main__.activeGroup.name, __main__.activeItem.name, publishType.lower())
						setWorkPath = '%s/work/%s' %(setBasePath, __main__.activeApplication)
						newFileInfo = self.generateLatestVersionName(setWorkPath, customComponent=publishType.lower())
						filename = newFileInfo[1]
						publishDirectory = '%s/published/%s' %(setBasePath, filename.split('.ma')[0])
						publishFilePath = '%s/%s' %(publishDirectory, filename.split('.ma')[0])

						# Copy our file to its appropriate component
						shutil.copy2(__main__.activeFilePath, newFileInfo[0])
					
					print 'steg2'
					# Do the actual publish
					if publishType.lower() == 'model':
						status = model.Model().publish(publishDirectory, publishFilePath)
					elif publishType.lower() == 'rig':
						status = rig.Rig().publish(publishDirectory, publishFilePath)
					elif publishType.lower() == 'groom':
						status = groom.Groom().publish(publishDirectory, publishFilePath, filename)
					elif publishType.lower() == 'lookdev':
						status = lookdev.Lookdev().publish(publishDirectory, publishFilePath, filename)
					elif publishType.lower() == 'matchmove':
						status = matchmove.Matchmove().publish(publishDirectory, publishFilePath)
					elif publishType.lower() == 'techanim':
						status = techAnim.TechAnim().publish(publishDirectory, publishFilePath)
					elif publishType.lower() == 'groomsim':
						import core.handler.componentHandling.groomSim as groomSim
						reload(groomSim)
						print publishType.lower()
						status = groomSim.GroomSim().publish(publishDirectory, publishFilePath)
					elif publishType.lower() == 'lighting':
						status = lighting.Lighting().publish(publishDirectory, publishFilePath)
					elif publishType.lower() == 'render':
						status = render.Render().publish(publishDirectory, publishFilePath)
					elif publishType.lower() == 'animation':
						status = animation.Animation().publish(publishDirectory, publishFilePath)
						if cmds.checkBox('saverAnimationSendDeadlineGroomSim_checkBox', q=True, v=True):
							from groomsimtools import applyGrooms;reload(applyGrooms);applyGrooms.ApplyGrooms(hidden=True).updateGroom()
							import core.handler.componentHandling.groomSim as groomSim;reload(groomSim);groomSim.GroomSim().generateSet()
							status = groomSim.GroomSim().publish(publishDirectory, publishFilePath)
							yetiNodes = cmds.ls('*:*_yeti')
							for yeti in yetiNodes:
								cmds.delete(yeti)
						
					cmds.progressBar(progressControl, edit=True, step=progressValue)
					print 'steg3'
					# Check for notification email
					if status:
						if not publishType.lower() == 'render':
							if cmds.checkBox('saver' + publishType + 'Email_checkBox', q=True, en=True):
								timestamp = '%s, %s' %(time.strftime("%Y-%m-%d"), time.strftime("%H:%M"))
								subject = 'Publish Report: ' + __main__.activeProject.name + '/' + __main__.activeType + '/' + __main__.activeGroup.name + '/' + __main__.activeItem.name + '/' + publishType.lower()
								print 'steg 3.1'
								renderSubmit = 'False'
								if 'Render' in publishTypes:
									if cmds.checkBox('saverRenderEnabled_checkBox', q=True, v=True):
										renderSubmit = 'True'
								
								body = ('''
Author: ''' + __main__.activeUser.firstName + ' ' +__main__.activeUser.lastName + '''
Timestamp: ''' + timestamp + '''
Status: ''' + __main__.activeComponent.status + '''
Progress: ''' + str(__main__.activeComponent.percentage) + '''%
File: ''' + __main__.activeFile + '''
Path: ''' + __main__.activeBasePath + '/published/' + __main__.activeFile.split('.')[0] + '''
Render: ''' + renderSubmit + '''

Comment: ''' + str(__main__.saveDescription)) 
							
								toaddr = __main__.activeProject.name[5:] + '@fablefx.com'
								print '3.15'
								mail.send(subject, body, toaddr)
		print 'steg 3.2'						
		cmds.progressBar(progressControl, edit=True, step=10)
		if status:
			self.runPreScripts(type='post')
			self.updateKove(fileregistration=True, registerType='PUBLISH')
			self.versionUp(runScripts=False)
		print 'steg4'	
		cmds.progressBar(progressControl, edit=True, step=10)
		cmds.deleteUI(publishProgressWindow)
		cmds.select(cl=True)
	def updateKove(self, fileregistration=False, registerType=None):
		if __main__.projectManager == 'offline':
			print 'Ignoring file registration as of Offline mode'
		elif __main__.projectManager == 'kove':
			# Update status & Progress
			__main__.activeComponent.status = cmds.optionMenu('saverGeneralStatus_optionMenu', q=True, v=True)
			__main__.activeComponent.percentage = cmds.text('saverGeneralProgress_label', q=True, l=True)
			dict = {'status':__main__.activeComponent.status, 'percentage':__main__.activeComponent.percentage}
			#dict = {'status':newStatus, 'percentage':self.progress}
			
			if __main__.activeType == 'assets':
				__main__.kove.updateAssetComponent({'data':dict, 'projectId':__main__.activeProject.id, 'assetGroupId':__main__.activeGroup.id, 'assetId':__main__.activeItem.id, 'componentId':__main__.activeComponent.id})
			if __main__.activeType == 'sequences':
				__main__.kove.updateShotComponent({'data':dict, 'projectId':__main__.activeProject.id, 'sceneId':__main__.activeGroup.id, 'shotId':__main__.activeItem.id, 'componentId':__main__.activeComponent.id})
		elif __main__.projectManager == 'ftrack':
			print 'ftrack saver'
		print '# core: File successfully saved'
	

def thumbnail(path=None):
	if path == None:
		mayaScene = __main__.activeFilePath
	else:
		mayaScene = path
	
	frame = int(cmds.currentTime(q=True))
	fileName = mayaScene.split('/')[-1]
	mayaPath = mayaScene.split(fileName)[0]
	try:
		if 'work/maya' in mayaPath:
			if os.path.isfile(mayaPath+'/fileImages/'+fileName[:-3]+'.jpg'):
				os.remove(mayaPath+'/fileImages/'+fileName[:-3]+'.jpg')
			cmds.playblast(format='image', filename=mayaPath+'fileImages/'+fileName[:-3], viewer=0, showOrnaments=0, compression='jpg', offScreen=True, st=frame, et=frame, percent=100, widthHeight=(310,171))
			os.rename(mayaPath+'/fileImages/'+fileName[:-3]+'.'+str(frame)+'.jpg', mayaPath+'/fileImages/'+fileName[:-3]+'.jpg')
	except:
		pass