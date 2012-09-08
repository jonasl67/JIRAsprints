"""
    Settings for the JIRA DB used
"""

PROGVERSION = "0.1"
PROGNAME = "jirasprints"

# DB settings

# local host DB
sDBServerAddress = "127.0.0.1"
#sDBUser = "jira"
#sDBUserPassword = "jira"
#sDBName = "jiradb"

# Production DB
#sDBServerAddress = "192.168.0.40"
sDBUser = "jirareader"
sDBUserPassword = "donaldduck"
sDBName = "jiradb"

# JIRA issue status values
iStatOpen = 1
iStatNew = 10000
iStatAssigned = 10001
iStatIntegrated = 10003
iStatImplemented = 10002
iStatVerified = 10004
iStatRejected = 10005
iStatInProgress = 3
iStatOnHold = 10006
iStatReOpened = 4
iStatResolved = 5
iStatClosed = 6
iStatPlanned = 10007

# JIRA custom field's IDs
iFieldSprintID = 10032
iFieldDevEffort = 10033

# first 3 digits of years for sprints
yyy = "201"

# length of sprints in days, including weekend days
sprintDays = 12

# path where to put images generated
sImagePath = "./static/"