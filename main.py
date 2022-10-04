import imaplib
import email
import time
import datetime as dt
import pytz
import os
import sys
from tkinter import *


import re

import base64, quopri

from os import path
from datetime import timezone

# This is a sample Python script.
user = "mecroat@mastermode.com"
password = "Mandy@4629"
imap_url = "mbox.server289.com"
dateFile = "MailFileDate.txt"
blacklistFile = "BlackList.txt"
whitelistFile = "WhiteList.txt"
returnlistFile = 'JustReturns.txt'
newestFile = "NewestSendersToConsider.txt"

max_emails_to_scan = 50
ids_with_extra_data = {}

blacklist = dict()
whitelist = dict()
newlist = dict()

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(name)# Press Ctrl+F8 to toggle the breakpoint.

def get_date_time( ) -> []:
    date_time = dt.datetime.now()
    current_time = date_time.now( pytz.timezone( 'America/Chicago' ) )
    Temp1 = str( current_time )
    Temp1 = Temp1.replace( '-', '' )
    Temp1 = Temp1.replace( ':', '' )

    FormattedDate = Temp1[0:8]
    FormattedTime = Temp1[9:15]
    return [FormattedDate, FormattedTime]

def logit( logString: str, filename: str) -> bool :

    result = True

    fh = open( filename, "a")
    d = get_date_time()
    out = d[0] + "." + d[1] + " " + logString
    out_str = [out]
    fh.writelines(out_str)
    fh.close()

    return result

def log( s: str):

    ret = logit( s + "\n", logfilename)

    if ret == False:
        sys.exit("I/O error on log file!")

def check_if_work_needed (filename: str, yesterdayDate: dt.date ) -> (bool, str) :
#
#   Find out if we have alread done this today.
#   Currently not used
#
    Date = ""
    result = True
    # if date file nt present, create it and populate with
    # yesterday's date
    if (not os.path.isfile(filename)):
        Date = today - dt.timedelta(days=1)
    else :
        fh = open(dateFile, "r")
        Date = fh.read()
        fh.close()

    return result, Date

def get_command_line_params(clin) -> (bool, str, int):
#
#   There are 2 params:
#       - scan
#           Scan the latest emails for items not on whitelist or blacklist
#       OR
#       - purge
#           Purge (permanently delete) recent emails in blacklist
#   Both have a value called limit which is a number expressing the
#   limit of emails to scan or check for deletion
#
    result = True
    ac = ""
    lim = "0"
    for i in clin:
        s = i.split("=")
        if s[0] == "action":
            ac = s[1]
        elif s[0] == "limit":
            lim = int(s[1])

    return result, ac, lim

def get_blacklist_file(file_name:str) -> (bool, list):
#
# open and read the file of emails that should be deleted
#
    result = True
    contents = []
    if os.path.isfile(file_name) :
        fh = open(file_name,"r")
        contents = fh.readlines()
        fh.close()
    else :
        # create the delete file
        fh = open(file_name, "w")
        fh.close()

    strr = contents

    contents = []

    for i in strr:
        contents.append(i.rstrip('\n'))

    return result, contents

def get_newest_sender_file(file_name:str, append:bool = FALSE) -> (bool, list):
#
# open and read the file of emails that should be deleted
#
    result = True
    contents = []
    if os.path.isfile(file_name) :
        fh = open(file_name,"r")
        contents = fh.readlines()
        fh.close()
    else :
        # create the delete file
        fh = open(file_name, "w")
        fh.close()

    strr = contents

    contents = []

    if (append == TRUE):
        for i in strr:
            contents.append(i.rstrip('\n'))

    return result, contents

def get_whitelist_file(file_name:str) ->(bool, list):
#
# open and read the file of emails that should be allowed
#
    result = True
    contents = []
    if os.path.isfile(file_name) :
        fh = open(file_name,"r")
        contents = fh.readlines()
        fh.close()
    else :
        # create the delete file
        fh = open(file_name,"w")
        fh.close()

    strr = contents

    contents = []

    for i in strr:
        contents.append(i.rstrip('\n'))

    return result, contents


def encoded_words_to_text(encoded_words):

    #print ("E =" + str(encoded_words))
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

# Press the green button in the gutter to run the script.
#encoded_words_to_text("I Guarantee =?UTF-8?B?WW914oCZbGw=?= Have the Chance To see gains")

d = get_date_time()

logfilename = d[0] + "_" + d[1] + ".log"


if __name__ == '__main__':
    log( "Start..")
else:
    sys.exit()

__argc = len(sys.argv)

result, action, max_emails_to_scan  = get_command_line_params(sys.argv)

temp = ""
for i in range(0, __argc):
    temp = temp + " " + sys.argv[i]

log( "Command line: " + temp)

action = action.lower()

#print ( date_time.strftime("%m.%d.%Y %H:%M:%S"))
today = dt.date.today()

result = True

if (action == "scan"):
    result, DateFileDate = check_if_work_needed(dateFile, today)

if result:
    pass
else:
    if (action == "scan"):
        log("Date file Not Found")
        sys.exit()

# open the delete file
result, blacklist = get_blacklist_file(blacklistFile)

if result:
    result, whitelist = get_whitelist_file(whitelistFile)
    if result:
        result, newlist = get_newest_sender_file( newestFile, FALSE )
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
    log("No mail folders, no login!")
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
    log("InBox is empty!")
    sys.exit()

scan_count = int( max_emails_to_scan )

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
            __s = subject.split( "\n" )
            subject = ""
            for __str in __s:
                __str = __str.replace("\r", "")
                if "=?utf-" in __str.lower():
                    subject += encoded_words_to_text(__str)
                else:
                    subject += __str
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
                log ("Skip " + from_address + ": in blacklist")
                continue
            if return_path in blacklist:
                log ("Skip " + return_path + ": in blacklist")
                continue
            if from_address in whitelist:
                log ("Skip " + from_address + ": in whitelist")
                continue
            if return_path in whitelist:
                log ("Skip " + return_path + ": in whitelist")
                continue
            else:
                while (True ):
                    if action == "scan":
                        result = input("\nFrom: " +  from_address + "\nSubject: " + subject + "\n[b]lacklist,[w]hitelist,[s]kip,[r]eset,[q]uit: default=s?")
                    else:
                        result = "s"
                        break
                    if  result == "" or result == "s":
                        log("message from " + from_address + " manually skipped.")
                        break
                    if result == "b":
                        if from_address not in blacklist:
                            blacklist.append(from_address)
                            log( "from address " + from_address + " blacklisted." )
                            if from_address not in newlist:
                                newlist.append( '(f) - ' + from_address)
                        if return_path not in blacklist:
                            blacklist.append(return_path)
                            if return_path not in newlist :
                                newlist.append('(r) - ' +  return_path)
                            log( "return path " + return_path + " blacklisted." )
                        break
                    elif result == 'w':
                        if from_address not in whitelist:
                            whitelist.append(from_address)
                            log( "from address " + from_address + " whitelisted." )
                        if return_path not in whitelist:
                            whitelist.append(return_path)
                            log( "from address " + return_path + " whitelisted." )
                        break
                    elif result == "r":
                        log("user requested resetting scan loop.")
                        break
                    elif result == "q":
                        log("Operator Abort")
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

    fd = open(blacklistFile, "w")
    for n in blacklist:
        fd.write(str(n) + "\n")
    fd.close()

    whitelist.sort(key = lambda x: x.lower())

    fd = open(whitelistFile, "w")

    for n in whitelist:
        fd.write(str(n) + "\n")
    fd.close()

    newlist.sort(key = lambda x: x.lower())

    fd = open(newestFile, "a")

    d = get_date_time()
    fd.write('\n*** ' + d[0] + ' ' + d[1] + ' *** \n\n')

    for n in newlist:
        s = n.replace("<", "")
        s = s.replace(">", "")
        fd.write(str(s) + "\n")
    fd.close()

elif (action == "purge"):
    ref = dataX[0].split()
    for i in range( -1, 0-max_emails_to_scan-1, -1):
        num = ref[i]
        result, dataY = mail.uid( 'fetch', num, '(RFC822)' )
        if result == "OK":
            from_address = ""
            email_message = email.message_from_bytes(dataY[0][1])
            from_party = email_message['From']
            subject = email_message['Subject']
            __s = subject.split( "\n" )
            subject = ""
            for __str in __s:
                __str = __str.replace("\r", "")
                if "=?utf-" in __str.lower():
                    subject += encoded_words_to_text(__str)
                else:
                    subject += __str
            m = re.search('<.+>', from_party)
            if m == None:
                from_address = from_party
            else:
                from_address = m.group(0)
                from_address = from_address.replace('<', '')
                from_address = from_address.replace('>', '')

            if from_address in blacklist:
                log( "Purging: " + str(from_address) + " : " + subject + " : " + str(num) )
                _ , msg = mail.uid('fetch', num, "(RFC822)")
                try:
                  mail.uid('STORE', num, '+FLAGS', '\\DELETED')
                except Exception as e:
                    log ("Mail store (delete) error for UID " + str(num) + " From: " + from_address + " Subject : " + subject + "... Skipping")
            else:
                try:
                    mail.uid('STORE', num, '-FLAGS', '\\SEEN')
                except Exception as e:
                    #print ("Error {0} ".format(e))
                    log ( "Mail store (unread) error for UID " + str(num) + " From: " + from_address + " Subject : " + subject + "... Skipping")
        else:
            log("Failed to fetch mail for UID " + str(num))

    mail.expunge()
    mail.close()
    mail.logout()

elif action == "test":
    pass

