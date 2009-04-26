from django.db import models
from apps.reporters.models import Reporter, PersistantConnection

# TODO: better name
class MessageInWaiting(models.Model):
    '''A message in waiting for a response.'''
    STATUS_TYPES = (
        ('P', 'Pending'), # the message has been received, but not handled
        ('H', 'Handled'), # the message has been handled by the user but not sent
        ('S', 'Sent'), # the message has been sent
    )
    # we need either a reporter or a connection to respond
    # TODO: this should be a dual-non-null key if that is possible
    reporter = models.ForeignKey(Reporter, null=True, blank=True)
    connection = models.ForeignKey(PersistantConnection, null=True, blank=True)
    time = models.DateTimeField()
    incoming_text = models.CharField(max_length=160)
    status = models.CharField(max_length=1, choices=STATUS_TYPES)
    
    @staticmethod
    def from_message(msg):
        to_return = MessageInWaiting(time=msg.date, incoming_text=msg.text, status='P')
        if msg.reporter:
            to_return.reporter = msg.reporter
        else:
            to_return.connection = msg.persistant_connection 
        return to_return
    
    
    def get_connection(self):
        if self.reporter:
            return self.reporter.connection
        return self.connection
    
    def __unicode__(self):
        return self.incoming_text


# TODO: better name    
class ResponseInWaiting(models.Model):
    
    '''The responses to send to the messages in waiting'''
    RESPONSE_TYPES = (
        ('O', 'Original'), # the original response - as decided by RapidSMS.  These won't go out unless they are confirmed 
        ('C', 'Confirmed'), # an original response that is to be sent out as-is
        ('A', 'Added'), # when we want to send our own messages back
    )
    
    # TODO: better name - what is the antonym of response?
    originator = models.ForeignKey(MessageInWaiting)
    text = models.CharField(max_length=160)
    type = models.CharField(max_length=1, choices=RESPONSE_TYPES)
    
    def __unicode__(self):
        return self.text

