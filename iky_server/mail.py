import imaplib
import smtplib
import sys
from email.parser import Parser

import requests
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

__author__ = "Alfred Francis"
__copyright__ = "Copyright 2007, The IKY Project"
__credits__ = ["Noora Farooqi", "Joseph Cleatus"]
__version__ = "1.0.0"
__maintainer__ = "Alfred Francis"
__email__ = "alfred.francis@pearldatadirect.com"
__status__ = "Development"

class emailManager:
    def __init__(self, serverName, userName, passWord):
        self.serverName = serverName  # "imap.gmail.com"
        self.userName = userName
        self.passWord = passWord
        self.imapConnection = imaplib.IMAP4_SSL(serverName, 993)
        self.smtpConnection = smtplib.SMTP('smtp.gmail.com', 587)

    def openIMAP(self):
        try:
            (self.responseCode, capabilities) = self.imapConnection.login(self.userName, self.passWord)
        except:
            print sys.exc_info()[1]
            sys.exit(1)
        return self.responseCode

    def openSMTP(self):
        self.smtpConnection.starttls()
        self.smtpConnection.login(self.userName, self.passWord)

    def sendEmail(self, toAddress, subject, body):
        msg = MIMEMultipart()
        msg['From'] = self.userName
        msg['To'] = toAddress
        msg['Subject'] = subject

        body = body
        msg.attach(MIMEText(body, 'plain'))

        text = msg.as_string()
        self.smtpConnection.sendmail(self.userName, toAddress, text)

    def closeSMTP(self):
        return self.smtpConnection.quit()

    def closeIMAP(self):
        return self.imapConnection.close()

    def getUnReadMessages(self, emailSubject=""):
        parser = Parser()
        self.imapConnection.select(readonly=0)
        # responseCode, emails = self.imapConnection.search(None,'(UNSEEN SUBJECT "%s")' % emailSubject)
        responseCode, emails = self.imapConnection.search(None, '(UnSeen)')
        if responseCode == 'OK':
            for mailNumber in emails[0].split():
                responseCode, resultData = self.imapConnection.fetch(mailNumber, '(RFC822)')
                parsedEmail = parser.parsestr(resultData[0][1])
                singleMail = dict(parsedEmail)
                singleMail["body"] = ""
                if parsedEmail.is_multipart():
                    for part in parsedEmail.get_payload():
                        if part.get_content_type() == "text/plain":
                            singleMail["body"] += str(part.get_payload(decode=True))
                else:
                    singleMail["body"] = parsedEmail.get_payload()
                responseCode, resultData = self.imapConnection.uid('store', '542648', '+FLAGS', '(\\Seen)')
                yield singleMail


# Testing
if __name__ == '__main__':
    testEmail = emailManager("imap.gmail.com", "ikytesting@gmail.com", "ikytesting999")
    testEmail.openIMAP()
    testEmail.openSMTP()
    while True:
        try:
            for singleMail in testEmail.getUnReadMessages():
                print("New Email from :" + singleMail["From"])
                # print(singleMail["To"])
                print(singleMail["body"])

                r = requests.get("http://172.30.10.141/iky_parse?user_say=" + singleMail["body"])
                body = "Hi,\n" + r.content + "\nCheers,\n\tiKY"
                print(body)
                testEmail.sendEmail(singleMail["From"], "Reply to your query", body)
        except KeyboardInterrupt:
            testEmail.closeIMAP()
            testEmail.closeSMTP()
            print "Bye"
        sys.exit()
