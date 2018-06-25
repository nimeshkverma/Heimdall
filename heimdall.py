import os
import re
import smtplib
import subprocess
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders
from settings import SERVER_EMAIL, SERVER_PASSWORD, NOTIFICATION_DETAILS, WATCHED


class Heimdall(object):

    def __init__(self):
        self.smtp_server = self._smtp_server()
        self.watched = self._watched()

    def _watched(self):
        watched = {watched_key: '' for watched_key in WATCHED.keys()}
        for watched_key, watched_list in WATCHED.iteritems():
            for watched_command in watched_list:
                watched[watched_key] += self._terminal_string(watched_command)
        return watched

    def _smtp_server(self):
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SERVER_EMAIL, SERVER_PASSWORD)
        return server

    def _notify(self, subject, body, to=[]):
        try:
            for to_email in to:
                msg = MIMEMultipart()
                msg['From'] = SERVER_EMAIL
                msg['To'] = to_email
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'plain'))
                text = msg.as_string()
                self.smtp_server.sendmail(SERVER_EMAIL, to_email, text)
        except Exception as e:
            self.smtp_server.sendmail(
                SERVER_EMAIL, SERVER_EMAIL, 'Error in Heimdall due to {e}'.format(e=str(e)))

    def _terminal_string(self, command):
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        return proc.stdout.read()

    def _should_notify(self, terminal_string_type, identifier, watched_string):
        should_notify = False
        if terminal_string_type == 'process' and not re.findall(identifier, watched_string):
            should_notify = True
        stop_regex = identifier + '\s*' + 'stop/waiting'
        if terminal_string_type == 'service' and re.findall(stop_regex, watched_string):
            should_notify = True
        print should_notify
        return should_notify

    def _clean(self):
        self.smtp_server.quit()

    def watch_and_notify(self):
        for terminal_string_type, notification_triggers in NOTIFICATION_DETAILS.iteritems():
            for notification_trigger in notification_triggers:
                for identifier in notification_trigger.get('identifiers', []):
                    if self._should_notify(terminal_string_type, identifier, self.watched.get(terminal_string_type, '')):
                        self._notify(notification_trigger.get('subject', 'Notification from Heimdall'),
                                     notification_trigger.get(
                                         'body', 'Notification from Heimdall'),
                                     notification_trigger.get('to_emails', 'Notification from Heimdall'))
        self._clean()

if __name__ == '__main__':
    watchman = Heimdall()
    watchman.watch_and_notify()
