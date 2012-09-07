#!/usr/bin/env python
# -*- coding: utf-8 -*-

#-- stdlib imports
import config as cfg
import logging
from datetime import date, timedelta, datetime

#-- third party import
import numpy as np
import matplotlib.pyplot as plt

#-- project imports
from JIRAdb import JIRAdb

class Sprint():
    """
        Class that represents a sprint
    """

    # class/static vars 
    
    def __init__(self, sWeek):
        """
            sWeek = yww, the year and week no of the sprint
        """

        # initilize sprint
        self.okToGo = False
        if None == sWeek or sWeek == '' or sWeek.isnumeric() == False:
            logging.critical("Attempt to create sprint with invalid name, not YWW")
            return None
        self.sEndWeek = sWeek
        self.noOfDays = cfg.sprintDays
        self.sprintDays = self.__setSprintDays()
        self.okToGo = True
        
        # sprint data source
        self.db = JIRAdb()
        if None == self.db.db:
            logging.critical("No DB available for sprint data")
            self.okToGo = False
            return None
    def __calcBurnDownPlots(self, fMaxVal, noOfValues):
        """
            Return a list with values that will plot a straight line
            -fMaxVal, the max value to start plot from
            -noOfValues, the number of values required in the list
        """
        step = fMaxVal/(noOfValues-1)
        values = []
        i=0
        while i < noOfValues:
            values.append(fMaxVal-step*i)
            i=i+1
        return values
    def __calcDoneEffortForDay(self, aDate, doneIssues):
        """
            Return the effort that was done at end of aDate 
            aDate - a date within the sprint
            doneIssues - list of issues that's currently in status Implemented or further
        """
        
        doneEffort = 0
        for issue in doneIssues:
            if aDate >= issue[2]: # get the datetime
                #print "%10s effort %.2f was done %s" % (issue[0], issue[1], issue[2])
                doneEffort = doneEffort + issue[1]
        
        #print "Total effort done by %s is %.2f" % (aDate, doneEffort)
        return doneEffort
    def __dateAddGenerator(self, startDate, len):
        """
            Generate dates starting with the startDate
        """
        date = startDate
        list = range(len)
        for i in list:
            yield date
            date = date + timedelta(days=1)
    def __setSprintDays(self):
        """
            Return a list of all dates in the sprint
        """
        
        # create a list of strings with dates of the sprint
        startDate = self.firstDateOfSprint(cfg.sprintDays)
        gen = self.__dateAddGenerator(startDate, cfg.sprintDays)
       
        sprintDays = []
        for i in gen:
            sprintDays.append(i)
        return sprintDays
    def getDoneIssues(self):
        """
            Returns a list of all done issues for the sprint
        """
        return self.db.getDoneDateForIssuesForSprint(self.sEndWeek)
    def getIssues(self, status):
        """
            status = string with Done/Open/All to print the issues with this status
            Returns a list with issueID/issueDescription/issueStatus/devEffort
        """
        
        if status != "Done" and status != "Open" and  status != "All":
            logging.error("Printing issue with status %s not supported, will not print anything." % status)
            return None
        return self.db.getIssuesForSprint(self.sEndWeek, status)
    def firstDateOfSprint(self, iNoOfDays):
        """
            Return the first date of the sprint
            Sprints are assumed to end on Fridays
        """
        year = int(cfg.yyy + self.sEndWeek[0])
        week = int(self.sEndWeek[1:])
        startDate = datetime.strptime('%04d-%02d-1 %d:%d:%d' % (year, week, 23, 59, 59), '%Y-%W-%w %H:%M:%S')
        # first Thursday  
        if date(year, 1, 4).isoweekday() > 4:
            startDate -= timedelta(days=7)
        
        # calc first day 
        if iNoOfDays > 5:
            startDate = startDate - timedelta(iNoOfDays-5)
        
        logging.debug("First date of sprint is calculated to: %s" % (startDate))
        return startDate
    def plotBurnDownChart(self):
        """
            Create a burndown chart of the requested sprint
        """   

        #issues = self.db.getDoneIssuesForSprint(self.sEndWeek)
     
        fig = plt.figure()
        fig.subplots_adjust(bottom=0.2)
        ax = fig.add_subplot(111)
        ax.grid(True)
        now = datetime.now()
        time = now.strftime("%Y-%m-%d %H:%M")
        ax.set_title('Burndown of sprint %s @ %s' % (self.sEndWeek, time) )
        
        # y axis labels
        plt.ylabel('Man days effort')

        # x axis labels
        xLabels = []
        for i in self.sprintDays:
            xLabels.append(i.strftime("%y-%m-%d %a"))
        plt.xticks(np.arange(self.noOfDays), xLabels, rotation=45, size='small', ha='right')
        
        # plot ideal burn down line, straight line from total effort to 0
        fTotalEffort = self.db.getTotalEffortForSprint(self.sEndWeek)
        if fTotalEffort > 0:
            pIdeal = plt.plot(self.__calcBurnDownPlots(fTotalEffort, self.noOfDays),linewidth=2, marker='o')
        else:
            pIdeal = [0]
            
        # plot actual burn down
        # create the values for each day in sprint
        xValues = []
        doneEffort = 0
        i=0
        today = datetime.today().date()
        doneIssues = self.getDoneIssues()
        while i < self.noOfDays:
            # only plot up to current date so we don't get long horizontal line for remaining days of sprint
            if today >= self.sprintDays[i].date():
                doneEffort = self.__calcDoneEffortForDay(self.sprintDays[i], doneIssues)
                xValues.append(fTotalEffort - doneEffort) # effort left for each day
            i=i+1
        pActual = plt.plot(xValues, color='g', linewidth=2, marker='o')
        
        ax.legend([pIdeal[0], pActual[0]], ["Ideal", "Actual"])
        #plt.show()
        plt.savefig('%s%s%s.png' % (cfg.sImagePath, "BurndownSprint", self.sEndWeek))
    def plotEffortBarsChart(self):

        fSumEffort = self.db.getTotalEffortForSprint(self.sEndWeek)
        fSumDoneEffort = self.db.getDoneEffortForSprint(self.sEndWeek)
        fSumEffortLeft = self.db.getOpenEffortForSprint(self.sEndWeek)

        # create bar chart for effort
        ind = np.arange(3)  # the x locations for the groups
        width = 0.5       # the width of the bars

        # tuple with floats for bars
        effortBars = (round(fSumEffort, 2), round(fSumDoneEffort, 2), round(fSumEffortLeft, 2) )
        fig = plt.figure()
        
        # make some space above highest bar
        maxheight = round(fSumEffort, 2)
        plt.ylim(ymax=maxheight+(maxheight*0.1))
        
        # create bars plot
        ax = fig.add_subplot(111)  # 1 row, 1 column, first plot
        bars = ax.bar(ind, effortBars, width, color=('b', 'g', 'r'), align = 'center')
        
        # labels & legend
        ax.set_ylabel('Effort man days')
        ax.set_title('Man days effort for sprint %s' % self.sEndWeek)
        ax.set_xticks(ind)
        ax.set_xticklabels( ('Planned\neffort', 'Effort\ndone', 'Effort\nleft',) )
        
        # print values on top of bars
        def autolabel(rects):
            # attach some text labels
            for rect in rects:
                height = rect.get_height()
                ax.text(rect.get_x()+rect.get_width()/2.,
                    height+1,
                    '%d'%int(height),
                    ha='center', va='bottom')

        autolabel(bars)
        
        #plt.show()
        plt.savefig('%s%s%s.png' % (cfg.sImagePath, "EffortSprint", self.sEndWeek))
    def plotEffortStackedBarChart(self):

        fSumDoneEffort = self.db.getDoneEffortForSprint(self.sEndWeek)
        fSumEffortLeft = self.db.getOpenEffortForSprint(self.sEndWeek)
        
        # create stacked bar chart for effort
        ind = np.arange(1)  # the x locations for the groups
        width = 0.1       # the width of the bars
        
        # make some space above bar
        maxheight = round(fSumDoneEffort+fSumEffortLeft,2) 
        plt.ylim(ymax=maxheight+(maxheight*0.1))
        
        # create bar
        b1 = plt.bar(ind, round(fSumDoneEffort, 2), width, color='g', align = 'center')
        b2 = plt.bar(ind, round(fSumEffortLeft, 2), width, color='r', align = 'center', bottom=round(fSumDoneEffort, 2))
        
        # labels & legend
        plt.legend( (b1[0], b2[0]), ('Effort done', 'Effort left') )
        
        #plt.show()
        plt.savefig('%s%s%s.png' % (cfg.sImagePath, "EffortStackSprint", self.sEndWeek))
    def printEffortSummary(self):
        """
            Print a text summary of total, done and open effort for the sprint
        """
        
        fTotalEffort = self.db.getTotalEffortForSprint(self.sEndWeek)
        fDoneEffort = self.db.getDoneEffortForSprint(self.sEndWeek)
        fOpenEffort = self.db.getOpenEffortForSprint(self.sEndWeek)
        
        print "Total effort is: %.2f" % fTotalEffort
        print "Done effort is.: %.2f" % fDoneEffort
        print "Open effort is.: %.2f" % fOpenEffort
    def printIssues(self, status):
        """
            status = string with Done/Open/All to print the issues with this status
            Returns a list with issueID/issueDescription/issueStatus/devEffort
        """
        
        if status != "Done" and status != "Open" and  status != "All":
            logging.error("Printing issue with status %s not supported, will not print anything." % status)
            return None
        results = self.db.getIssuesForSprint(self.sEndWeek, status)
        print "%s issues for sprint %s:" % (status, self.sEndWeek)
        nSumEffort = 0
        for row in results:
            sExtIssueID = row[0]
            sDescription = row[1]
            sStatus = row[2]
            nEffort = row[3]
            sAssignee = row[4]
            nSumEffort = nSumEffort + nEffort
            # Now print fetched result
            print "%-10.10s %-80.80s %-12.12s %.2f %-15.15s" % \
                (sExtIssueID, sDescription, sStatus, nEffort, sAssignee )
    def printIssuesPerStatus(self):
        self.printIssues("Done")
        self.printIssues("Open")
