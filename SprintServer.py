#!/usr/bin/env python
# -*- coding: utf-8 -*-

#-- stdlib imports
import logging

#-- third party import
import web
import logging

#-- project imports
import config as cfg
from JIRAdb import JIRAdb
from Sprint import Sprint

# where to look for templates, use layout.html as base class/template
render = web.template.render('templates/', base='layout')

# URLs supported
urls = (
  '/', 'index' ,
  '/query', 'query'
)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', filename='log.txt')
logging.info('Starting')
app = web.application(urls, globals())

class index:
	def GET(self):
		url = web.input(sprint=None, command=None)

		if(url.sprint == None or url.sprint == "" or url.command == None):
			return render.index(None, None,
			    """<br>
			    Howdy!
	    		In the input fields above please enter the sprint ID you are interested in, use YWW (year + week number) format. <br>
	    		For example '211' will show the sprint that ends in week 11 year 2012.<br>
	    		<br>""")
		else:
			sprint = Sprint(url.sprint)
			if sprint.okToGo == False:
				return render.index(url.sprint,  None, 
					"""<br>
	    			There was a problem getting information on the sprint, there could be db connection issue<br>
	    			<br>""")
			   
			# do the requested work
			if url.command == 'plotburn':
				res = sprint.plotBurnDownChart()
				return render.burndown(url.sprint)
			elif url.command == 'ploteffort':
				res = sprint.plotEffortBarsChart()
				return render.burndown(url.sprint)
			elif url.command == 'plotbar':
				res = sprint.plotEffortStackedBarChart()
				return render.burndown(url.sprint)
			elif url.command == 'issuesstatus':
				res = sprint.printIssuesPerStatus()
			elif url.command == 'allissues' or url.command == 'issues':
				rows = sprint.getIssues("All")
				return render.issueslist(url.sprint, "All", rows)
			elif url.command == 'doneissues':
				rows = sprint.getIssues("Done")
				return render.issueslist(url.sprint, "Done", rows)
			elif url.command == 'openissues':
				rows = sprint.getIssues("Open")
				return render.issueslist(url.sprint, "Open", rows)
			elif url.command == 'effortsummary':
				res = sprint.printEffortSummary()

			return render.index(url.sprint, url.command, """<br>Job done!<br>""")
class query:
	def POST(self):
		i = web.input()
		if i.sprint == "":
			# TODO display an info that sprint ID must be provided
			pass # just 		
		# just redirect to main page with query parameters to show what's requested
		uStr = u'/?sprint=' + i.sprint + '&command=' + i.command
		raise web.seeother(uStr)


if __name__ == "__main__": app.run()