import sys,pprint
from optparse import OptionParser

from sfMagma import SFMagmaTool
from sfContact2 import SFContact
from sfLead import SFLead

def main_flow(opts, args):
   sfTool = SFMagmaTool()

   HARDBOUNCE = False
   defaultReason = ''
   if opts.mode == 'hardbounce':
       HARDBOUNCE = True
       defaultReason = 'Marked inactive due to hard email bounce.'
       pass

   inFile = args[0]

   fh = file(inFile)

   fields = ('Id', 'FirstName', 'LastName', 'Email')

   ctRow = 0
   for row in fh.readlines():
       ctRow += 1
       #if ctRow > 2: break
       email, reason = row.split(",", 1)

       if email is None:
          continue
       elif email.lower() in ['email', 'e mail', 'e-mail']:
          continue

       if reason in [None,'']:
           reason = defaultReason
           pass

       email = email.strip()
       reason = reason.strip()
           


       print 'Processing email address: %s' %(email)
       #continue
       where = [['Email', '=', email]]

       # look up and process contacts
       contactList = SFContact.queryWhere(sfTool, where, fields)
       for contact in contactList:
           contactData = contact.getDataMap()

           contactData['HasOptedOutOfEmail'] = True

           if HARDBOUNCE is True:
               if contactData.get('FirstName','')[-2:] != '-x':
                   contactData['FirstName'] = "%s-x" \
                                              %(contactData.get('FirstName',
                                                                ''))
                   pass
               
               if contactData.get('LastName','')[-2:] != '-x':
                   contactData['LastName'] = "%s-x" \
                                             %(contactData.get('LastName'))
                   pass
               
               contactData['Email'] = 'null@null.null'
               contactData['Description'] = reason
               contactData['ContactStatus_c'] = 'Inactive'
               pass

           contact.update()
           continue
       
       # look up and process leads
       leadList = SFLead.queryWhere(sfTool, where, fields)
       for lead in leadList:
           leadData = lead.getDataMap()

           leadData['HasOptedOutOfEmail'] = True

           if HARDBOUNCE is True:
               # first try to delete the lead
               res = lead.delete()
               if res is True:
                   # lead deletion worked - move along
                   continue
               
               if leadData.get('FirstName','')[-2:] != '-x':
                   leadData['FirstName'] = "%s-x" \
                                           %(leadData.get('FirstName',''))
                   pass
               
               if leadData.get('LastName','')[-2:] != '-x':
                   leadData['LastName'] = "%s-x" %(leadData.get('LastName'))
                   
               leadData['Email'] = ''
               leadData['Description'] = reason
               pass

           lead.update()
           continue

       continue
   return


def main_cl():
    """ Handle the command line """
    usage = "%s -m [optout|hardbounce] /path/to/inputfile.csv" %sys.argv[0]
    
    op = OptionParser(usage=usage)

    op.add_option('-m', '--mode', dest='mode', default=None,
                  help='Mode of operation - "optout" for opt outs, '
                  '"hardbounce" for hard bounces')

    opts, args = op.parse_args()

    # sniff the opts
    if opts.mode is None:
        print 'You must provide a mode (use the -m arg.)'
    if opts.mode not in ['optout', 'hardbounce']:
        print 'Mode must be either "optout" or "hardbounce"'
        pass


    # sniff the args
    if len(args) == 0:
        print 'You must provide path to an input file'
        pass
    
    main_flow(opts, args)

if __name__ == "__main__":
    main_cl()
