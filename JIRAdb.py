#!/usr/bin/env python
# -*- coding: utf-8 -*-

#-- stdlib imports
import config as cfg
import logging
from datetime import date, timedelta, datetime

#-- third party import
import MySQLdb

class JIRAdb():
    """
        Class that represents the JIRA db used to keep all information on issues and sprints
    """
    # class/static vars 
    db = None
    cursor = None
    def __init__(self):
        db = self.__openDB()
        if None == db:
            return None
    def __closeDB(self, db):
           
        # disconnect from server
        db.close()
    def __openDB(self):
        """
            Open the database and return the handle to it, or None if failing
        """
        
        # Open database connection
        try:
            logging.info("Connecting to database: %s at: %s\n" % (cfg.sDBName, cfg.sDBServerAddress))
            self.db = MySQLdb.connect(cfg.sDBServerAddress, cfg.sDBUser, cfg.sDBUserPassword, cfg.sDBName)
        except:
            logging.critical("Cannot connect to database: %s at: %s\n" % (cfg.sDBName, cfg.sDBServerAddress))
            return None

        # prepare a cursor object using cursor() method
        self.cursor = self.db.cursor()
        
        # set the DB to use
        try:
            self.cursor.execute("USE %s" % cfg.sDBName)
        except:
            logging.critical("Cannot USE database: %s at: %s\n" % (cfg.sDBName, cfg.sDBServerAddress))
            return None

        return self.db
    def getDoneDateForIssuesForSprint(self, sReqSprint):
        """
            Returns a list of all done issues for the sprint, each done issue comes with
                -issueID
                -effort
                -string with date and time when the issue was put to implemented
        """
        
        # Prepare SQL query to get done issues for the specified sprint
        sql = """select pkey, NUMBERVALUE from customfieldvalue, jiraissue \
            JOIN issuestatus ON jiraissue.issuestatus = issuestatus.ID \
            where ISSUE IN \
                (select ISSUE from customfieldvalue where CUSTOMFIELD = %d AND STRINGVALUE = %s) \
            AND customfield = %d AND customfieldvalue.ISSUE = jiraissue.ID \
            AND (issuestatus = %d OR issuestatus = %d OR issuestatus = %d OR issuestatus = %d) \
            order by pkey;""" % (cfg.iFieldSprintID, sReqSprint, cfg.iFieldDevEffort, \
                cfg.iStatIntegrated, cfg.iStatImplemented, cfg.iStatVerified, cfg.iStatRejected)

        try:
            # Execute the SQL command
            self.cursor.execute(sql)
            # Fetch all the rows in a list of lists.
            results = self.cursor.fetchall()
            list = []
            for row in results:
                sExtIssueID = row[0]
                nEffort = round(row[1],2)
                
                # get the date when it was done (implemented status)
                sql = """select created from changegroup \
                    join changeitem on changegroup.id = changeitem.groupid \
                    where issueid = (select ID from jiraissue where pkey = "%s") AND \
                    field = "status" AND NEWVALUE = %d""" % (sExtIssueID, cfg.iStatImplemented);
                try:
                    # Execute the SQL command
                    self.cursor.execute(sql)
                    # Fetch all the rows in a list of lists.
                    date = self.cursor.fetchone()
                    # if issue was rejected there is no done state transition, and assume no effort TODO: should effort be the original?
                    if None == date:
                        date = (datetime.today(), 0) # tuple since that's what we get from mysql
                        nEffort = 0
                except:
                    # not much sensible to do, use today's date
                    logging.error("Failed to find date when %s was put to status implemented, using today as the date" % (sExtIssue))
                    date = (datetime.today(), 0)
                list.append([sExtIssueID, nEffort, date[0]])
            return list
        except:
           logging.error("Unable to fecth done issues for sprint %s" % sReqSprint)   
           return []
    def getDoneEffortForSprint(self, sReqSprint):
        """
            Return float with effort done so far for the sprint, negative if there is none or there is a problem
        """

        # Prepare SQL query to get done issues for the specified sprint
        sql = """select SUM(NUMBERVALUE) AS DoneEffort from customfieldvalue, jiraissue \
            JOIN issuestatus ON jiraissue.issuestatus = issuestatus.ID \
            where ISSUE IN \
                (select ISSUE from customfieldvalue where CUSTOMFIELD = %d AND STRINGVALUE = %s) \
            AND customfield = %d AND customfieldvalue.ISSUE = jiraissue.ID \
            AND (issuestatus = %d OR issuestatus = %d OR issuestatus = %d OR issuestatus = %d)""" \
            % (cfg.iFieldSprintID, sReqSprint, cfg.iFieldDevEffort, \
                cfg.iStatIntegrated, cfg.iStatImplemented, cfg.iStatVerified, cfg.iStatRejected)

        try:
            # Execute the SQL command
            self.cursor.execute(sql)
            # get the total effort
            nDoneEffort = self.cursor.fetchone()
            if nDoneEffort[0] is None: nDoneEffort = (0.0, 0.0)
        except:
           logging.error("Error: unable to fecth done issues for sprint %s" % sReqSprint)
           return -1
        
        return round(nDoneEffort[0], 2)
    def getIssuesForSprint(self, sReqSprint, issueState):
        """
            issueStatus == "Done" | "Open" | "All"
        """
        
        # Prepare SQL query to get done issues for the specified sprint
        if issueState == "Done":
            sql = """select pkey, SUMMARY, pname, NUMBERVALUE, assignee from customfieldvalue, jiraissue \
                JOIN issuestatus ON jiraissue.issuestatus = issuestatus.ID \
                where ISSUE IN \
                    (select ISSUE from customfieldvalue where CUSTOMFIELD = %d AND STRINGVALUE = %s) \
                AND customfield = %d AND customfieldvalue.ISSUE = jiraissue.ID \
                AND (issuestatus = %d OR issuestatus = %d OR issuestatus = %d OR issuestatus = %d) \
                order by pkey;""" % (cfg.iFieldSprintID, sReqSprint, cfg.iFieldDevEffort, \
                    cfg.iStatIntegrated, cfg.iStatImplemented, cfg.iStatVerified, cfg.iStatRejected)
        elif issueState == "Open":
            sql = """select pkey, SUMMARY, pname, NUMBERVALUE, assignee from customfieldvalue, jiraissue \
                JOIN issuestatus ON jiraissue.issuestatus = issuestatus.ID \
                where ISSUE IN \
                    (select ISSUE from customfieldvalue where CUSTOMFIELD = %d AND STRINGVALUE = %s) \
                AND customfield = %d AND customfieldvalue.ISSUE = jiraissue.ID \
                AND (issuestatus = %d OR issuestatus = %d OR issuestatus = %d OR issuestatus = %d OR issuestatus = %d OR issuestatus = %d) \
                order by pkey;""" % (cfg.iFieldSprintID, sReqSprint, cfg.iFieldDevEffort, cfg.iStatNew, cfg.iStatAssigned, 
                cfg.iStatInProgress, cfg.iStatOnHold, cfg.iStatReOpened, cfg.iStatPlanned)
        elif issueState == "All":
            sql = """select pkey, SUMMARY, pname, NUMBERVALUE, assignee from customfieldvalue, jiraissue \
                JOIN issuestatus ON jiraissue.issuestatus = issuestatus.ID \
                where ISSUE IN \
                    (select ISSUE from customfieldvalue where CUSTOMFIELD = %d AND STRINGVALUE = %s) \
                AND customfield = %d AND customfieldvalue.ISSUE = jiraissue.ID \
                order by pkey;""" % (cfg.iFieldSprintID, sReqSprint, cfg.iFieldDevEffort)
                
        try:
           # Execute the SQL command
           self.cursor.execute(sql)
           results = self.cursor.fetchall()
           list = []
           for row in results:
              sExtIssueID = row[0]
              sDescription = row[1]
              sStatus = row[2]
              nEffort = row[3]
              sAssignee = row[4]
              iEffort = "%.2f" % nEffort
              list.append([sExtIssueID, sDescription, sStatus, iEffort, sAssignee])
        except:
           logging.error("Error: unable to fetch issues for sprint %s" % sReqSprint)
           return []
        return list
    def getOpenEffortForSprint(self, sReqSprint):
        """
            Return float with effort left/open for the sprint, negative if there is none or there is a problem
        """
        
        # Prepare SQL query to get open issues for the specified sprint
        sql = """select SUM(NUMBERVALUE) AS nOpenEffort from customfieldvalue, jiraissue \
            JOIN issuestatus ON jiraissue.issuestatus = issuestatus.ID \
            where ISSUE IN \
                (select ISSUE from customfieldvalue where CUSTOMFIELD = %d AND STRINGVALUE = %s) \
            AND customfield = %d AND customfieldvalue.ISSUE = jiraissue.ID \
            AND (issuestatus = %d OR issuestatus = %d OR issuestatus = %d OR issuestatus = %d OR issuestatus = %d OR issuestatus = %d)""" \
            % (cfg.iFieldSprintID, sReqSprint, cfg.iFieldDevEffort, cfg.iStatNew, cfg.iStatAssigned, 
                cfg.iStatInProgress, cfg.iStatOnHold, cfg.iStatReOpened, cfg.iStatPlanned)
        
        try:
            # Execute the SQL command
            self.cursor.execute(sql)
            # get the total effort
            nOpenEffort = self.cursor.fetchone()
            if nOpenEffort[0] is None: nOpenEffort = (0.0, 0.0)
        except:
           logging.error("Error: unable to fetch open issues for sprint %s" % sReqSprint)
           return -1
       
        return round(nOpenEffort[0], 2)
    def getTotalEffortForSprint(self, sReqSprint):
        """
            Return float with total effort estimated for the sprint, negative if there is a problem
        """
        
        # get the total effort estimated for the sprint
        sql = """select SUM(NUMBERVALUE) AS EffortTotal from customfieldvalue \
            where ISSUE IN (select ISSUE from customfieldvalue where CUSTOMFIELD = %d AND STRINGVALUE = %s) AND customfield = %d;""" \
            % (cfg.iFieldSprintID, sReqSprint, cfg.iFieldDevEffort)
        
        try:
            # Execute the SQL command
            self.cursor.execute(sql)
            # get the total effort
            nTotalEffort = self.cursor.fetchone()
            if nTotalEffort[0] is None: nTotalEffort = (0.0, 0.0)
        except:
            logging.error("Error: unable to fecth/calculate total effort for the sprint")
            return -1
        
        return round(nTotalEffort[0], 2)
