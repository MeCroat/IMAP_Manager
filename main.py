import base64
import datetime as dt
import email
import imaplib
import os
import quopri
import re
import sys
from tkinter import *

import pytz

#################################################
# BEGIN CLASS DEFINITIONS                       #
#################################################

#   Logger: used to maintain file containing the list of log messages
class Logger(object):

    STATE_NULL: int          = 0
    STATE_ACTIVE: int        = 1
    STATE_PAUSED: int         = 2
    STATE_FILE_OPEN_ERROR: int  = 3
    STATE_LOG_OPEN_FAIL: int = 4

    state_messages = {STATE_NULL: 'NULL', STATE_ACTIVE: 'ACTIVE', STATE_PAUSED: 'PAUSED',
                      STATE_FILE_OPEN_ERROR: 'FILE OPEN ERROR', STATE_LOG_OPEN_FAIL: 'LOG FILE OPEN FAILURE'}

    init_success: bool       = False
    last_error_message       =  ""

    MSG_FILE_OPEN_ERROR = "LOG_FILE_OPEN_ERROR"

    def __init__(self, file_name="./IMAP_LOG_FILE"):
        #
        self.file_name=file_name
        self.state=Logger.STATE_NULL
        self.last_error_message=""

        try:
            fh = open( self.file_name, "a")
            fh.close()
            self.state=Logger.STATE_ACTIVE

        except IOError as e:
            self.state=Logger.STATE_FILE_OPEN_ERROR
            self.last_error_message=str(e)
    def __repr_(self):
        print ('{} - {} - {}'.format(self.file_name, self.state_messages[self.state], self.last_error_message )

    def __str__(self):
        print('{}'.format(self.file_name))

    def __delete__(self):
        pass

    def is_active(self)->bool:
        return self.state==Logger.STATE_ACTIVE

    def is_inactive(self):
        return not self.state==Logger.STATE_ACTIVE

    def get_error_messsage_text(self):
        return self.last_error_message
        pass

    def pause_logger(self):
        self.state = Logger.STATE_PAUSED

    def log_it(self, log_strs: list)-> bool:
        return_value = True
        if self.state == Logger.STATE_ACTIVE :
            try:
                fh = open( self.file_name, "a")
                fh.writelines(log_strs)
                fh.close()
            except IOError as e:
                self.state = Logger.STATE_FILE_OPEN_ERROR
                self.last_error_message = str(e)
        elif self.state == Logger.STATE_PAUSED:
            return_value = True
        else:
            return_value = False
            self.last_error_message = "Logger is not Active"

        return return_value

#################################################
# END CLASS DEFINITIONS                         #
#################################################
user        = "xxxx@yyy.com" # subject email address
password    = "password" # subject email address password
imap_url    = "mbox.server289.com" # url of the IMAP server

MAX_EMAILS_TO_SCAN = 50 # Maximum number of email to scan, Used of no 'limit' is
                        # specified on the command line
#
# Local Files
date_file       = str("./MailFileDate.txt")  # Date of last execution of the program
blacklist_file  = "BlackList.txt" # list of email addresses that are blacklisted
blacklist       = list()
whitelist_file  = "WhiteList.txt" # List if emailaddresses that are whitelisted
whitelist       = list()
newest_file     = "NewestSendersToConsider.txt"
newlist         = list()

num_emails_to_scan  = MAX_EMAILS_TO_SCAN

ids_with_extra_data = dict()

def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(name)# Press Ctrl+F8 to toggle the breakpoint.

def log_message( the_logger: Logger, message: str):

    d = get_date_time()
    out_str = [d[0] + "." + d[1] + " " + message + '\n']

    if (the_logger.log_it( out_str) == FALSE):
        print ("Unable to log ", out_str)

def get_date_time( ) -> []:

    date_time = dt.datetime.now()
    current_time = date_time.now( pytz.timezone( 'America/Chicago' ) )
    temp1 = current_time.__str__()
    temp1 = temp1.replace( '-', '' )
    temp1 = temp1.replace( ':', '' )
    formatted_date = temp1[0:8]
    formatted_time = temp1[9:15]
    return [formatted_date, formatted_time]

def check_if_work_needed (filename: str, yesterdayDate: dt.date ) -> (bool, str) :
#
#   Find out if we have alread done this today.
#   Currently not used
#
    date = ""
    result = True
    # if date file nt present, create it and populate with
    # yesterday's date
    if (not os.path.isfile(filename)):
        date = today - dt.timedelta(days=1)
    else :
        fh = open(date_file, "r")
        date = fh.read()
        fh.close()

    return result, date

def get_command_line_params(clin) -> (bool, str, str, str, int):
#
#   There are 4 command line params:
#
#   Param 1: action=<scan|purge>
#       - scan
#           Scan the latest emails for items not on whitelist or blacklist
#       OR
#       - purge
#           Purge (permanently delete) recent emails in blacklist
#   Param 2: limit=<number>
#       A number expressing the
#       limit of emails to scan or check for deletion
#
#   Param 3: email_address=<email address>
#       A valid email address which is the account to be addressed
#
#   Param 4: password=<password>
#       Password for the email account expressed in paramater 3 above.
#
#   Example Command Line:
#       > python.exe main.py  email_address=xx@yyy.com password=$$password action=scan limit=50
#
    result = True
    ac = ""
    lim = 0
    email_address = ""
    password = ""

    fatal_errors=0
    for i in clin:

        s = i.split("=")
        if s[0] == "action":
            if s[1] == "scan" or s[1] == "purge":
                ac = s[1]
            else:
                log_message( my_logger, "invalid action" + s[1] + " specified on the command line")
                fatal_errors+=1
        elif (s[0] == "limit"):
            if s[1].isdigit():
                lim = int(s[1])
            else:
                log_message(my_logger, "limit " + s[1] + " is not a number.")
                fatal_errors+=1
        elif s[0] == "email_address":
            email_regex = re.compile(r"[^@]+@[^@]+\.[^@]+")
            if email_regex.match(s[1]):
                email_address = s[1]
            else:
                log_message( my_logger, "Invalid Email Address " + s[1])
                fatal_errors+=1
            pass
        elif s[0] == 'password':
            if len(password) == 0:
                password = s[1]
            pass

    if (len(ac) == 0):
        log_message( my_logger, "required command line parameter action is missing or invalid")
        fatal_errors+=1
    if len(email_address) == 0:
        log_message( my_logger, "required command line parameter email_address is missing or invalid")
        fatal_errors+=1
    if len(password) == 0:
        log_message( my_logger, "required command line parameter password is missing or invalid")
        fatal_errors+=1

    if (fatal_errors > 0):
        sys.exit()

    return result, ac, email_address, password, lim

def get_blacklist_file(file_name:str) -> (bool, list):
#
# open and read the file of emails that should be deleted
#
    result = True
    str_list = list()
    if os.path.isfile(file_name):
        fh = open(file_name,"r")
        str_list = fh.readlines()
        fh.close()
    else :
        # create the blacklist file
        fh = open(file_name, "w")
        fh.close()

    contents = [n.rstrip('\n') for n in str_list]

    return result, contents

def get_newest_sender_file(file_name:str, append:bool = FALSE) -> (bool, list):
#
# open and read the file of emails that should be deleted
#
    result = True
    str_list = []
    if os.path.isfile(file_name) :
        fh = open(file_name,"r")
        str_list = fh.readlines()
        fh.close()
    else :
        # create the newest sender file
        fh = open(file_name, "w")
        fh.close()

    contents = []

    if (append == TRUE):
        contents = [i.rstrip('\n') for i in str_list]

    return result, contents


def get_whitelist_file(file_name:str) ->(bool, list):
#
# open and read the file of emails that should be allowed
#
    result = True
    str_list = []
    if os.path.isfile(file_name) :
        fh = open(file_name,"r")
        str_list = fh.readlines()
        fh.close()
    else :
        # create the whitelist file
        fh = open(file_name,"w")
        fh.close()

    contents = [i.rstrip('\n') for i in str_list]

    return result, contents

def encoded_words_to_text(encoded_words):

    # Decode words that are encoded by IMAP. Frequently this is done for Subject Lines
    encoded_word_regex = r'(.*)=\?{1}(.+)\?{1}([B|Q|b|q])\?{1}(.+)\?{1}=(.*)'
    pre_text, charset, encoding, encoded_text, post_text = re.match(encoded_word_regex, encoded_words).groups()
    if encoding == 'B' or encoding == 'b':
        byte_string = base64.b64decode(encoded_text)
    elif encoding == 'Q' or encoding == 'q':
        byte_string = quopri.decodestring(encoded_text)
    return pre_text + byte_string.decode(charset) + post_text

#########################################################
########## M A I N ######################################
#########################################################
def main():
    pass

if __name__ == '__main__':
    main()
#
# Construct log file name from current date
d = get_date_time()
log_file_name = d[0] + "_" + d[1] + ".log"

my_logger = Logger(log_file_name)

if my_logger.is_inactive():
    print("unable to start logger: " + my_logger.last_error_message)
    sys.exit()

temp = ""

__argc = len(sys.argv)

for i in range(0, __argc):
    temp = temp + " " + sys.argv[i]


result, action, user, password,  num_emails_to_scan = get_command_line_params(sys.argv)

log_message( my_logger, "Command line " +  temp)

action = action.lower()
today = dt.date.today()

result1 = True

if (action == "scan"):
    result1, date_fileDate = check_if_work_needed(date_file, today)

if result1:
    pass
else:
    if (action == "scan"):
        log_message( my_logger, "Date file Not Found")
        sys.exit()

# open the delete file
result, blacklist = get_blacklist_file(blacklist_file)

if result:
    result, whitelist = get_whitelist_file(whitelist_file)
    if result:
        result, newlist = get_newest_sender_file( newest_file, FALSE )
        if result :
            pass
        else:
            print( "No new file" )
            sys.exit()
    else:
        print ( "No whitelist file")
        sys.exit()
else:
    print ("No blacklist file")
    sys.exit()
mail = imaplib.IMAP4_SSL("mbox.server289.com", 993)

result, folders =  mail.login(user, password)

#print (mail.list())

if result != 'OK':
    log_message( my_logger, "No mail folders, no login!")
    sys.exit()

if (action == 'scan'):
    result, data = mail.select("inbox", readonly=True)
    #result, data = mail.select("inbox")
else:
    result, data = mail.select("inbox")

#result, dataX = mail.uid('search', None, 'ALL')
if result == "OK":
    result, dataX = mail.uid('search', None, 'ALL')

if result != "OK":
    log_message( my_logger, "InBox is empty!")
    sys.exit()

scan_count = num_emails_to_scan

if (action == 'scan'):

    ref = dataX[0].split()
    # collect the email: From Subject and internal unique identifier (uid)

    for endo in range(-1,0-scan_count-1,-1):

        num = ref[endo]
        result, dataY = mail.uid('fetch', num, '(RFC822)')
        from_address = ""
        subject = ""

        if result == "OK":

            email_message = email.message_from_bytes(dataY[0][1])
            subject = email_message['Subject']
            from_party = email_message['From']
            return_party = email_message['Return-Path']
            s = subject.split( "\n" )

            for str in s:
                str = str.replace("\r", "")
                if "=?utf-" in str.lower():
                    subject += encoded_words_to_text(str)
                else:
                    subject += str
            # kick out the extraneous characters
            m = re.search('<.+>', from_party)
            if m is not None:
                from_address = m.group(0)
                from_address = from_address.replace('<', '')
                from_address = from_address.replace('>', '')
            else:
                from_address = from_party
            m = re.search( '<.+>', return_party )
            if m is not None:
                return_path = m.group( 0 )
                return_path = return_path.replace( '<', '' )
                return_path = return_path.replace( '>', '' )
            else:
                return_path = return_party
            dlist = ["","",1,""]
            if len(from_address) > 0:
                # add to Ids
                # create the list of data = from address, subject, count
                dlist[0] = from_address
                dlist[1] = subject
                dlist[2] = 1
                dlist[3]= return_path
                d = {num:dlist}
                ids_with_extra_data.update(d)

    mail.close()
    mail.logout()

    done = False
    while not done:
        result = ""
        for n in ids_with_extra_data.items():
            return_path = n[1][3]
            from_address = n[1][0]
            subject = n[1][1]
            if from_address in blacklist:
                log_message( my_logger, "Skip " + from_address + ": in blacklist")
                continue
            if return_path in blacklist:
                log_message( my_logger, "Skip " + return_path + ": in blacklist")
                continue
            if from_address in whitelist:
                log_message( my_logger, "Skip " + from_address + ": in whitelist")
                continue
            if return_path in whitelist:
                log_message( my_logger, "Skip " + return_path + ": in whitelist")
                continue
            else:
                while (True ):
                    if action == "scan":
                        result = input("\nFrom: " +  from_address + "\nSubject: " + subject + "\n[b]lacklist,[w]hitelist,[s]kip,[r]eset,[q]uit: default=s?")
                    else:
                        result = "s"
                        break
                    if  result == "" or result == "s":
                        log_message( my_logger, "message from " + from_address + " manually skipped.")
                        break
                    if result == "b":
                        if from_address not in blacklist:
                            blacklist.append(from_address)
                            log_message( my_logger,  "from address " + from_address + " blacklisted." )
                            if from_address not in newlist:
                                newlist.append( '(f) - ' + from_address)
                        if return_path not in blacklist:
                            blacklist.append(return_path)
                            if return_path not in newlist :
                                newlist.append('(r) - ' +  return_path)
                            log_message( my_logger,  "return path " + return_path + " blacklisted." )
                        break
                    elif result == 'w':
                        if from_address not in whitelist:
                            whitelist.append(from_address)
                            log_message( my_logger,  "from address " + from_address + " whitelisted." )
                        if return_path not in whitelist:
                            whitelist.append(return_path)
                            log_message( my_logger,  "from address " + return_path + " whitelisted." )
                        break
                    elif result == "r":
                        log_message( my_logger, "user requested resetting scan loop.")
                        break
                    elif result == "q":
                        log_message( my_logger, "Operator Abort")
                        sys.exit()
                    else:
                        continue
            if (result == "r" ):
                break
        if (result != "r"):
            done = True

    if result == "q":
        sys.exit('Operator Abort')

    blacklist.sort(key = lambda x: x.lower())

    fd = open(blacklist_file, "w")
    for n in blacklist:
        fd.write(str(n) + "\n")
    fd.close()

    whitelist.sort(key = lambda x: x.lower())

    fd = open(whitelist_file, "w")

    for n in whitelist:
        fd.write(str(n) + "\n")
    fd.close()

    newlist.sort(key = lambda x: x.lower())

    fd = open(newest_file, "a")

    d = get_date_time()
    fd.write('\n*** ' + d[0] + ' ' + d[1] + ' *** \n\n')

    for n in newlist:
        s = n.replace("<", "")
        s = s.replace(">", "")
        fd.write(str(s) + "\n")
    fd.close()

elif (action == "purge"):
    ref = dataX[0].split()
    for i in range( -1, 0-num_emails_to_scan-1, -1):
        num = ref[i]
        result, dataY = mail.uid( 'fetch', num, '(RFC822)' )
        if result == "OK":
            from_address = ""
            email_message = email.message_from_bytes(dataY[0][1])
            from_party = email_message['From']
            subject = email_message['Subject']
            s = subject.split( "\n" )
            subject = ""
            for str in s:
                str = str.replace("\r", "")
                if "=?utf-" in str.lower():
                    subject += encoded_words_to_text(str)
                else:
                    subject += str
            m = re.search('<.+>', from_party)
            if m == None:
                from_address = from_party
            else:
                from_address = m.group(0)
                from_address = from_address.replace('<', '')
                from_address = from_address.replace('>', '')

            if from_address in blacklist:
                log_message( my_logger,  "Purging: " + str(from_address) + " : " + subject + " : " + str(num) )
                _ , msg = mail.uid('fetch', num, "(RFC822)")
                try:
                  mail.uid('STORE', num, '+FLAGS', '\\DELETED')
                except Exception as e:
                    log_message( my_logger, "Mail store (delete) error for UID " + str(num) + " From: " + from_address + " Subject : " + subject + "... Skipping")
            else:
                try:
                    mail.uid('STORE', num, '-FLAGS', '\\SEEN')
                except Exception as e:
                    #print ("Error {0} ".format(e))
                    log_message( my_logger,  "Mail store (unread) error for UID " + str(num) + " From: " + from_address + " Subject : " + subject + "... Skipping")
        else:
            log_message( my_logger, "Failed to fetch mail for UID " + str(num))

    mail.expunge()
    mail.close()
    mail.logout()

elif action == "test":
    pass

